# TSK-0115 — Strom A „Board & Plan", Phase 2 (Bau)

Rolle: `harness-implementer` (Opus). Worktree `C:/Offline Repos/v2-testbed/_worktrees/g3-board`
(Branch `g3/board`, Stand `e45c0ca`). Scratch nur unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/`. Kein Commit, kein Push, keine Installation
in den globalen Speicher.

FRs: **FR-0075** (primär), **FR-0079**, **FR-0080**. Bindend: `DEC-0064`, `DEC-0065`, `DEC-0066` (5),
`DEC-0062`, `DEC-0063`; Baustand `04-build-spec.md` §0/§5, `03-tokens-final.md`, `08-final.md`.

---

## 0. Vorgefunden (gemessen vor der ersten Zeile Code)

| Gegenstand | Stand am Rundenbeginn | Wie gemessen |
|---|---|---|
| `tools/test_board.py` | 49 Tests grün, 28,28 s | `python -B -m pytest tools/test_board.py -q` im Worktree |
| `team-kits/kernel/board.py` | 776 Zeilen; 14 Typsektionen alphabetisch; keine Fokuszahlen, kein Records-Block, keine Zeitleiste, kein Einklappen | `wc -l`, Lesen |
| `team-kits/kernel/backlog_tree.py` | 321 Zeilen; `_LABELS` deckt 10 von 17 Typen | `set(ACTIVE_DIRS) - set(_LABELS)` = 7 |
| `generate_dashboard.py` | 423 Zeilen, rendert Items **und** Vitalwerte | Lesen |
| `progress.dashboard.template.html` | 351 Zeilen | `wc -l` |
| `team-kits/kernel/plan_diagram.py` | existiert nicht | `ls` |
| Auslöser des Boards | `state._regenerate_index_locked` → `_write_board`, **eine** Uhr für Index und Board | `state.py` 1260–1345 |
| Uhr im Renderer | keine; `render(state, entries, generated_at)` ist rein | Lesen |
| Offene Anfragen | nur `report.generate_session_brief` liest `approvals/pending/`; `board` gar nicht | `report.py` 235–255 |
| Spiegelpflicht | `generate_dashboard.py` + Hülle liegen **nur** im dev-team-Kit | `ls team-kits/*/templates/repo/scripts/` |

## 1. Plan und der verworfene Weg

Gebaut wurde: ein Renderer (`kernel/board.py`) für alle Items, Stil E; Dashboard auf Vitalwerte +
Verweis; `kernel/plan_diagram.py` neu; Record-Labels und Ablehnungs-Wörter in `backlog_tree.py`.

**Verworfener Weg, eine Zeile (FR-0084-Form):** die Seite aus einem eingebetteten JSON-Block im
`<script>` aufbauen (die Form des alten Dashboards) statt als fertiges Markup — verworfen, weil dann
Item-Inhalt durch JavaScript ginge und `test_board.test_the_page_script_carries_no_item_content_at_all`,
die ganze Escaping-Begründung der Seite, nicht mehr haltbar wäre.

## 2. Nahttabelle — gemeldet, hier **nicht** geschrieben

| Empfänger | Zeile(n), wörtlich | Schiedsrichter-Test |
|---|---|---|
| C (`backlog_types.py`) | siehe §7.1: Automat, Verzeichnis, Pflichtfelder und die Datumsprüfung; `PARENT_FIELDS` folgt daraus und braucht keine eigene Zeile | `test_board.test_the_milestone_type_is_wired_completely_or_not_at_all` |
| A/Merge (`backlog_tree.py`) | §7.2: `_LABELS["MST"]` und `MST` in den `children` der Produktsicht — **bewusst nicht in dieser Runde**, Grund unten | `test_board.test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view` |
| C (`state.py`) | §7.3: die Diagrammschreibung in `_write_board` | `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` |
| C (`cli.py`) | §7.4: `generate-index` druckt auch die zwei Diagrammpfade | `test_board.test_the_documented_command_writes_and_names_both_artefacts` |
| C (`approvals.py`) | §7.5: ein **optionales** `now=None` an der **vorhandenen** `open_requests(state)` | **zwei** Schiedsrichter: `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` **und** `tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent` |
| C/Merge (Hooks) | `guard_no_adhoc.ITEM_TYPES` + `"mst"` in drei Kits | `test_hooks.test_no_adhoc_covers_every_item_type` |
| D (Verfassungen) | eine `MST`-Zeile je Typtabelle der drei Verfassungen | Textprüfung von Strom D |
| B (geteilt) | `tools/test_hooks.py`, Dashboard-Abschnitt (hier geändert, §5) | Merge-Runde |
| Merge | `templates/project_memory/milestones/active/.gitkeep` in drei Kits | `test_board.test_each_kit_renders_the_types_its_own_template_ships` |

**Naht, die entfällt:** `04-build-spec.md` §2.1 sah eine `now`-Zeile von `state` an `board.render`
als C-Naht vor. Nicht nötig: `board._clock` leitet Epoche **und** Kalendertag aus dem bereits
übergebenen `generated_at` ab — dieselbe Uhr, die den Index stempelt. Die Seite bleibt damit ohne
jede Naht eine reine Funktion ihrer Eingaben; der Test dazu heißt
`test_board.test_the_board_is_a_pure_function_of_the_state_and_the_stamp_it_is_handed`.

## 3. Je FR: Abnahmezeile, Messung, roter Test

### FR-0075 — Board neu, ein Renderer mit zwei Ausgaben

**Abnahme:** `kernel/board.py` rendert die Tafel in Stil E mit den drei Zahlen, Karten als Zeile mit
Kante über die volle Fensterbreite, einklappbarer Hierarchie mit Tastaturpfad, zugeklappten Records
und Reiter Timeline; `generate_dashboard.py` rendert **keine** Items mehr; Auslöser, Kit-Besitz und
Ein-Datei-Eigenschaft aus FR-0030 bleiben; die Seite ist eine reine Funktion des Zustands.

| Behauptung | Messung (vorher → nachher) |
|---|---|
| Kein Kartenpaar überlappt, kein Textüberlauf, rechter Rand 0 px | `measure_layout.py` über die vier gebauten Endzustände × 3 Breiten × jeder Reiter (39 Zeilen): **0 / 0 / 0 px** bei 1280, 1920, 390. Vorher (Phase 1, `layout-before.md`): 110 bzw. 333 Paare, 115/752 px leer |
| Die Seite lädt nichts nach | Sichtlauf mit `page.on("request")`: **0** Anfragen außerhalb von `file:` über 105 Bilder |
| Vier Zustände, jeder Reiter, hell/dunkel, drei Breiten | `review/build/render.json`: 4 Seiten, **105 Bilder**, `errors: []` bei allen vier |
| Das Dashboard nennt kein Item mehr | `generate_dashboard.py` am echten Zustand (289 Items): Ausgabe **4 946 Byte**, kein Item-Id im HTML; vorher rendert es 50 Items je Sicht |
| Dashboard-Größe | 423 → **244** Zeilen Generator, 351 → **91** Zeilen Hülle |
| „wartet auf dich" stimmt mit dem Sitzungsbrief überein | Store mit 3 offenen (eine davon zu einem unter der Anfrage archivierten Item) + 1 abgelaufenen Anfrage: Tafel **3**, Brief **3**, gleiche Gegenstandsmenge |

**Rot ohne den Fix** (je Test eine eigene Mutation, in `_round-scratch/TSK-0115/red/` gemessen):

| Test | Wiederhergestellter Defekt |
|---|---|
| `test_board.test_the_first_strip_counts_blocked_waiting_and_in_flight_from_the_state` | `%(first)s` aus der Seitenvorlage entfernt (der ausgelieferte Stand) |
| `test_board.test_an_expired_approval_request_is_not_waiting_on_anyone` | Ablaufregel in `open_requests` entfernt |
| `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` | `open_requests` liest das Verzeichnis nicht |
| `test_board.test_a_blocked_card_carries_its_blocker_on_its_face` | (a) Blockier-Flagge auf der Karte entfernt, (b) Freigabe-Flagge entfernt |
| `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` (zweite Mutation) | Anfrage ohne Karte wird übersprungen |
| `test_board.test_living_types_precede_records_and_no_type_is_lost` | Record-Typen fallen ganz weg |
| `test_board.test_an_empty_end_state_is_named_not_drawn` | jeder leere Endzustand wieder gezeichnet |
| `test_board.test_a_task_without_a_title_shows_its_work_on_the_face` | `face_title` fällt auf `_face_title` zurück |
| `test_board.test_every_deep_group_starts_hidden_and_every_root_open` | `FOLD_DEPTH = 99` |
| `test_board.test_a_fold_control_states_what_it_hides` | `aria-expanded` fest `true` |
| `test_board.test_the_noscript_page_shows_every_group_and_no_fold_control` | `.fold`, `.tree-tools`, `.figures`, `.focus-list` aus der noscript-Regel |
| `test_board.test_the_board_is_a_pure_function_of_the_state_and_the_stamp_it_is_handed` | `_clock(generated_at)` → `time.time()`/`date.today()` |
| `test_board.test_a_stamp_the_board_cannot_read_costs_the_today_marker_and_not_the_page` | `_clock` reicht den Fehler durch |
| `test_board.test_an_item_not_under_a_goal_says_what_it_is_in_kit_language` | `NO_LINK`-Wort wieder „unassigned" (DEC-0066 (5)) |
| `test_board.test_every_type_the_kernel_has_carries_a_plain_language_name` | `EVD` aus `_LABELS` |
| `test_board_browser.test_no_two_cards_of_the_board_overlap_at_any_width` | `box-sizing`-Regel nach `all: unset` entfernt |
| `test_board_browser.test_the_board_uses_the_width_it_is_given` | Slot wieder `flex: 0 0 15rem` |
| `test_board_browser.test_a_fold_control_works_by_keyboard_and_shows_its_focus` | Falt-Knopf wird ein `<span>` |
| `test_hooks.test_the_dashboard_carries_no_item_of_its_own_and_points_at_the_board` | Indexzeilen wieder in den Datenblock des Dashboards |

### FR-0079 — Meilensteine (MST) auf der Zeitleiste

**Abnahme:** Die Tafel rendert `MST`-Einträge als Sektion **und** als Reiter Timeline mit
Drei-Bänder-Lineal, Heute-Marke, Verspätung und Bahnzählung in Worten; die Kernel-Typzeilen sind
eine Naht an Strom C (§7.1), und die Testvorrichtung ist der **Schiedsrichter** dieser Naht: sie
vergleicht die Zeilen mit `DEC-0064`, wenn C sie gelegt hat, und legt sie sonst für den Test selbst.

| Behauptung | Messung |
|---|---|
| Meilenstein steht mit seinen Zielen und Bahnzahlen | Fixture mit vier `MST`, gesichtet (`review/build/timeline-timeline-1280.png`, `-1920`, `-390`, dunkel) |
| Keine zwei Beschriftungen teilen ein Band | `test_board_browser.test_ruler_labels_share_no_band` bei 1280/1920/390: 3 Beschriftungen, **0** Überlappungen; `measure_layout` über `timeline.html`: 0 in allen Reitern |
| Kein Prozentwert auf der Zeitleiste | im Test geprüft: `%` steht in keiner Zielzeile |

**Rot ohne den Fix:** `test_a_milestone_stands_on_the_timeline_with_the_goals_it_names` (Reiter fällt
weg) · `test_a_milestone_past_its_date_and_not_reached_is_late` (Erreicht-Prüfung entfällt) ·
`test_two_milestones_a_day_apart_keep_both_labels` und `test_board_browser.test_ruler_labels_share
_no_band` (Bandwechsel entfällt) · `test_a_milestone_with_an_unreadable_date_is_shown_with_no_date`
(Datumsfehler durchgereicht) · `test_the_milestone_type_is_wired_completely_or_not_at_all` (Naht nur
an einer von fünf Stellen angewandt).

### FR-0080 — Plan und Mindmap als `.drawio.svg`

**Abnahme:** `kernel/plan_diagram.py` erzeugt `plan.drawio.svg` und `mindmap.drawio.svg` aus
denselben Entries wie die Tafel, als reine Funktion; `content`-mxfile im selben Durchgang;
`data-source-digest` trennt `pristine` / `hand-edited` / `stale`; `staging._assert_xml_wellformed`
besteht; die Auslöserzeile ist eine Naht an C (§7.3) und wird **nirgends behauptet**, bis sie liegt.

| Behauptung | Messung |
|---|---|
| Beide Dateien am echten Zustand | 289 Items → Plan **65 488 B**, Mindmap **95 885 B**, beide `pristine`, `_assert_xml_wellformed` grün |
| Keine Beschriftung ragt aus ihrem Kasten | Chromium, Kasten-für-Kasten: Plan **97** Beschriftungen, Mindmap **95**, **0** Überläufe. Vorher (globale Kappung bei 58 Zeichen): 4 bzw. 5 Beschriftungen über 288 px, sichtbar über den Nachbarn |
| `CHAR_WIDTH = 0.62` ist gemessen | breiteste Beschriftung 343,1 px bei 58 Zeichen und Schriftgröße 10 → 0,59 em; 0,62 mit Reserve |
| `CELL_BUDGET = 240` ist gemessen | 5 000 synthetische Items: **mit** Deckel 0,084 s und 161 904 + 245 868 B, **ohne** 0,210 s und 3 310 075 + 5 112 502 B. Dieses Repo hängt **90** Items unter Wurzeln, der Deckel greift also hier nicht (Reserve 2,7×) |

**Rot ohne den Fix:** `test_the_diagram_is_a_pure_function_of_the_entries` (Uhr im Generator) ·
`test_a_hand_edit_is_told_from_a_stale_file` (Digest weg) ·
`test_the_file_is_well_formed_and_carries_a_drawio_model` (`content` weg — die Pilotform) ·
`test_every_cell_names_an_item_the_entries_hold` (eine Baumebene fällt weg) ·
`test_status_is_never_carried_by_colour_alone` (Bahnwort weg) ·
`test_no_colour_outside_the_named_palette` (ein Hex an einer Aufrufstelle) ·
`test_a_project_over_the_budget_says_what_it_left_out` (Deckel schneidet stumm).

## 4. Rot-zuerst: die Messung selbst

`_round-scratch/TSK-0115/red_first.py` kopiert den Worktree **ohne** die `.git`-Datei nach
`_round-scratch/TSK-0115/red/`, fährt je Eintrag den benannten Test grün, setzt den Defekt, fährt
ihn erneut und setzt die Datei zurück. Ergebnis: **33 Mutationen, 33 rot.**

Zwei Behauptungen, die beim Selbst-Durchgang **nicht** gedeckt waren, sind dabei aufgefallen und
wurden gedeckt statt abgeschwächt:

1. `board._card` behauptete **beide** Signale auf der Kartenfläche (blockiert **und** „wartet auf
   dich"), gemessen war nur das erste. `test_a_blocked_card_carries_its_blocker_on_its_face` misst
   jetzt beide; Mutation „Freigabe-Flagge weg" → rot.
2. `board._first_strip` behauptete, eine offene Anfrage zu einem Item, das **nicht** auf der Tafel
   steht (unter der Anfrage archiviert), werde mitgezählt und stimme mit dem Brief überein. Der
   Paritätstest hatte nur Anfragen mit Karte. Mit dem verschärften Test kam ein echter Befund:
   die Zeile ohne Karte nannte ihren Gegenstand nirgends maschinenlesbar, also konnte niemand die
   zwei Leser vergleichen. **Gebaut:** die Zeile trägt `data-request` und nennt denselben
   Gegenstand wie der Brief — das Item, sonst die Art der Freigabe. Mutation „Anfrage ohne Karte
   überspringen" → rot.

Der erste Lauf meldete außerdem **einen** Test, der die Mutation überlebt: `test_plan_diagram.test_every_cell
_names_an_item_the_entries_hold` baute seine Erwartung mit `plan_diagram._outline` — also mit genau
der Funktion, die entscheidet, welche Items eine Zelle bekommen. Ein Walker, der jede Ebene ab Tiefe 2
verliert, verkleinerte die Erwartung mit. Der Test leitet seine Erwartung jetzt aus dem Vertrag von
`backlog_tree.arrange` ab (jedes Item eines Typs, den die Sicht zeigt, das nicht in `unassigned`
liegt) und wird mit derselben Mutation rot.

## 5. Was an `tools/test_hooks.py` geändert wurde (geteilte Datei, Naht an Strom B)

| Test | Was daraus wurde |
|---|---|
| `test_dashboard_renders_typed_items` | ersetzt durch `test_the_dashboard_carries_no_item_of_its_own_and_points_at_the_board` |
| `test_dashboard_on_a_greenfield_project_renders_and_says_nothing_is_captured` | prüft `active_items == 0` statt `views` |
| `test_dashboard_survives_a_hand_written_item` | prüft jetzt: die Zählung bleibt ehrlich und der Titel erreicht die Seite **nicht** |
| `test_dashboard_delivery_board_hides_finished_work` | **entfernt** — der Filter (`VIEWS`, `hide_done`) existiert nicht mehr |
| `test_dashboard_page_size_is_the_hard_ceiling` | **entfernt** — `PAGE_SIZE` existiert nicht mehr |
| `test_dashboard_views_cover_every_item_type` | **entfernt** — die Eigenschaft „kein Typ verschwindet" trägt jetzt `test_board.test_each_kit_renders_the_types_its_own_template_ships` (Sektion **oder** Silent-Zeile) |
| `test_dashboard_refuses_without_an_index`, `test_dashboard_vitals_and_the_file_budget_see_the_same_files`, `test_the_documented_dashboard_command_survives_the_write_scope_gate` | unverändert grün |

## 6. Suiten-Läufe (DEC-0050: betroffene Suiten, nicht die volle)

| Lauf | Ergebnis |
|---|---|
| `tools/test_board.py` | 69 grün (vorher 49), 24,7 s |
| `tools/test_board_browser.py` | 4 grün (Playwright vorhanden; ohne Playwright **skip**, nicht grün) |
| `tools/test_plan_diagram.py` | 9 grün |
| `test_board + test_board_browser + test_plan_diagram + test_kernel + test_report + test_kitupdate` | 409 grün, 1 skip, **1 rot** → `test_kernel.test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted`: der gezählte Rest `L24` stand auf 8 Stellen, das neue Dashboard setzt `archive` nicht mehr zusammen → Pin auf 7 und die Stellenliste in `L24` nachgezogen; danach grün |
| `test_hooks + test_repo_hygiene + test_migrate + test_disposition + test_shortening_net + test_hooks_v2 + test_role_contracts + test_shared_skill_contract + test_finance_dashboard` | 3 321 grün, 13 skip, **3 rot** (47 min) — zwei repariert, einer benannt, siehe unten |
| Wiederholung nach den Reparaturen: `test_repo_hygiene + test_disposition + test_migrate + test_shortening_net` | 209 grün, **1 rot** (nur der benannte DEC-Zeiger); `tools/test_migrate.py` danach allein 141 grün |
| `tools/test_board + test_board_browser + test_plan_diagram` (Abschlusslauf) | **83 grün** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed (nach `git add` der drei neuen Dateien — vorher: „hashed into a kit VERSION but not git-tracked") |
| `python tools/bump_kit_version.py` | dev/office/research → **2026.09.03-6** (vorläufig, Stand nach Nacharbeit 3) |

### 6.1 Die drei roten Tests des Sammellaufs

1. **`test_kernel.test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted`** —
   der gezählte Rest `L24` stand auf 8 Stellen; das neue Dashboard setzt `archive` nicht mehr
   zusammen. **Repariert:** Pin auf 7, Stellenliste in `L24` nachgezogen. Grün.
2. **`test_migrate.test_an_imported_items_legacy_id_is_not_read_as_a_relation`** — der Test lud
   `generate_dashboard.relations`, das es nicht mehr gibt. Die gemessene EIGENSCHAFT („der frühere
   Name eines importierten Items ist kein Zeiger") ist nicht weggefallen, sie hat nur den Besitzer
   gewechselt: sie gehört jetzt `backlog_tree.parents_of`, dem einen Leser, mit dem Tafel,
   Merge-Gate und Plan-Diagramm Items platzieren. **Repariert:** der Test misst dieselbe Aussage
   dort und prüft zusätzlich, dass `legacy_fields` kein Bindungsfeld von `PROC` ist. Grün.
3. **`test_disposition.test_every_code_citation_resolves_in_the_file_it_names`** — das historische
   Prüfprotokoll `docs/reviews/phase0-disposition.md` zitierte eine Funktion, die diese Runde
   entfernt hat. **Repariert:** die Zeile nennt die Datei und die damalige Funktion, ohne die
   `datei.py:symbol`-Zitatform, und ein datierter Nachtrag sagt, dass dieser Rest entfallen ist —
   Geschichte bleibt lesbar, das tote Zitat verschwindet. Grün. **Mechanismus offen benannt:** der
   Zitat-Test von `test_disposition` erkennt nur die Form `datei.py:symbol`; die Prosafassung
   entzieht sich ihm. Das ist hier richtig (die Funktion gibt es nicht mehr, das Protokoll ist
   Geschichte), aber es ist ein Ausweg, den jemand auch für ein *lebendes* Zitat nehmen könnte —
   der Test sieht das nicht. Wer die Klasse schließen will, misst Prosa-Nennungen mit; das ist
   nicht dieser Strom.

### 6.2 Der eine rote Test, der **nicht** von mir repariert werden kann

`test_repo_hygiene.test_every_decision_pointer_in_a_shipped_kit_file_resolves` ist im Worktree rot:
`board.py`, `backlog_tree.py`, `plan_diagram.py` und `generate_dashboard.py` nennen `DEC-0064`,
`DEC-0065` und `DEC-0066` als ihren Grund — so, wie CLAUDE.md es verlangt —, und der Test verlangt,
dass ein von einer Kit-Datei genannter `DEC` im Store dieses Repos liegt. Die drei Items existieren,
sind aber **nach** `e45c0ca` erfasst und noch **nicht committet**, stehen also im Worktree nicht auf
der Platte.

**Gemessen** (`_round-scratch/TSK-0115/decprobe/`, Kopie außerhalb des Repos, ohne die `.git`-Datei):

| Kopie | Ergebnis |
|---|---|
| Worktree wie er ist | **FAIL** |
| dieselbe Kopie + die drei DEC-Dateien aus `project_memory/decisions/active/` | **PASS** |

Ich schließe das nicht: `project_memory/**` ist forbidden_scope, und der Kernel ist der einzige
Schreiber dieses Verzeichnisses. In der Merge-Runde, die gegen einen Baum mit den drei DEC-Dateien
läuft, ist der Test grün. Die Alternative — die `DEC`-Nummern aus den Kit-Dateien nehmen — wäre
gegen CLAUDE.md („eine gebaute Datei, die eine Entscheidung verkörpert, nennt ihre `DEC`-Nummer")
und würde genau die Zeiger löschen, wegen derer der Test existiert.

Die volle Suite gehört der Merge-Runde (DEC-0050) und wurde hier bewusst nicht gefahren.

## 7. Naht-Zeilen, wörtlich

### 7.1 Strom C, `team-kits/kernel/backlog_types.py` (DEC-0064)

```python
# in AUTOMATA
"MST": _Automaton(
    chain=("PLANNED", "REACHED"),
    terminals=("REACHED", "MISSED", "DROPPED"),
    terminal_from={"MISSED": ("PLANNED",), "DROPPED": ("PLANNED",)},
),
# in ACTIVE_DIRS
"MST": "milestones/active",
# in REQUIRED_FIELDS
"MST": ("title", "due", "derives_from"),
```

Dazu (DEC-0064 (3)) die Datumsprüfung in `state.capture_preflight`: `due` muss
`datetime.date.fromisoformat` lesen können. `PARENT_FIELDS["MST"]` braucht **keine** eigene Zeile —
es wird aus `REQUIRED_FIELDS` abgeleitet (`backlog_types._parent_fields`), was die Testvorrichtung
in `test_board.milestone_type` genau so nachvollzieht.

### 7.2 `backlog_tree.py` — bewusst **nicht** in dieser Runde geschrieben

```python
# in _LABELS
"MST": ("milestone", "milestones"),
# in VIEWS, Produktsicht
children=("FR", "CR", "MST"),
```

**Grund:** `test_board.test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view`
verlangt, dass jeder von einer Sicht genannte Typ in `ACTIVE_DIRS` steht. Solange die Zeilen aus
§7.1 fehlen, wäre die Suite mit diesen zwei Zeilen **dauerhaft rot** — eine rote Suite als Übergabe
ist schlechter als eine benannte Naht. Die zwei Zeilen gehören in dieselbe Anwendung wie §7.1
(Strom C oder die Merge-Runde), und `test_the_milestone_type_is_wired_completely_or_not_at_all`
wird rot, wenn nur ein Teil davon landet.

### 7.3 Strom C, `team-kits/kernel/state.py`, in `_write_board`, innerhalb desselben `try`

```python
        for name, text in plan_diagram.render_all(entries):
            self._write_text_atomic(self.generated_path(name), text, errors="replace")
```

plus `from . import board, plan_diagram` im Kopf von `state.py`. **Abweichung von
`05-diagrams.md`:** die Signatur ist `render_all(entries)` ohne `state` — das Modul liest nichts
außer den Entries, und das ist die Eigenschaft, auf der `is_pristine` steht.

### 7.4 Strom C, `team-kits/kernel/cli.py`, `generate-index`

Die zwei Pfade `generated/plan.drawio.svg` und `generated/mindmap.drawio.svg` mitdrucken. Achtung:
`test_board.test_the_documented_command_writes_and_names_both_artefacts` prüft heute **genau zwei**
gedruckte Zeilen; mit dieser Naht werden es vier, und der Test zieht mit (er heißt dann „all").

### 7.5 Strom C, `team-kits/kernel/approvals.py`

**Die Funktion existiert bereits** (`def open_requests(state: ProjectState) -> list:`) und wird von
`gate_approval.py:284` in allen drei Kits mit **einem** Argument gerufen. Die Naht ist deshalb kein
neuer `def`, sondern ein **optionales** zweites Argument an genau dieser Funktion:

```python
def open_requests(state: ProjectState, now=None) -> list:
```

`now` wird an die Ablaufprüfung durchgereicht (heute `pending_request` je Datei); ohne Argument
bleibt das Verhalten der Haken unverändert, die Tafel setzt ihren Seitenstempel. Danach rufen
Brief, Haken und Tafel dieselbe Regel.

**Warum das hier so genau steht — gemessen** (Kopie außerhalb des Repos, beide Formen gegen
dieselben drei Tests):

| Form | `test_hooks_v2` Kanal-Test | `test_hooks_v2` Ablauf-Test | `test_board` Parität |
|---|---|---|---|
| `open_requests(state, now)` — Pflichtargument, wie §7.5 es vorher schrieb | **rot** | **rot** | grün |
| `open_requests(state, now=None)` | grün | grün | grün |

Die dritte Spalte ist die eigentliche Lehre: der Schiedsrichter, den die Nahttabelle bisher allein
nannte, **sieht diesen Schaden nicht**. Die Naht trägt darum zwei — der zweite ist
`tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`.
H126 schließt sich mit der Naht.

## 8. Bewusst nicht geschlossen, aber benannt

1. **H126 (neu, Rest):** die Ablaufregel für offene Anfragen steht zweimal (Brief und Tafel), und
   die zwei lesen zwei Uhren. Gemessene Kette und Begrenzung stehen im Eintrag; die Naht ist §7.5.
2. **H127 (neu, OFFEN):** eine Handänderung an einem erzeugten Diagramm sieht zwischen zwei
   Zustandsschreibvorgängen niemand. Begrenzung und Naht-Vorschlag im Eintrag.
3. **H128 bleibt unbenutzt.** Der dritte reservierte Kandidat aus `04-build-spec.md` §6 — zwei
   Regeln für die Archivzählung — hat sich mit DEC-0065 (1) von selbst geschlossen: das Dashboard
   zählt das Archiv nicht mehr (`L24` in der Löcherliste ist entsprechend nachgezogen).
4. **Die Diagramme haben heute keinen Auslöser.** Bis §7.3 liegt, entstehen sie nur, wenn jemand
   `plan_diagram.render_all` ruft. Das steht so im Kopf des Moduls und in H127; **nirgends** steht
   „mit dem Board regeneriert".
5. **Die MST-Sektion auf der Tafel warnt, solange §7.1 offen ist.** Ohne Automat kennt der Kernel
   kein Statusvokabular für `MST`; die Seite meldet das dann als `unknown-status`. Das ist wahr und
   verschwindet mit der Naht. In einem echten Projekt tritt es nicht auf, weil ohne §7.1 gar kein
   `MST` erfasst werden kann.
6. **Das Dashboard braucht ein Skript**, um seine Zahlen zu zeigen (JSON-Block + Inline-Skript, wie
   vorher). Die `noscript`-Zeile der Seite sagt das; die Tafel daneben braucht keines.
7. **Der Sichtlauf ist auf diesem Windows-11-Host gemacht** (Segoe UI Variable); auf anderen
   Systemen greift der nächste Name des Schriftstapels, ungesichtet. Übernommen aus
   `03-tokens-final.md`, hier nicht neu gemessen.
8. **Der DEC-Zeiger-Test ist im Worktree rot** und kann es dort bleiben — Messung und Grund in
   §6.2. Er wird grün, sobald der Baum die drei Generation-3-Entscheidungen trägt.
9. **`generate_dashboard.py` wird copy-if-absent installiert** (es steht nicht in
   `repo_kit_owned.txt`). `DEC-0065` (1) — das Dashboard rendert keine Items mehr — gilt darum
   sofort nur für **neue** Installationen; ein bestehendes Projekt behält seine alte Kopie bis zum
   nächsten Kit-Update, das die Datei ersetzt. Das ist der bestehende Update-Weg dieses Kits und
   kein Befund dieses Stroms, aber es gehört in die Merge-Runde, damit niemand die Zahl-Parität
   für schon installierte Projekte als sofort gültig liest.
10. **Die zwei Bänder des Lineals sind eine gemessene Grenze.** Drei Marken innerhalb einer Lücke
   wechseln unten–mitte–unten, die dritte steht also wieder auf der ersten. Selbst nachgemessen
   (`probe_bands.py`): zwei Marken 0 Überlappungen bei 1280 und 390; **drei** Marken einen Tag
   auseinander: 0 bei 1280, **1 Paar** bei 390 (MST-0001 gegen MST-0003, 34 × 16 px); vier Marken:
   **2 Paare** bei 390. Nicht geschlossen — es kostet ein drittes Band oder eine Messung je
   Beschriftung, und es geht nichts verloren: jeder Meilenstein hat unter dem Lineal eine Karte.
   Der Kopf von `board._timeline_view` und der Docstring von
   `test_board_browser.test_ruler_labels_share_no_band` sagen jetzt beide genau das.
11. **Nebenbefund, nicht in diesem Strom behoben:** ein Lauf von `tools/test_hooks.py` aus dem
   Repo-Wurzelverzeichnis hängt eine Zeile an `project_memory/.audit/hook_events.jsonl` des
   **Repos** an (ein Test fährt einen Haken ohne eigenes Arbeitsverzeichnis). Die Zeile aus dem
   Vorlauf vom 2026-09-02 steht dort schon; meine Runde hat eine zweite erzeugt. Sie ist aus dem
   Patch **ausgenommen** (`git diff HEAD -- . ':(exclude)project_memory'`); `project_memory/` ist
   forbidden_scope, also wird hier weder korrigiert noch zurückgesetzt.

## 9. Übergabe

- **Patch:** `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/stream-board.patch`
  (16 Dateien, +3 003 / −891 Zeilen; `project_memory/` ausgenommen).
- **Sichtungen:** `project_memory/staging/TSK-0115/review/build/` — 105 Bilder + `render.json`
  (SHA-256 je Seite), dazu `dashboard.png`, `dashboard-dark.png`, `plan.png`, `mindmap.png`.
- **Layout-Messung:** `review/layout-build.md` / `.json` (0 Überlappungen, 0 Überläufe,
  rechter Rand 0 px).
- **Prüfer-Kopie:** `_round-scratch/TSK-0115/red/` ist **ohne** die `.git`-Datei des Worktrees
  angelegt (`red_first.prepare`), kann als Vorlage dienen.
- **VERSION (vorläufig):** dev/office/research `2026.09.03-6`.
- Kein Commit, kein Push, keine Installation in den globalen Speicher.

## 10. (g)-Tabelle

| Größe | Wert |
|---|---|
| Wanddauer Phase 2 (Spawn → Übergabe) | rund 4 h |
| Tokens | rund 490 k von 1 M im Kontextbudget verbraucht |
| Neue/geänderte Tests | +20 in `test_board.py`, +4 `test_board_browser.py`, +9 `test_plan_diagram.py`, −3/+1 im Dashboard-Abschnitt von `test_hooks.py` |
| Rot-zuerst-Mutationen | 33, alle rot (nach einer Nachbesserung am Test selbst) |
| Zeilen Produktionscode | `board.py` 776 → 1 719, `backlog_tree.py` 321 → 374, `plan_diagram.py` 0 → 431, `generate_dashboard.py` 423 → 244, Hülle 351 → 91 (Stand nach Nacharbeit 3; Nacharbeit 4 ändert keinen Kit-Code) |


## 11. Nacharbeit 1 (Prüfurteil FAIL, B 2 / M 2 / N 7)

Alles im selben Worktree, Messungen in `_round-scratch/TSK-0115/rework1/` (Kopien außerhalb des
Repos), Sonden mit ins Paket gelegt: `probe_b1.py`, `probe_m1.py`, `probe_m2.py`, `probe_bands.py`,
`probe_halves.py`.

### B-1 — `board.open_requests` war der erste Leser eines neuen Verzeichnisses ohne die zwei Abwehren des Moduls

**Selbst nachgemessen, vor dem Fix** (`probe_b1.py`, drei Stores außerhalb des Repos, Anfragedatei
von Hand — `approvals.create_pending_request` kann keine davon schreiben, die TTL ist ihr eigenes
Argument):

| Anfragedatei | Zustandsschreibvorgang | Tafel neu gebaut | Seitengröße |
|---|---|---|---|
| `expires_at_epoch: 99999999999` | 0,02 s, geht durch | **nein** (OSError) | 33 703 B, eingefroren |
| `expires_at_epoch: 1e30` | 0,03 s, geht durch | **nein** (OverflowError) | 33 703 B, eingefroren |
| `item:` = Alias-Graph, Datei **504 Byte** | 0,87 s | ja | **106 990 101 B** |

Die ersten beiden sind die schwerere Hälfte: `_write_board` ist absichtlich fail-soft, also bleibt
die Seite stehen — **bei jedem weiteren Zustandsschreibvorgang**, bis jemand die Datei löscht. „Es
verschwindet nichts" kippt damit zu „es verschwindet alles".

**Gebaut:** die Anfragefelder gehen durch `_flat` (Tiefen- und Zeichenbudget von `_emit`, dieselbe
Abwehr wie für jedes andere Feld), und der Uhrenaufruf ist gefangen (`OSError`, `OverflowError`,
`ValueError` → „unreadable expiry"). **Nachher, gleiche Sonde:** alle drei Fälle Tafel neu gebaut,
35 520 / 35 520 / 35 523 Byte, 0,02 s.

**Rot ohne den Fix:** `test_board.test_a_request_file_nothing_could_write_costs_neither_the_page
_nor_the_write` (drei Fälle, parametrisiert). Zwei Mutationen, beide rot: `except` fängt nur noch
`ZeroDivisionError`; `_flat` zurück auf `str(...)`. Der Test misst, dass die Tafel **neu geschrieben**
wird (`data-generated-at` = `generated_at` des Index) und dass die Seite nicht wächst — verglichen
mit demselben Store ohne die Datei, nicht gegen eine Zahl.

### B-2 — ein Kommentar behauptete einen Stolperdraht, den der genannte Test nicht legte

`backlog_tree` sagte, `test_board.test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can
_produce` halte `_REASON_LABELS` in beide Richtungen gegen `MESSAGES`; der Test las die Karte nie.
**Gebaut:** beide Enden stehen jetzt in genau diesem Test, dazu die Zusage, dass jede Bahn ein Wort
liefert; der Kommentar sagt jetzt, was der Code baut, und benennt, dass er es eine Runde lang nicht
tat. **Rot ohne den Fix:** zwei Mutationen (toter Eintrag; fehlender Eintrag) — beide rot.

### M-1 — ein Titel ohne Umbruchgelegenheit macht die Seite breiter als das Fenster

**Selbst nachgemessen** (`probe_m1.py`, Titel = `team-kits/dev-team/templates/repo/scripts/
progress.dashboard.template.html`, also die Titelform dieses Repos): bei 390 px stand das Dokument
**171 px** breiter als das Fenster (Board +137, Produkt +116, System +171); bei 1280 und 1920 px 0.

**Welche Hälfte trägt, gemessen statt behauptet** (`probe_halves.py`, vier Läufe): ohne
`min-width: 0` → 0 px; ohne `overflow-wrap: anywhere` → 171 px; ohne beides → 171 px. Also trägt
**nur** die Umbruchregel. Die `min-width`-Zeile ist deshalb **nicht** im Paket — eine Zeile, die
keinen Fix trägt, ist eine Zeile, der der nächste Leser vertraut; der Kommentar sagt, dass sie
gemessen und verworfen wurde.

**Und die zweite Hälfte des Befunds:** die Überlaufsonde des Design-Passes fragt jedes Element
`scrollWidth > clientWidth` — ein Element, das **wächst**, meldet damit nichts. Der neue Test misst
darum das **Dokument**: `test_board_browser.test_a_title_that_is_one_long_word_does_not_widen_the
_page`, drei Breiten × jeder Reiter × beide Fokuslisten × offene Akte, mit einer Fixture aus
Pfad-Titel und einem 140-Zeichen-Wort. **Rot ohne den Fix.** Nachher: 0 px Überhang, gesichtet unter
`review/build/rework1-longtitle-*.png` (12 Bilder, 390 hell/dunkel und 1280, `errors: []`).

### M-2 — `html.escape` beantwortet eine andere Frage als „darf das Zeichen in ein XML-Dokument"

**Selbst nachgemessen** (`probe_m2.py`, Titel `NUL SOH " NUL first"`): beide Diagramme **nicht
wohlgeformt**, und `is_pristine` sagte trotzdem `pristine` — richtig, denn pristine heißt „gleich
einem frischen Render", und der war genauso kaputt. Die Datei kann sich also nicht selbst melden.

**Gebaut:** `_clip` ersetzt, was XML 1.0 §2.2 nicht erlaubt (C0-Steuerzeichen außer Tab/Zeilenumbruch/
Wagenrücklauf, Surrogathälften) durch U+FFFD — eine Tür, weil jede Beschriftung durch `_clip` geht.
Dabei kam ein zweiter, eigener Befund heraus: `digest_of` läuft **vor** jeder Beschriftung und
`str.encode` verweigert eine einzelne Surrogathälfte → `UnicodeEncodeError` aus dem Renderer. Das
Diagramm bekommt jetzt dieselbe Toleranz, die `state._write_text_atomic` schon hat
(`errors="replace"`), mit der genannten Folge (zwei Items, die sich nur in einer nicht kodierbaren
Hälfte unterscheiden, hashen gleich). **Nachher:** beide Dateien wohlgeformt, Modell parst.
**Rot ohne den Fix:** `test_plan_diagram.test_a_control_character_in_a_title_cannot_break_the_model`
(drei Formen), zwei Mutationen, beide rot.

### Die kleinen Befunde

N-1 Stempel und Zeilenzahlen in §6/§10 nachgezogen · N-2 die Klammer über eine „Schema-Datei" in §2
gestrichen (§7.1 sagt korrekt: aus `REQUIRED_FIELDS` abgeleitet) · N-3 Lineal-Grenze in Code und
Test auf das Gemessene gebracht, siehe §8 Punkt 10 · N-4 copy-if-absent, §8 Punkt 9 · N-5 ohne
Skript fehlen die drei Zahlen, die `noscript`-Zeile sagt es — nichts zu tun · N-6 Mechanismus des
Zitat-Auswegs in §6.1 benannt · N-7 die Zeile in `.audit/hook_events.jsonl` bleibt benannt und
außerhalb des Patches.

### Läufe dieser Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `tools/test_board.py + test_board_browser.py + test_plan_diagram.py` | **90 grün** (vorher 83) |
| `tools/test_hooks.py -k dashboard` | 6 grün |
| `tools/test_kernel.py -k path_rule` · `tools/test_board.py -k no_kernel_writer` | je 1 grün |
| Rot-zuerst gesamt (`red_first.py`) | **40 Mutationen, 40 rot** (33 aus Runde 1 + 7 dieser Nacharbeit) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python tools/bump_kit_version.py` | **2026.09.03-4** |

Kein Sammellauf über die neun Suiten (Auftrag der Nacharbeit); die volle Suite bleibt der
Merge-Runde. Patch neu geschrieben: 16 Dateien, +3 259 / −892.

**Wanddauer Nacharbeit 1:** rund 1,5 h. **Tokens:** rund 120 k.


## 12. Nacharbeit 2 (Wiederholungsprüfung FAIL: ein Befund, zwei Zeilen)

### M-3 — die Abwehr galt für drei Felder, gemessen war sie an einem

`open_requests` liest drei Felder einer Anfragedatei, und der Kopf behauptete den Schutz für alle
drei. `_UNWRITABLE_REQUESTS` und `red_first.py` setzten die Alias-Bombe aber nur in `item`: ein
Rückfall auf `str()` bei `request_id` oder `kind` ließ die ganze Datei grün. Das ist die
Deckungslücke, nicht ein zweiter Defekt — die drei Zeilen im Code waren richtig.

**Selbst nachgemessen** (`probe_m3.py` / `probe_m3_before.py`, Kopie außerhalb des Repos, dieselbe
~500-Byte-Bombe, je Feld einmal die Schranke gelöst):

| Feld ohne Schranke | Zustandsschreibvorgang | Spitzenspeicher | Seite |
|---|---|---|---|
| `request_id` | 5,90 s | **28,01 MB** | 36 704 B — **unverändert** |
| `kind` | 6,61 s | 558,11 MB | **106 991 429 B** |
| `item` | 6,83 s | 510,19 MB | 106 991 287 B |
| *mit Schranke, alle drei* | **0,02–0,03 s** | **0,19 MB** | 36 704–36 851 B |

`request_id` ist der Fall, der die alte Zusage nicht hätte fangen können: das Feld erreicht die
Seite **nirgends**, die Seitengröße bleibt gleich, und nur die Zeit und der weggeworfene String
verraten es. Deshalb misst der Test jetzt zusätzlich `tracemalloc` — dieselbe Wahl und derselbe
Grund wie in `test_board.test_an_alias_bomb_cannot_stretch_a_state_write` (eine Stoppuhr trennt die
Fassungen erst bei Hunderten von Megabyte). Die Schranke liegt bei 8 MB: 42-fach über dem
gemessenen Bedarf mit Fix und 3,5-fach unter dem billigsten Defektfall.

**Gebaut:** `_alias_bomb_request(field)` baut die Bombe je Feld, `_UNWRITABLE_REQUESTS` hat fünf
Formen statt drei, der Test bekommt die Speicher- und Zeitzusage. **Rot ohne den Fix:** vier
Mutationen auf demselben Testknoten (Uhr, `item`, `request_id`, `kind`) — alle vier rot.

### N-8 — eine Aussage, ein Ort

`.card .title` stand mit `overflow-wrap: anywhere` zweimal: im Blatt des Design-Passes und noch
einmal in der Sammelregel dieser Runde. Die Sammelregel nennt die Karte jetzt nicht mehr; der
Kommentar sagt, dass die Karte die Regel schon oben trägt und warum sie hier nicht wiederholt wird.
Die Mutation „Sammelregel weg" bleibt **rot** (die Baumzeilen, die Fokuszeilen und die
Meilensteinflächen hängen allein an ihr), und `test_board_browser` ist nach der CSS-Änderung erneut
gelaufen.

### Läufe dieser Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `tools/test_board.py` (voll) | **74 grün** (vorher 72; zwei neue Formen) |
| `tools/test_board_browser.py` | 5 grün — gefahren, weil N-8 CSS ändert, die dieser Test misst |
| Rot-zuerst (`red_first.py`) | die vier Anfrage-Mutationen und die Titel-Mutation: **rot** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python tools/bump_kit_version.py` | **2026.09.03-5** |

Patch neu: 16 Dateien, +3 292 / −892. Sonden im Paket ergänzt: `probe_m3.py`,
`probe_m3_before.py`. Kein Commit, kein Push.

**Wanddauer Nacharbeit 2:** rund 35 min. **Tokens:** rund 45 k.


## 13. Nacharbeit 3 (dritte Prüfung FAIL: ein blockierender Textbefund, drei Pflegepunkte)

### M-4 — die Naht übergab eine Funktion, die es schon gibt

`§7.5` und `H126` beschrieben Strom C ein **neues** `def open_requests(state, now)`. Die Funktion
existiert bereits (`team-kits/kernel/approvals.py`, `def open_requests(state: ProjectState)`), und
`gate_approval.py:284` ruft sie in allen drei Kits mit **einem** Argument.

**Selbst nachgemessen** (`probe_m4.py`, Kopie außerhalb des Repos, beide Signaturen gegen dieselben
drei Tests):

| Form | `test_hooks_v2` Kanal-Test | `test_hooks_v2` Ablauf-Test | `test_board` Parität |
|---|---|---|---|
| `open_requests(state, now)` — so, wie die Naht es schrieb | **rot** | **rot** | grün |
| `open_requests(state, now=None)` | grün | grün | grün |

Die dritte Spalte ist der eigentliche Befund: der Schiedsrichter, den die Nahttabelle allein nannte,
**sieht den Schaden nicht**. Ein Strom C, der die Zeile wörtlich anwendet, hätte zwei Tests
zerbrochen und meinen Test grün gelassen.

**Gebaut (nur Text):** `§7.5` beschreibt jetzt ein **optionales** `now=None` an der vorhandenen
Funktion, mit der Messtabelle und mit **zwei** Schiedsrichtern — der zweite ist
`tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`,
wörtlich in der Nahttabelle. `H126` ebenso, dazu die Korrektur, dass die Regel **dreimal** steht
(`approvals.open_requests`, `report.generate_session_brief`, `board.open_requests`). Die
Zyklus-Begründung nennt jetzt den bindenden Weg `approvals → state → board` statt `report`; im
Kopf von `board.open_requests` ebenfalls (dort verifiziert an den Importzeilen:
`approvals.py:56 from .state import ProjectState`, `state.py:71 from . import board`).

### N-11 — ein Feld, das niemand liest, wurde berechnet

`request_id` wurde in den Anfragedatensatz geschrieben und im ganzen Modul nie gelesen; der
billigste Defektfall (28 MB für einen weggeworfenen String) entstand also für nichts. **Entfernt**,
mit Grund im Code: nichts auf der Seite zeigt die Id, und wenn die Naht aus §7.5 liegt, kommt sie
mit dem Datensatz aus `approvals.pending_request` statt aus einer zweiten Berechnung hier.

Die Fixture zu diesem Feld bleibt — sie misst jetzt die **Gegenrichtung**: ein Feld, das dieser
Leser nicht liest, darf beliebig aussehen und muss nichts kosten (gemessen: 0,19 MB, Seite
unverändert). Die Rot-zuerst-Mutation dazu ist entfallen, weil die Zeile, die sie traf, weg ist.

### N-9 — eine Zahl, ein Ort

`8 * 1024 * 1024` stand dreimal und `took < 30` dreimal in `tools/test_board.py`. Jetzt:
`_MEMORY_BUDGET` und `_STATE_WRITE_SECONDS`, je eine Konstante mit ihrem Grund, drei Aufrufstellen.
Beim Zeitbudget steht ausdrücklich dabei, dass es die **Hausform der Suite** ist und kein Defekt
dieser Runde von ihm gefunden wurde — die tragende Messung ist die Allokation.

### N-10 — die Reserve hing an einer Zahl, die zweimal stand

Die Bombentiefe stand als `range(1, 21)` **und** als `*a20`. Beim Nachmessen ist mir genau das
passiert: eine Sonde senkte die Schleife und ließ die Referenz stehen, die Datei parste nicht mehr,
der Leser übersprang sie — und der „Defekt" maß **0,19 MB und sah harmlos aus**.

**Gebaut:** `_BOMB_LEVELS` steht einmal, der Endalias wird daraus abgeleitet; und der Test prüft,
dass die Datei **ankommt**, bevor er irgendetwas über Kosten behauptet. Gemessen
(`probe_arrival.py`): Ableitung wieder durch das Literal ersetzt und die Schleife gesenkt →
**3 von 5 Formen rot**.

**Was der Block NICHT tut**, korrigiert in Nacharbeit 4 (N-13): er fängt keinen Fall, der sonst
durchginge. Ohne ihn scheitern dieselben drei Formen an `page.figures["you"] == 1` drei Zeilen
tiefer — gemessen, mit und ohne Block je „3 failed, 2 passed". Was er ändert, ist **wo** das
Scheitern steht: mit Block nennt die Meldung die Fixture (`item: *a20`, der nicht auflösbare Alias),
ohne ihn liest sie sich als Produktdefekt („the request itself no longer arrives"), während der
Fehler in der Testdatei liegt. Das ist der Grund, aus dem er bleibt — nicht zusätzliche Deckung.

### Läufe dieser Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `tools/test_board.py` + `tools/test_board_browser.py` (beide voll) | **79 grün** |
| Rot-zuerst gesamt (`red_first.py`) | **41 Mutationen, 41 rot** (die `request_id`-Mutation entfiel mit der Zeile) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python tools/bump_kit_version.py` | **2026.09.03-6** |

Patch neu: 16 Dateien, +3 364 / −896. Sonden ergänzt: `probe_m4.py`, `probe_arrival.py`,
`probe_n10.py`. Kein Commit, kein Push.

**Wanddauer Nacharbeit 3:** rund 50 min. **Tokens:** rund 60 k.


## 14. Nacharbeit 4 (vierte Prüfung PASS, vier Pflegezeilen)

Kein Kit-Code berührt: die Änderungen liegen in `tools/test_board.py` (N-12, N-14), in
`docs/POST_V2_WISHLIST.md` (N-15) und in diesem Protokoll (N-13). `bump_kit_version.py` meldet
folgerichtig **unchanged (2026.09.03-6)**.

### N-12 — die Ankunftszusage las den TYP, nicht die STÄRKE

`isinstance(value, list)` sagt nur, dass die Aliaskette aufgelöst hat. Eine flache „Bombe" gilt
damit als angekommen, bleibt aber unter jeder Kostenschranke darunter — die Zusagen beweisen dann
nichts.

**Selbst nachgemessen** (`probe_n12.py`, Kopie außerhalb des Repos, **beide** Abwehren im Renderer
entfernt):

| Fixture | Zusage | Ergebnis |
|---|---|---|
| `_BOMB_LEVELS = 8` | nur Typ (alter Stand) | **5 passed** — der Defekt bleibt unsichtbar |
| `_BOMB_LEVELS = 3` | nur Typ | **5 passed** |
| `_BOMB_LEVELS = 8` | Stärke (neu) | **3 failed** — und die Meldung nennt die Fixture |
| `_BOMB_LEVELS = 3` | Stärke | **3 failed** |
| `_BOMB_LEVELS = 21`, Code heil | Stärke | 5 passed |

**Gebaut, als Definition statt als Zahl:** die Fixture muss ihre WIRKUNG beweisen — was `str()` auf
dem bombierten Feld erzeugen würde, muss größer sein als die Seite, zu der die Anfrage kommt. Der
Preis wird über den Graphen gerechnet (`_flattened_length`, memoisiert über `id()`, linear in den
Ebenen) und nicht gebaut: die Stärke zu messen darf nicht kosten, was die Bombe kostet. Damit hängt
`_BOMB_LEVELS` an seinem Zweck statt an einer Zahl, der jemand vertraut.

### N-13 — mein Satz schrieb dem Block einen Fang zu, den er nicht hat

**Selbst nachgemessen** (`probe_n13b.py`, Fixture-Ableitung gebrochen): mit Block „3 failed,
2 passed", ohne Block ebenfalls „3 failed, 2 passed". Der Block fängt also **keinen** Fall, der
sonst durchginge — `page.figures["you"] == 1` tut das drei Zeilen tiefer. Was er ändert, ist **wo**
das Scheitern steht: mit Block nennt die Meldung die Fixture (`item: *a20`), ohne ihn liest sie sich
als Produktdefekt, während der Fehler in der Testdatei liegt. §13 sagt das jetzt so.

### N-14 — „die tragende Messung" galt an der dritten Aufrufstelle nicht mehr

Seit `request_id` nicht mehr gelesen wird (N-11), erreicht jedes Feld, das die Tafel liest, auch die
Seite — die Größenzusage fängt beide Defekte allein. **Gemessen** (`probe_n13_n14.py`): Speicher-
zusage an dieser Stelle gelöscht und beide Abwehren entfernt → weiter „2 failed"; Speicherzusage
gelöscht und Code heil → „5 passed". **Gebaut:** der Kommentar an `_MEMORY_BUDGET` benennt jetzt die
zwei Stellen, an denen er trägt, und gibt der dritten ihren eigenen Grund — sie steht für den Tag,
an dem wieder ein Feld gelesen wird, das die Seite nicht zeigt.

### N-15 — drei Leser, zwei Uhren

`H126` sagte „die zwei Leser lesen verschiedene Uhren". Es sind drei Leser auf zwei Uhren:
`approvals.open_requests` fragt `has_expired`, und das liest `time.time()` (`approvals.py:2047`) —
dieselbe Uhr wie der Sitzungsbrief; die Tafel liest ihren Seitenstempel. Überschrift, Satz und
Übersichtszeile korrigiert, mit dem Zusatz, warum die Naht deshalb ein **optionales** `now` ist:
die zwei Uhren bleiben zwei, die Regel wird eine.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `tools/test_board.py` (voll) | **74 grün** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python tools/bump_kit_version.py` | **unchanged (2026.09.03-6)** — kein Kit-Code berührt |

Patch neu; Sonden ergänzt: `probe_n12.py`, `probe_n13b.py`, `probe_n13_n14.py`. Kein Commit, kein
Push.

**Wanddauer Nacharbeit 4:** rund 30 min. **Tokens:** rund 35 k.
