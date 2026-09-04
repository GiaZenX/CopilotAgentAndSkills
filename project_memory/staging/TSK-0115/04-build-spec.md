# 04 — Bauanleitung für Phase 2 (Opus)

Was hier steht, muss ohne die Design-Phase ausführbar sein. Offene Entscheidungen stehen in
`user-feedback.md` mit Nummer; wo eine davon den Bau ändert, ist es hier gesagt. Die Prototypen
(`make_mockups.py`, `make_diagrams.py`) sind das Vorbild für jede Zeile — sie importieren den Kernel und
bauen auf `board._detail`, `board._section`, `board._tree_view`, `backlog_tree.arrange` auf, damit Phase 2
so wenig wie möglich neu erfindet.

## 0. Stand nach den Phasen 1b–1d (verbindlich für Phase 2)

- **Visuelles System = `03-tokens-final.md`** (E, vom Nutzer gewählt) — nicht `03-tokens.md` (Phase 1,
  abgelöst) und nicht A–D. Code-Quelle: `directions.M_TOKENS_LIGHT`, `M_TOKENS_DARK`, `M_FONTS`,
  `M_RULES`, `E_RULES` plus Basis in `make_mockups.STYLE`/`NOSCRIPT_STYLE`/`SCRIPT`.
- **Entscheidungen im Zustand:** `DEC-0064` (MST ist ein Typ; Option A unten), `DEC-0065` (ein Renderer,
  Diagramme in `generated/`, Records zugeklappt, drei Zahlen, `READY` = in flight, Englisch).
- **Markup-Zusätze aus 1d** (`08-final.md`): Falt-Knopf je Knoten mit Kindern (`button.fold[data-fold]
  [aria-expanded]`, Platzhalter `.fold-space` sonst), `.row` um Falt-Knopf und `node-face`, `hidden` auf
  den `.group` eines Knotens ab Tiefe `FOLD_DEPTH = 1`, `.tree-tools` mit `[data-fold-all]` je Sicht,
  Skriptzusatz (Konstante, kein Item-Inhalt), `noscript` blendet `.fold` und `.tree-tools` aus.
- **Layoutregeln aus 1d** (`03-tokens-final.md`, Tabelle): `box-sizing: border-box` nach jedem `all: unset`,
  fließende Slots, gestapelt `flex: 0 0 auto`, Slot-Kopf mit Zahl neben Namen, Lineal mit drei Bändern.
- **Vier Zustände, die Phase 2 rendert und misst:** leer, gesund, blockiert, Zeitleiste — die Fixtures aus
  `fixtures.py` und `milestones.yaml`; die Bilder in `review/final/` sind der Vergleich.

## 1. Dateien und die eine Entscheidung dahinter

**Ein Renderer der Items: `team-kits/kernel/board.py`.** Das Dashboard des dev-team-Kits rendert keine
Items mehr (Begründung und Messung: `parity.md`).

| Pfad | Änderung |
|---|---|
| `team-kits/kernel/board.py` | die Seite aus `make_mockups.py`: Kopf, First-Streifen mit Fokus-Listen, Reiter, Typreihenfolge, Slots mit Leerregel, T-Karte, Records-Block, Timeline (je nach Frage 4), `_STYLE` = `make_mockups.STYLE`, `_SCRIPT` + Fokus-Zusatz (weiter eine Konstante ohne Item-Inhalt) |
| `team-kits/kernel/backlog_tree.py` | `_LABELS` um die Record-Typen (`make_mockups.LABELS`), sonst nichts — die Bäume bleiben |
| `team-kits/kernel/plan_diagram.py` | **neu**: `render_all`, `is_pristine`, `digest_of` aus `make_diagrams.py` (`05-diagrams.md`) |
| `team-kits/dev-team/templates/repo/scripts/generate_dashboard.py` | rendert `generated/dashboard.html` nur noch mit `repo_vitals` (`compute_repo_vitals`) und einem relativen Verweis auf `board.html`; `VIEWS`, `assign_views`, `load_index`-Item-Pfad, `read_item`, `next_status`, `is_finished`, `relations`, `archive_summary` entfallen. Der dokumentierte Befehl bleibt: `python scripts/generate_dashboard.py` (Verfassung §2.3 / Phase 8 bleiben wahr, kein D-Seam) |
| `team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html` | die Hülle schrumpft auf Vitalwerte + Verweis; **gleiches visuelles System** wie das Board (Token-Block kopiert, kein zweiter Look) — oder die Datei geht ganz und der Generator schreibt die kleine Seite selbst; Phase 2 entscheidet an der Zahl der Zeilen und sagt es |
| `tools/test_board.py` | `_Board`-Parser folgt dem Markup (`card blocked`, `.figure`, `[data-focus-list]`, `.slot`, `.records`), neue Tests aus §5 |
| `tools/test_plan_diagram.py` | **neu**, §5 |
| `tools/test_hooks.py` (Dashboard-Abschnitt, Zeilen ~1843–2100) | Tests über `data["views"]`/`archive` werden Tests über Vitalwerte und Verweis; `test_the_documented_dashboard_command_survives_the_write_scope_gate` bleibt unverändert. Geteilte Datei mit Strom B → Seam-Tabelle |
| `team-kits/*/VERSION` | `python tools/bump_kit_version.py` vor jedem Urteil (Hausregel 7) |
| `docs/POST_V2_WISHLIST.md` | nur unter H126–H128 (§6), mit Modulpräfix in jeder Nennung |

Was **nicht** angefasst wird (Scope): `state.py`, `cli.py`, `backlog_types.py`, `report.py`,
`approvals.py`, Hooks, Verfassungen, Templates der anderen Kits, `templates/project_memory/**`.

## 2. Der Renderer, Stück für Stück (Reihenfolge = Reihenfolge auf der Seite)

1. **`render(state, entries, generated_at)`** behält die Signatur — `state._write_board` ruft sie so.
   Neu gelesen wird **eine** Quelle: `approvals/pending/` (Regel in `02-data-contract.md`). Ort der Regel:
   sie steht heute in `report.generate_session_brief`; `report` importiert `state`, `state` importiert
   `board`, also darf `board` `report` nicht importieren (Zyklus, wie `board.VALUE_MAX_CHARS` es erklärt).
   Zwei Wege: (a) C zieht eine Funktion `approvals.open_requests(state, now)` heraus, die beide rufen
   (**Seam**, empfohlen); (b) bis dahin liest `board` das Verzeichnis selbst mit derselben Regel, und
   `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` hält die beiden Leser
   gegeneinander (rot, wenn einer die Ablaufregel verliert). Phase 2 baut (b), meldet (a).
   `now` kommt vom Aufrufer wie `generated_at` (Reinheit: kein `time.time()` im Renderer; `state` reicht
   die Epoche der einen Uhr mit — eine Zeile in `_write_board`, C-Seam; bis dahin `time.time()` in `board`
   mit Test auf Determinismus bei eingefrorener Uhr).
2. **Bahn** (`lane`) und **Typreihenfolge** (`type_order`) wie im Prototyp, beides aus `AUTOMATA` und
   `backlog_tree.ROOT_TYPES` abgeleitet; keine Typliste.
3. **First**: drei `<button class="figure" data-focus>` mit `.num`/`.word`/`.ex`, darunter drei
   `<div class="focus-list" data-focus-list data-count>`; die Zahl auf dem Knopf und `data-count` der Liste
   sind dieselbe Zählung (Test §5).
4. **Sektionen**: `section()` aus dem Prototyp ersetzt `board._section`s Markup, **behält seine
   Warnungen** (Prototyp ruft `board._section` heute nur dafür — Phase 2 trennt Warnungen von Markup, eine
   Funktion `_column_warnings`). Leerregel: leerer Kettenslot schmal, leerer Endzustand nicht gezeichnet,
   `.empties` mit `.ends`/`.chain`.
5. **Karte**: `card()`; `face_title()` für `TSK` aus Pflichtfeldern. `data-lane` auf jeder Karte.
6. **Records**: `records_section()`; Typen ohne Statusvokabular ohne Gruppenkopf.
7. **Timeline** (Frage 4): `timeline_view()`; bei Option A aus `MST`-Entries, bei B aus Items mit `due`.
   In beiden Fällen ohne Prozent, mit Ebenenwechsel der Beschriftungen (auch für die Heute-Marke).
8. **Akte, Bäume, Skript, noscript**: unverändert bis auf CSS und den Fokus-Zusatz im Skript.

Was der Renderer NIE tut, bleibt: Zustand lesen, den er nicht bekam (außer `approvals/pending/`, s. o.);
schreiben; eine Anfrage nach außen; Item-Inhalt ins Skript.

## 3. Der Auslöser — unverändert für das Board, ein Seam für die Diagramme

Das Board: `state._regenerate_index_locked` → `_write_board` — jeder Kernel-Schreiber, eine Uhr
(`test_board.test_every_state_write_leaves_a_board_as_fresh_as_the_index`). Nichts zu tun.
Die Diagramme: die Zeilen in `05-diagrams.md` für `state._write_board` und `cli.py` (C). Bis zum Merge
liefert Phase 2 Modul + Tests; die Behauptung „mit dem Board regeneriert" steht **nirgends**, bis
`test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` sie um `plan_diagram`
erweitert grün ist.
Das Dashboard: bleibt Hand-Schritt der Checkliste; da es keine Items mehr trägt, veraltet daran nichts, was
das Board auch hat.

## 4. Fixtures

`fixtures.py` baut `empty`, `healthy`, `blocked` aus einer Kopie dieses Repos in
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0115\fixtures\`; für Tests genügt, was `test_board`
heute tut (Items durch `ProjectState.capture` und die Walker aus `conftest`, Entries direkt an `render`).
Für **blocked** braucht ein Test `blocked_by` (ein Feld, das `capture` nimmt) und eine Anfrage in
`approvals/pending/` — die schreibt `approvals.create_pending_request` über `cli request-approval`
(`tools/test_approvals_dispatch.py` zeigt den Weg); eine von Hand geschriebene Anfrage wäre eine Form,
die nichts erzeugt.

## 5. Tests — jeder rot ohne seinen Fix, je FR getrennt (DEC-0062 (4))

Rot-zuerst nach Hausregel 5: Defekt in einer Kopie außerhalb des Repos wiederherstellen (Regel
entfernen, Attribut weglassen), Test scheitern sehen, zurücksetzen, Namen ins Protokoll. Namen sind
Vorschläge, Eigenschaften nicht. Alle lesen die gerenderte Seite über `_Board` (DOM), nie einen String.

**FR-0075 (Board)**

| Test | Misst | Rot, wenn |
|---|---|---|
| `test_board.test_the_first_strip_counts_blocked_waiting_and_in_flight_from_the_state` | echter Store mit einem `blocked_by`, einer offenen Anfrage, einer `IN_PROGRESS`-TSK → `.figure .num` = 1/1/1 und `data-count` der Listen gleich | eine Zählung eine andere Quelle liest als die Liste |
| `test_board.test_an_expired_approval_request_is_not_waiting_on_anyone` | Anfrage mit `expires_at_epoch` in der Vergangenheit → 0, keine Karte blau | die Ablaufregel fehlt |
| `test_board.test_a_blocked_card_carries_its_blocker_on_its_face` | `button.card.blocked .flag` nennt die Id aus `blocked_by`, Liste oder Skalar (BUG-0015-Form) | das Merkmal nur in der Akte steht |
| `test_board.test_living_types_precede_records_and_no_type_is_lost` | Reihenfolge der `section.type` = Wurzeln, Automaten, dann `details.records`; Summe aller Karten + Record-Zeilen = Entries | ein Typ weder Sektion noch Record ist |
| `test_board.test_an_empty_end_state_is_named_not_drawn` | kein `.slot[data-status=<terminal>]` mit `data-count=0`; `.empties .ends` nennt ihn; ein leerer Kettenslot ist da | die Leerregel kippt (beide Enden) |
| `test_board.test_a_task_without_a_title_shows_its_work_on_the_face` | TSK ohne `title` → Fläche trägt `type`, Ziel, Rolle | die Fläche leer bleibt (heutiger Stand) |
| `test_board.test_the_page_script_carries_no_item_content_at_all` | bestehend; deckt den Fokus-Zusatz | — |
| `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` | `open_approvals` des Briefs = Ids der blauen Karten (bis Seam (a) landet) | ein Leser die Regel verliert |
| `test_hooks.test_the_dashboard_carries_no_item_of_its_own_and_points_at_the_board` | `dashboard.html` ohne Item-Id des Stores, mit `href="board.html"`, Vitalwerte vorhanden | das Dashboard wieder zählt |
| `test_hooks.test_the_documented_dashboard_command_survives_the_write_scope_gate` | bestehend | — |
| Playwright (Messrig, nicht Suite — die Suite hat keinen Browser, `test_board`-Kopf): Fokusklick blendet ab und öffnet die Liste; `page.on("request")` nur die eigene URL | protokolliert wie in TSK-0079 | |

**FR-0075, Phase 1d (Layout und Einklappen)** — die DOM-Tests in `tools/test_board.py`, die
Bounding-Box-Tests in einem eigenen `tools/test_board_browser.py`, das Playwright braucht und ohne
Playwright **nicht still grün** wird: `pytest.importorskip("playwright")` mit Grund, und das Protokoll
nennt den Lauf mit Zahl der Bilder — so wie TSK-0079 seinen Browserlauf protokolliert hat.

| Test | Misst | Rot, wenn |
|---|---|---|
| `test_board_browser.test_no_two_cards_of_the_board_overlap_at_any_width` | Bounding-Boxes aller `.slot > .card` bei 1280, 1920, 390 (die Gruppen aus `measure_layout.GROUPS`): kein Paar schneidet sich um mehr als 1 px in beiden Achsen; Fixture = ein Store mit zwei belegten Nachbarspalten | `box-sizing` fehlt (vorher 110 Paare) oder die gestapelte Basis zurückkommt (vorher 327) |
| `test_board_browser.test_the_board_uses_the_width_it_is_given` | bei 1280 und 1920: rechter Rand des breitesten Slots ≥ Fensterbreite − `body`-Innenabstand − 1 px, für jede Typzeile mit Karten | ein Slot wieder fest 15 rem ist (vorher 115 / 752 px leer) |
| `test_board_browser.test_a_fold_control_works_by_keyboard_and_shows_its_focus` | `focus()` auf den ersten `[data-fold]` der Systemsicht, `Enter` → seine `.group` verlieren `hidden`, `aria-expanded` wird `true`; `getComputedStyle(...).outlineStyle` ≠ `none` bei `:focus-visible` | der Knopf kein `<button>` mehr ist oder der Ring fehlt |
| `test_board.test_every_deep_group_starts_hidden_and_every_root_open` | DOM (`_Board`): jede `.group` unter einem Knoten mit `data-depth` ≥ 1 trägt `hidden`, keine unter einer Wurzel; jeder Knoten mit Gruppen trägt genau einen `[data-fold]`, jeder ohne einen `.fold-space` | der Standard kippt oder ein Knoten keinen Knopf bekommt |
| `test_board.test_a_fold_control_states_what_it_hides` | `aria-expanded="false"` genau dann, wenn die Gruppen des Knotens `hidden` tragen; `aria-label` nennt die Id des Knotens | Zustand und Aussage auseinanderlaufen |
| `test_board.test_the_page_script_carries_no_item_content_at_all` | bestehend; deckt den Falt-Zusatz | — |
| `test_board.test_the_noscript_page_shows_every_group_and_no_fold_control` | die `noscript`-Regeln enthalten `.fold` und `.tree-tools` im `display: none`-Satz und `[hidden]` im `display: block`-Satz — geparst aus dem `<noscript><style>` der Seite, nicht als Zeichenkette über die Datei | ohne Skript Gruppen unsichtbar blieben |
| `test_board_browser.test_ruler_labels_share_no_band` | Zeitleisten-Fixture mit zwei Marken einen Tag auseinander und Heute dazwischen, 390 px: keine zwei Beschriftungen (`.tick .id`, `.today span`) schneiden sich | die Bänder zusammenfallen (vorher 1 Überlappung) |

**FR-0079 (Timeline)** — Option A (B analog mit `due`-Items)

| Test | Misst | Rot, wenn |
|---|---|---|
| `test_board.test_a_milestone_stands_on_the_timeline_with_the_goals_it_names` | Entries mit `MST`-Zeilen direkt an `render` → `[data-view=timeline] .milestone[data-milestone]` je Item, `.goals` mit Knöpfen der genannten Wurzeln, Zahlen je Bahn = Nachkommen im Systembaum | eine Zahl den Archiv-Anteil behauptet oder ein Ziel fehlt |
| `test_board.test_a_milestone_past_its_date_and_not_reached_is_late` | `due < today`, Status nicht terminal → `.milestone.late`; erreicht → nicht | die Bahn statt des Datums entscheidet |
| `test_board.test_two_milestones_a_day_apart_keep_both_labels` | zwei Marken < 9 % auseinander → die zweite trägt `up` | die Regel fehlt |
| `test_board.test_a_milestone_with_an_unreadable_date_is_shown_with_no_date` | `due: gestern` → Karte „no date", keine Marke, kein Traceback | ein Datum den Zustandsschreib fällt |

**FR-0080 (Diagramme)**

| Test | Misst | Rot, wenn |
|---|---|---|
| `test_plan_diagram.test_the_diagram_is_a_pure_function_of_the_entries` | zwei Renders gleiche Bytes; kein `datetime`/`time`/`random` im Modul (AST) | eine Uhr hineinkommt |
| `test_plan_diagram.test_a_hand_edit_is_told_from_a_stale_file` | die drei Urteile aus `05-diagrams.md` | Digest oder Vergleich fehlt |
| `test_plan_diagram.test_the_file_is_well_formed_and_carries_a_drawio_model` | `staging._assert_xml_wellformed` besteht; `content` parst; Wurzel `mxfile`; je Zelle eine `mxGeometry` | das Modell fehlt oder die Pilot-Form (Bild ohne Modell) durchgeht |
| `test_plan_diagram.test_every_cell_names_an_item_the_entries_hold` | Ids in Zellen ⊆ Ids der Entries; jedes Item unter einer Wurzel hat eine Zelle | ein Item verschwindet oder eins erfunden wird |
| `test_plan_diagram.test_status_is_never_carried_by_colour_alone` | jede gefüllte Blattzelle trägt das Bahn-Wort | die Farbe allein bleibt |
| `test_plan_diagram.test_no_colour_outside_the_named_palette` | Hexwerte im Modul ⊆ Palette (AST über Konstanten) | ein Literal hinzukommt |
| nach dem Merge: `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` um die Diagrammdateien erweitert | | |

## 6. Lochkandidaten H126–H128 (Phase 2 misst, nummeriert, mit Modulpräfix)

- **Archivzählung mit zwei Regeln** (`generate_dashboard.archive_summary` vs `board.archived_counts`,
  166/167/168 gemessen): schließt sich von selbst, wenn das Dashboard nicht mehr zählt; bleibt es dabei, ist
  es **H126** mit der Messung aus `parity.md`.
- **Zwei Leser der offenen Anfragen** (`report.generate_session_brief`, `board`) mit kopierter Ablaufregel,
  bis Seam (a) landet — **H127**, begrenzt durch den Paritätstest oben.
- **Eine Handänderung an einem Diagramm sieht zwischen zwei Zustandsschreibvorgängen niemand**
  (`plan_diagram.is_pristine` läuft nur in Tests; kein Gate, kein Validator-Aufruf) — **H128**, begrenzt
  durch: `generated/` ist ignoriert und die nächste Schreibung überschreibt; Seam-Vorschlag an C:
  `report.validate_state` meldet `stale`/`hand-edited` als Warnung.

## 7. Seams außerhalb dieses Stroms (melden, nicht schreiben)

| Empfänger | Zeile(n) | Schiedsrichter-Test |
|---|---|---|
| C (`state.py`) | Diagramm-Schreibung in `_write_board` (verbatim in `05-diagrams.md`); `now` an `board.render` | `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` |
| C (`cli.py`) | `generate-index` druckt auch die zwei Diagrammpfade | `test_board.test_the_documented_command_writes_and_names_both_artefacts` (heute „both", dann „all") |
| C (`approvals.py`) | `open_requests(state, now)` für Brief und Board | der Paritätstest in §5 |
| C (`backlog_types.py`, nur Option A) | die Zeilen aus `mst-decision-proposal.md` | dort je Zeile genannt |
| C/Merge (Hooks, nur Option A) | `guard_no_adhoc.ITEM_TYPES` + `"mst"` in drei Kits | `test_hooks.test_no_adhoc_covers_every_item_type` |
| D (nur Option A) | Typtabelle der drei Verfassungen: eine Zeile `MST` | Strom D's Textprüfung |
| B (geteilt) | `tools/test_hooks.py` Dashboard-Abschnitt | Merge-Runde |
| Merge | `templates/project_memory/milestones/active/.gitkeep` in drei Kits (nur Option A) | `test_board.test_each_kit_renders_the_types_its_own_template_ships` |

## 8. Suiten je Runde (DEC-0050)

Betroffen: `tools/test_board.py` (voll), `tools/test_plan_diagram.py` (voll), `tools/test_hooks.py -k
dashboard` plus voll einmal vor dem Stempel, `tools/test_kitupdate.py` (Template-Hash), `tools/validate.py`,
`python -B -m pytest .claude/hooks/test_gates.py -q` nicht (kein Gate berührt). Die volle Suite gehört der
Merge-Runde.
