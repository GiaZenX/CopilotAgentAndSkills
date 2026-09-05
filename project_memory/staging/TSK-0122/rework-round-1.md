# TSK-0122 — Nacharbeit zu Prüfrunde 1

Ergänzt `stream-protocol.md`; die Nahttabelle, §7 und §9 dort sind mitgeschrieben. Alle Zahlen hier
sind gemessen, jede Mutation in einer `.git`-losen Kopie unter
`_round-scratch/TSK-0122/rig/copy-redfirst2*`, jede vor der nächsten zurückgesetzt.

## Rot-zuerst je Befund

| Befund | Test | sauber | mit dem wiederhergestellten Defekt |
|---|---|---|---|
| F1 | `tools/test_approvals_dispatch.py::test_an_order_deriving_from_a_proposed_requirement_is_still_asked` | rc 0 | **rc 1** |
| F2 | `tools/test_migrate_holes.py::test_a_new_hole_can_be_filed_from_the_command_surface` | rc 0 | **rc 1** |
| F3 | `tools/test_migrate_holes.py::test_a_hole_captured_after_the_migration_reaches_the_generated_index` | rc 0 | **rc 1** |
| F4 | `tools/test_migrate_holes.py::test_a_number_collision_at_the_merge_is_refused_not_skipped` | rc 0 | **rc 1** |
| F6 | `.claude/hooks/test_gates.py::test_every_reference_to_a_measurement_leads_to_one` | **rc 1** über leerem Bestand | rc 0 ohne das `assert` |
| F18 | `tools/test_approvals_dispatch.py::test_the_remedy_for_an_already_triaged_wish_names_what_it_became` | rc 0 | **rc 1** |
| F19 | `tools/test_parallel_streams.py::test_a_worktree_nobody_can_stand_in_is_refused` | rc 0 | **rc 1** |

F6 ist die umgekehrte Form, und das ist der Punkt: über einem Bestand ohne Löcher ist der Knoten
mit dem `assert` **rot** und ohne es **grün** — genau die Klasse „ein benannter Test, der nicht
scheitern kann". Der Nachweis zeigt, dass er es jetzt kann.

**Ein untauglicher Mutationsversuch, protokolliert statt verschwiegen:** der erste F2-Lauf benannte
das Flag in `--hole-disabled-for-the-measurement` um und maß rc 0 — weil `argparse` ein
eindeutiges PRÄFIX akzeptiert, funktionierte `--hole` weiter. Die Mutation war unbrauchbar, nicht
der Test; der zweite Lauf entfernt, was das Flag TUT (`hole=args.hole`), und misst rc 1.

## Blockierende Befunde

**F1 — die SR-Pflicht hing an der Schreibweise von `derives_from`.**
Die Ausnahme ist jetzt an ihre Bedeutung gebunden: `dispatch._carries_its_own_criteria` liest den
FELDVERTRAG (`dispatch.CRITERIA_FIELDS` gegen `backlog_types._contract_fields`) — ein Ursprung
befreit, wenn er die Kriterien BRINGT, gegen die der Auftrag gemessen wird. Gemessen ergibt das
`{PR, RQ, BUG, CR, EXP}`; `SR` ist nicht darunter, trägt also keine Befreiung mehr und erfüllt die
Pflicht genau dann, wenn er der ACCEPTED Architektenschritt IST — was die vorhandene Suche schon
beantwortet, ohne einen zweiten Zweig für den Typ, um den die Regel geht. Der Docstring, der die
Aufzählung trug („names a BUG, a CR or an EXP"), nennt jetzt die Eigenschaft. Beide Enden hält
`test_only_an_origin_that_carries_criteria_excuses_the_architect_step`.
**Reichweite nachher, gemessen über 75a00d1:** `derives_from` nennt PR 3 + SR 29 = **32 von 120**
Aufträgen, für die die Pflicht jetzt gilt, statt 3.
**Kein Loch nötig:** der Rest, den der Prüfer benennen wollte, ist geschlossen — was übrig bleibt
(BUG/CR/EXP befreien), ist DEC-0072 (c) wörtlich und gewollt.

**F2 — es gab keinen Weg, ein neues Loch zu erfassen.**
`capture --hole` ist auf der Kommandofläche (`cli.py`), mit Vertrag in `--help`: das Flag sagt,
DASS der Datensatz ein Loch ist, der Kernel sagt WELCHE Nummer. Ein Körper, der `hole_number`
mitbringt, wird weiterhin verweigert. Ein `--hole` auf einer TSK wird abgelehnt (ein Arbeitsauftrag
ist kein Loch). Auf stderr steht, was der Index braucht, um nachzuziehen. **Als Prozess gemessen**,
nicht als Funktionsaufruf: `python -m kernel.cli --root project_memory capture BUG --hole` → rc 0,
`H4` auf stdout, Item im Speicher, `--reindex`-Hinweis auf stderr.

**F3 — die Abhilfe des Prüfers tat nichts.**
Der Neu-Schrieb des generierten Abschnitts läuft jetzt **bedingungslos** aus dem Speicher, nicht
mehr hinter der Eintragsschleife; dazu `--reindex`, das nur den Index schreibt und dafür kein
`--related-pr` braucht. Der Assertionstext des Gate-Prüfers nennt jetzt dieses Kommando — und sagt
dazu, dass es aus einer Shell **außerhalb** von Claude Code laufen muss (F13).

**F4 — eine Nummernkollision löschte einen Eintrag mit rc 0.**
`_assert_it_is_the_same_hole` vergleicht Titel und `observed` des gespeicherten Lochs gegen den
gelesenen Eintrag und verweigert bei Abweichung mit `SystemExit`; die Meldung nennt beide Fassungen
und den Weg heraus. Verglichen werden genau die zwei Identitätsfelder — nicht `limits` und nicht
die Testzitate, weil die sich bei einer Neubeurteilung legitim ändern und ein wiederaufgenommener
Lauf darüber nicht stolpern darf. Der Wiederaufnahmefall bleibt ein wortloser No-op.

## Mittlere Befunde

- **F5** Die Zahl ist aus dem Kommentar entfernt statt korrigiert: sie war über die eigene Funktion
  falsch (die liest beide Elternfelder und liefert 35, nicht 21), und zwei Zeilen darüber stand,
  dass eine solche Zahl in den Rundenbericht gehört. **Gemessen an 75a00d1:** 120 TSK-Dateien,
  `product_requirement = FR` 21, `derives_from = FR` 35, `tasks_under_an_inbox_item()` = **35**.
- **F6** siehe Rot-zuerst; zusätzlich ist die überschattende Variable (`holes` aus `_anchors`)
  umbenannt, damit die zweite Hälfte wieder das misst, was sie nennt.
- **F7** Alle drei Zeiger auf `report._check_triage_result_link` heißen jetzt
  `report._check_fr_result_link` (`backlog_types.py`, `dispatch.py`, `report.py`).
- **F8** `state.py` zitiert jetzt
  `tools/test_migrate_holes.py::test_a_second_run_over_the_same_document_writes_nothing` und sagt
  dazu, was `hole_by_number` NICHT entscheidet (Wiederaufnahme vs. Kollision — das ist F4s Stelle).
- **F9** Der Absatz an `RUN_SCOPES` sagt jetzt „öffnet keinen MERGE" statt „öffnet nichts" und
  nennt DEC-0071 mit der Begründung.
- **F10** Der Kommentar an `HOLE_REQUIRED_FIELDS` sagt jetzt, WO der engere Vertrag gilt
  (`validate_state` über gespeicherte Items und die Migrationstür) und dass `capture --hole` den
  vollen `BUG`-Vertrag verlangt — mit dem Grund: ein heute gemessener Defekt kann sagen, was
  stattdessen gelten soll und wie er reproduziert wurde; ein Eintrag von vor einem Jahr nicht.
  Beide Hälften misst
  `tools/test_backlog_types.py::test_the_hole_contract_is_the_reading_side_and_capture_still_asks_the_full_one`.
- **F11** Die Nahttabelle trägt jetzt den **gemessenen** AST-Vergleich (18 entfernt / 10 neu /
  5 geändert) und benennt jede geänderte Definition einzeln, darunter
  `test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`.
- **F12** Abschnitt 8 des Protokolls übergibt die Sätze jetzt **mit** den neuen Testnamen und nennt
  die fünf Dateien, in denen das tote Zitat steht.
- **F13** Abschnitt 7 sagt, dass das Merge-Kommando aus einer Shell außerhalb von Claude Code läuft;
  dasselbe steht im Assertionstext des Gate-Prüfers.

## Kleine Befunde

- **F14** Die Zahlen, die dieser Merge selbst ungültig macht, sind entfernt statt aktualisiert:
  „91 BUG records" (`backlog_types.py`), „die 140 Einträge" (`state.py`), „140 Einträge / 140-121-85"
  (`backlog_types.py`), „140 Eintraege" in H154. **Gemessen liefert das ausgelieferte Dokument
  143 Einträge und die Migration 143 Items.**
- **F15** Der Kommentar an `_delivery_evidence` sagt jetzt, wie weit die Bestätigungsfrage wirklich
  reicht: `evidence_covers` ist unverändert, also bestätigt auch ein Datensatz, der etwas nennt,
  das UNTER dem Item hängt.
- **F16** erledigt mit F1 und F7 (Eigenschaft statt Aufzählung an beiden Stellen).
- **F17** `report.py` nennt DEC-0071, `state.py` nennt DEC-0071, `dispatch.py` nennt DEC-0072.
- **F18** `_triage_remedy` liest den Zustand des Wunsches: ein bereits triagierter nennt das Item,
  das er wurde; nur ein untriagierter bekommt die Triage-Route.
- **F19** `--worktree` verweigert einen Pfad, an dem kein Verzeichnis liegt. Was nicht geprüft wird
  (git-Checkout? gehört zu diesem Zustand?) steht als zweite Restklasse in **H156**; dass zwei
  Leases denselben Baum nennen dürfen, ist dort ausdrücklich als **kein** Rest benannt.
- **F20** Als zweite Restklasse in **H154** aufgeschrieben, mit der gemessenen Kette (H156 mit
  zerstörtem YAML → Prüfer rc 0) und der Begrenzung (git-Diff, und der Index wird aus dem Speicher
  regeneriert, also fällt die fehlende Zeile beim nächsten `--reindex` auf).
- **F21** Die Zeilenzahl im Protokoll ist jetzt die gemessene (**3927**).
- **F22** Der umbrochene Testname in `migrate.py` steht wieder in einem Stück.

## Läufe nach der Nacharbeit

| Lauf | Ergebnis |
|---|---|
| Migration Ende zu Ende gegen eine frische Kopie ohne `.git` | **143 written, 143 prose files**, Dokument nach der Migration **2441** Zeilen; zweiter Lauf **1,79 s, 0 written**, Dokument byte-identisch; `validate` **0 Fehler / 66 Warnungen** (= vorher). Die Ausgangszahl stand hier als „9199“ und war der Stand 75a00d1, nicht das ausgelieferte Dokument — Prüfbefund R4 der Runde 2 |
| Gate-Knoten `-k "hole or holes or _hole or reference_to_a_measurement"` gegen die migrierte Kopie | **7 passed** (347 s) |
| `tools/test_state.py test_backlog_types.py test_migrate_holes.py test_parallel_scopes.py test_parallel_streams.py test_report.py test_kernel.py` | **414 passed** (147 s) |
| `tools/test_approvals_dispatch.py` | **193 passed** (153 s) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |

Stempel: **2026.09.05-3**. Patch: **3927 Zeilen, 18 Dateien**, ohne VERSION-Hunks.

## Nicht geschlossen

- Der EINE schreibende Migrationslauf gegen den kanonischen Zustand — verboten in diesem Auftrag,
  siehe Protokoll §7 (jetzt mit dem Hinweis auf die Shell außerhalb von Claude Code).
- Die volle Suite, `tools/test_hooks.py` und der Rest von `test_gates.py` — DEC-0050, Merge.
- `gate_dispatch.py` von office-team und research-team als Prozess (nur dev-team gemessen, vom
  Prüfer).
- Die vom Prüfer benannten, ungemessenen Nachwirkungen der Migration (Board, `session_brief`,
  Kit-Hash mit `docs/holes/`, Laufzeit von `_iter_every_stored_item` in einem großen Speicher,
  `related_pr: PR-0003` für 143 Löcher) — sie gehören dem Merge, weil sie erst nach dem einen Lauf
  messbar sind.
