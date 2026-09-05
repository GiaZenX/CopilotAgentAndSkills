# TSK-0122 — Strom G4-2 „Kernel contracts" (PR-0005), Stromprotokoll

Arbeitsbaum `C:/Offline Repos/v2-testbed/_worktrees/g4-kernel` (Branch `g4/kernel`, ab
`feat/harness-v2` bei `75a00d1`). Scratch ausschließlich unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0122/`. Kein Commit, kein Push, keine Installation.

Entscheidungsgrundlage: **DEC-0071** (BUG-0090, Option A), **DEC-0072** (FR-0085, Option A),
**DEC-0073** (FR-0087, Option A mit Teilfrage 3a) — vom Nutzer am 2026-09-04 auf die drei Vorlagen
`staging/TSK-0122/dec-*.json` entschieden.

---

## 0. Vorgefunden, und was die Runde unterbrochen hat

Vier Host-Abstürze des Nutzerrechners haben die Runde viermal abgeschnitten. Die Ursache ist
gemessen und lag **nicht** in diesem Strom: das Lastrig von G4-4 hat alle 16 logischen Kerne
belegt, Windows protokollierte harte Abschaltungen zwei bis drei Minuten nach dessen letzten beiden
Starts.

Die eine Stelle, die in diesem Strom nach einem Hänger aussah — der Suitenlauf über
`tools/test_approvals_dispatch.py` —, ist danach mit hartem Zeitdeckel nachgemessen worden:
**83,7 s für 186 Tests, langsamster Einzeltest 4,36 s**. Es gab hier weder einen Warteloop noch
einen Lauf ohne Ende; der 600-s-Deckel des Werkzeugs war der Deckel des Werkzeugs. Konsequenz
trotzdem gezogen: seither trägt **jeder** Lauf dieses Stroms ein `timeout`, lange Läufe laufen im
Hintergrund mit synchronem Warten auf eine Logdatei, und Patch und Protokoll werden nach jedem
Kriterium neu geschrieben.

Der Rot-zuerst-Rig (`_round-scratch/TSK-0122/redfirst.py`) verweigert den Lauf außerhalb seines
eigenen Rundenverzeichnisses (`_here()` prüft Verzeichnisnamen **und** den `_round-scratch`-Anteil
und beendet sich sonst mit `SystemExit`) und schreibt ausschließlich binär
(`io.open(..., "rb"/"wb")`, `replace()` arbeitet auf Bytes), weil der CRLF-Vorfall aus Generation 3
genau den Kernel getroffen hat. Kopien entstehen ohne `.git`.

---

## 1. Nahttabelle

| Naht | Wer | Bekommen / erwartet am Merge |
|---|---|---|
| `.claude/hooks/test_gates.py` | G4-1 (Gate-5-Tests), G4-4 (Timing-Test), hier die Löcherlisten-Prüfer | **gemessen als AST-Vergleich gegen ein reines 75a00d1** (nicht geschätzt, und in Prüfrunde 2 unabhängig nachgerechnet): **18 Definitionen entfernt, 10 neu, 5 geändert.** ENTFERNT sind die Text-Leser der alten Liste (`_hole_section`, `_hole_entries`, `_hole_rows`, `_stated_verdict`, `_hole_citation_sources`, `_prose_of`, `_fence_marker`, die Konstante `OVER_REFUSAL_ENTRY` und die alten Prüfer). **`_over_refusal` steht in BEIDEN Ständen unverändert** und gehört in keine der drei Listen — es hier unter „entfernt“ zu führen war Prüfbefund N4. NEU sind `_kernel`, `_holes`, `_hole_prose`, `OVER_REFUSAL_HOLE` und die item-lesenden Prüfer. **GEÄNDERT sind genau fünf, und das sind die Stellen, die G4-1 und G4-4 angehen:** `_anchors`, `test_every_reference_to_a_measurement_leads_to_one`, `test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`, `test_every_cell_a_closed_hole_names_is_one_the_table_carries`, `test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`. **Byte-identisch geblieben** sind `TABLE_TEST`, `TILDE_TEST`, `CELLS_RX` und `SUBJECTS_RX`; `_assert_it_is_the_same_hole` gehört **nicht** in diese Datei, sondern in `tools/migrate_holes.py`. **Kein Gate-5-Test und kein Timing-Test berührt.** |
| `tools/**` | alle vier Ströme | **erwartet**: `tools/conftest.py` trägt jetzt `satisfy_the_architect_step`; wer in einer Fixture eine Lease mintet, ruft sie. `tools/test_approvals_dispatch.py` trägt `a_scope_of_its_own(state)` — wer zwei Aufträge gleichzeitig least, braucht sie |
| `docs/POST_V2_WISHLIST.md` | dieser Strom migriert sie | **erwartet**: die anderen drei legen ihre neuen Löcher im **heutigen** Format ab (`### H<n>`-Überschrift plus dreispaltige Zusammenfassungszeile). Wie das im Merge zusammenkommt: Abschnitt 7 |
| `team-kits/*/VERSION` | alle | vorläufig **`2026.09.05-5`**, am Merge neu |
| Verfassungs-/PM-Skill-Sätze | **G4-3, wörtlich** | Abschnitt 8 |
| `team-kits/*/hooks/gate_dispatch.py` | dieser Strom **nicht angefasst** | DEC-0072 entschied den Kernel; **keine Spiegelung nötig**, und keine gespiegelte Datei wurde geändert |
| `team-kits/kernel/kitupdate.py` | G4-4 (BUG-0088) | hier verboten, nicht angefasst |
| `team-kits/kernel/migrate.py` | dieser Strom, eine Zeile | Abschnitt 2, AC-4 (Folgebefund) |

Reservierte Löchernummern dieses Stroms: **H154, H155, H156** — mehr nicht, und alle drei sind im
Dokument im heutigen Format abgelegt.

---

## 2. Je Kriterium: was gebaut wurde, die Messzeile, der rote Test

> Nachgearbeitet in zwei Prüfrunden. Was in Runde 1 und 2 gefunden und geschlossen wurde,
> steht je Befund mit Messzeile und rotem Test in `rework-round-1.md` und
> `rework-round-2.md`; die Zahlen unten sind auf den letzten Stand nachgemessen.

### AC-1 (BUG-0090, DEC-0071) — ehrliche Evidenz für einen BUG

**Gebaut.** `report.DELIVERY_QUESTION` / `report.CONFIRMATION_QUESTION` als geschlossene Vokabel;
`report._delivery_evidence` und `report.qa_verdicts` nehmen die **Frage** als benanntes Argument
(Vorgabe: die Lieferfrage, also für jeden bestehenden Aufrufer unverändert), und nur die
Lieferfrage lässt einen bestandenen Teillauf fallen. `state._assert_confirmed` ist der einzige
Aufrufer, der die zweite Frage stellt. Eine dritte Frage wird mit `ValueError` verweigert.

**Vorher / nachher, gemessen** (`_round-scratch/TSK-0122/m1_bug0090.py`, echte Kernel-Aufrufe,
Zustandsverzeichnis außerhalb des Repos, Stand 75a00d1):

- vorher: `qa_verdicts: {}` und `RESULT: transition REFUSED -> BUG-0001 FIXED -> VERIFIED needs a
  'test' Evidence that PASSES and covers BUG-0001; there is none`; derselbe Lauf ohne
  `run_command`/`run_scope`: `RESULT 2: transition WALKED -> VERIFIED`.
- nachher: `RESULT: transition WALKED -> VERIFIED`, und `qa_verdicts` (Lieferfrage) liefert
  weiterhin `{}` — der Merge-Leser ist buchstäblich unverändert.

**Rot ohne den Fix:** `tools/test_state.py::test_a_declared_regression_run_confirms_the_bug_it_names`
(gemessen: grün rc 0 / mit wiederhergestelltem Defekt rc 1).
Der Merge-Stolperdraht
`tools/test_report.py::test_a_pass_from_a_partial_run_is_not_merge_evidence_and_a_fail_still_is`
bleibt grün; die Gegenrichtung hält
`tools/test_report.py::test_a_selection_that_passes_confirms_the_item_it_names_and_ships_nothing`.

### AC-2 (BUG-0091, DEC-0066) — kein Arbeitsauftrag unter einem Posteingangs-Item

**Gebaut.** `backlog_types.TRIAGE_RESULT_LINK` + `is_inbox_type` als **Eigenschaft** („ein Typ,
dessen Lebenslauf damit enden kann, das Item zu benennen, das er GEWORDEN ist"), gelesen von zwei
Stellen: `report._check_fr_result_link` nimmt seine Pflicht daher (statt `"FR"` fest zu
verdrahten), und `dispatch._assert_the_origins_are_not_inbox_items` verweigert bei `create_task`
über **beide** Elternfelder (aus `PARENT_FIELDS`, nicht aus einer zweiten Liste). Dazu
`report.tasks_under_an_inbox_item` (Zähler über den ganzen Speicher) und
`report._check_tasks_under_an_inbox_item` (Warnung, nur für **aktive** Aufträge).

**Gemessen** (`m2_fr_roots.py`, `m2b_origins.py`, `m2c_tsk_origins.py`):

- 120 TSK-Dateien im Repo, davon **21 mit `product_requirement = FR-…`** und 35 mit
  `derives_from = FR-…`; **alle 21 sind archiviert**, aktive gibt es null. Deshalb zählt der Zähler
  über den ganzen Speicher und die Validator-Warnung nur über die aktiven.
- Der Grund für die Verweigerung **bei der Erstellung** ist gemessen und keine Geschmacksfrage:
  `create_task` mit einem FR gab rc 0 und ein DRAFT-Item; `create_pending_request(state, "scope",
  FR-0001)` verweigert („this type carries no user approval"), weil `FR` in keiner Zeile von
  `APPROVAL_TRANSITIONS` steht; `create_lease` verweigert dann mit „no user approval authorises
  dispatching TSK-0001". Ein solcher Auftrag ist **von Bauart nicht dispatchbar**, und seine Felder
  sind außerhalb DRAFT eingefroren.
- Verweigerungstext nachher: „`product_requirement FR-0001 is an inbox item, not a goal` … Remedy:
  `transition FR-0001 TRIAGED`, then `transition FR-0001 CONVERTED` or `transition FR-0001 MERGED`
  with `resulting_item` = the goal it became".

**Rot ohne den Fix:**
`tools/test_approvals_dispatch.py::test_a_work_order_under_an_inbox_item_is_refused_at_creation`
und
`tools/test_report.py::test_the_inbox_counter_sees_an_archived_work_order_and_the_validator_only_a_live_one`
(beide gemessen grün rc 0 / mit Defekt rc 1).

### AC-3 (FR-0085, DEC-0072) — SR-Pflicht nach Zielklasse, am Dispatch

**Gebaut.** `dispatch.architect_step_owed` (das Prädikat),
`dispatch._assert_the_architect_step_happened_locked` (die Verweigerung), gerufen aus
`create_lease` **und** `validate_dispatch` — so trägt auch eine Lease, die vor der Regel entstand,
keinen Spawn daran vorbei. `dispatch.SR_EXEMPT_CLASSES = {small, technical_enabler}`.

**Die Richtung ist gemessen begründet.** `class` hat in diesem Kernel **keine Vokabel** — die
ausgelieferte Suite allein erfasst Wurzelziele mit `feature`, `normal`, `research`, `exploratory`
und `technical_enabler`, und kein Schema schränkt den Wert ein. Eine Regel als „class in (normal,
large)" hätte die Pflicht für jeden nicht bedachten Wert **übersprungen**. Deshalb ist die
**Ausnahme** die geschlossene Menge. Der Preis steht als **H155** in der Löcherliste.

**Vorher / nachher, gemessen** (`m3_sr_duty.py`, gescaffoldete Pilotzustände außerhalb des Repos):

- vorher: `class=normal SRs=0 -> lease GRANTED`, ebenso `large` und `small` (drei von drei rc 0).
- nachher: `class=normal SRs=0 -> REFUSED: TSK-0001 hangs from PR-0001 (class 'normal'), and no SR
  in status ACCEPTED hangs from that goal …`; `small` und `technical_enabler` werden nicht gefragt;
  ein Auftrag, der von einem BUG ableitet, wird nicht gefragt.

**Was es kostete, gemessen statt vermutet:** die Pflicht traf **99 Tests** der ausgelieferten
Suite. Repariert wurde sie **nicht durch Aufweichen**, sondern in den Fixtures, die eine Lease
minten — `conftest.satisfy_the_architect_step` fragt dasselbe Kernel-Prädikat, das die Verweigerung
fragt, damit keine Fixture an einer Pflicht vorbeigeht, an der die Produktion nicht vorbeikommt.

**Rot ohne den Fix:**
`tools/test_approvals_dispatch.py::test_a_goal_of_an_unknown_class_is_asked_for_the_architect_step`
(grün rc 0 / mit Defekt rc 1); die Gegenrichtung hält
`tools/test_approvals_dispatch.py::test_a_small_goal_is_not_asked_and_neither_is_a_bugfix_order`.

### AC-4 (FR-0087, DEC-0073) — Löcher als typisierte Items

**Gebaut, Kernelseite.**

- `AUTOMATA["BUG"]` bekommt den Endzustand `ACCEPTED_EXCEPTION`, erreichbar **nur** aus `TRIAGED`,
  ohne ausgehende Kante.
- `approvals.HOLE_EXCEPTION_KIND` (`hole_exception`) in `APR_KINDS` und
  `APPROVAL_TRANSITIONS[("BUG", hole_exception)] = ("TRIAGED", "ACCEPTED_EXCEPTION")`; das Manifest
  ist item-abgeleitet und hasht Titel, `observed`, `expected`, `severity`, `limits` und
  `hole_number` — was der Nutzer unterschreibt, ist die **beschriebene** Lücke.
- `backlog_types.STATUS_DEPENDENT_FIELDS` als Karte (statt eines Zweigs je Fall), gelesen vom
  Validator; `HOLE_LIMIT_FIELD` ist genau in `ACCEPTED_EXCEPTION` Pflicht — enger, weil eine
  breitere Pflicht jeden gespeicherten BUG-Datensatz am Tag der Regel zu einem Validator-Fehler
  machte, den kein Kommando repariert (91 waren es an 75a00d1 — die Zahl gehört in diesen
  Bericht und nicht in den Kommentar, siehe F14).
- `HOLE_REQUIRED_FIELDS` + `required_fields_of`: ein Loch schuldet Titel, Wurzel, `observed` und
  `severity` — nicht `expected`/`repro`/`acceptance_criteria`, weil ein Loch ein Defekt ist, den
  niemand schließt. **Gemessen** über die Einträge des ausgelieferten Dokuments (heute 143):
  jeder nennt ein Urteil, 121 einen Mechanismus, 85 eine gemessene Kette — ein Vertrag, der von
  jedem ein Repro verlangt, wäre nur durch die fehlenden zu erfüllen, also durch Erfindung.
  **Wo dieser engere Vertrag gilt**, steht im Kommentar an `HOLE_REQUIRED_FIELDS`: bei
  `validate_state` über gespeicherte Items und an der Migrationstür; `capture --hole` verlangt
  weiterhin den vollen `BUG`-Vertrag (Prüfbefund F10).
- `state.capture(..., hole=True)` vergibt `hole_number` per Max-Scan über den ganzen Speicher; ein
  Körper, der das Feld mitbringt, wird verweigert.
- `state.capture_migrated_hole` — die Tür aus DEC-0073 (3a), mit vier gebauten Bolzen
  (nur mit `hole_number`; nur ein Status des Automaten; terminal ⇒ Archiv, sonst `active/`; eine
  vorhandene Nummer wird zurückgegeben statt überschrieben). Was sie weitet, steht als **H154** mit
  ihrer Begrenzung.

**Gebaut, Werkzeugseite.** `tools/migrate_holes.py`: liest Abschnitt 12, schreibt je Eintrag ein
dünnes Item **durch den Kernel** und die volle Prosa nach `docs/holes/H<n>.md`, und ersetzt den
Abschnitt durch einen **generierten** Zeigerindex. Kein Handschreiben in `project_memory` — das
Skript ruft ausschließlich `state.capture_migrated_hole`.

**Gebaut, Prüferseite.** Die Löcherlisten-Tests in `.claude/hooks/test_gates.py` lesen jetzt
**Items** (geparst, über `state._iter_every_stored_item`):
`test_every_hole_states_a_verdict_and_an_unclosed_one_names_its_limit` (das Urteil IST der Status;
„ungeschlossen" ist aus dem Automaten abgeleitet, nicht aus Wörtern),
`test_every_test_a_hole_names_is_one_that_exists` (liest `regression_tests` statt Markdown-Spans),
`test_the_hole_index_in_the_document_is_the_one_the_items_generate` (regeneriert und vergleicht,
kein zweiter Digest). Die drei Tests, die auf Zahlen in der Prosa stehen (Kreuztabelle, Tilde-Menge)
lesen die Prosadatei, die das Item über `source` nennt. Dazu zwei Anpassungen desselben Blocks:
`_anchors` liest H-Nummern jetzt **auch** aus dem generierten Index (sonst löst kein
`… H33`-Zitat eines Hook-Docstrings mehr auf), und
`test_every_reference_to_a_measurement_leads_to_one` liest die Prosadateien statt der Einträge.

**Gemessen, Ende zu Ende gegen eine Kopie des Repos außerhalb davon** (`m7_full_ac4.py`,
Log `_round-scratch/TSK-0122/m7.log`, letzter Lauf nach der Nacharbeit zu Prüfrunde 2):

```
APPLY rc=0 | 143 written, 0 already in the store, 143 prose files
prose files: 143
document lines: 2441 nach der Migration, 9313 davor (gelesen, nicht getippt)
SECOND RUN rc=0 | 0 written, 0 already in the store, 0 prose files
document byte-identical after the second run: True
prose files after the second run: 143
VALIDATE rc=0 | Counter({'warning': 66}) / errors: []
GATES rc=0 | 7 passed
```

Die Validator-Zahl ist eine Vorher/Nachher-Messung: **derselbe Zustand ohne Migration ergibt
ebenfalls 0 Fehler und 66 Warnungen** — die 143 Items fügen keinen einzigen Befund hinzu. Die
genauen Laufzeiten des letzten Laufs stehen in `m7.log`; sie schwanken mit der Last des Hosts und
werden hier nicht ein zweites Mal festgeschrieben.

**Rot ohne den Fix:**
`tools/test_state.py::test_the_kernel_hands_out_the_hole_number_and_never_the_caller` und
`tools/test_backlog_types.py::test_the_hole_exception_ending_is_reachable_only_from_a_judged_hole`
(beide grün rc 0 / mit Defekt rc 1). Dazu ohne Mutationsnachweis, weil sie neue Gegenstände sind:
`tools/test_state.py::test_the_migration_door_writes_a_hole_and_refuses_everything_else`,
die sechs Tests in `tools/test_migrate_holes.py` und die sieben Gate-Knoten.

**Drei Folgebefunde, die erst diese Erweiterung sichtbar gemacht hat** — alle drei sind echte
Fehler in bestehenden Ableitungen, nicht in meinem neuen Code:

1. `approvals.approved_statuses` sammelte nur Freigabeziele, die auf der **Chain** liegen. Die
   erste Freigabekante mit einem Off-Chain-Ziel ließ die Funktion „keine Freigabe hat das gesetzt"
   über genau den Status sagen, den der Nutzer eben unterschrieben hatte. Gefunden von
   `test_a_status_an_approval_commits_is_an_approved_status`.
2. `test_the_gated_edges_are_exactly_the_ones_the_mint_walks` trug die Regel „eine terminale Kante
   ist nie gegated" als **Aufzählung** mit einem angeflickten `target != "ACCEPTED"`. Ersetzt durch
   die Eigenschaft: ein Terminal, das **mehrere** Statuus erreichen, ist ein Abbruch; ein Terminal
   mit genau einer eingehenden Kante ist ein Ergebnis, und welche Ergebnis-Terminals gegated sind,
   wird jetzt als Menge in **beide** Richtungen gehalten.
3. `migrate.item_size` misst eine Körpergröße mit `widest_status()` als Platzhalter. Sobald
   `widest_status()` einen freigabegebundenen Status zurückgab, las der AST-Prüfer diese **Messung**
   als Statusschreiber. Der Platzhalter ist jetzt eine Länge (`"x" * len(...)`), und der Prüfer
   lernt die Form „String mal Zahl" als „kann keinen Status erzeugen" — auf die **Form** gebunden,
   nicht auf einen Funktionsnamen.

### AC-5 (C-2/C-3) — Leases für parallele Spezialisten

**Gebaut.** `dispatch._assert_no_running_lease_owns_the_same_file_locked` in `create_lease`:
Prädikat ist `kernel.scopes` (also der ausgelieferte `gate_write_scope._matches` mit beidseitiger
Faltung), die deklarierte Naht wird von `scopes.overlaps` abgezogen, verglichen wird **nur** gegen
Leases, die noch laufen. Kostet nichts, wenn nichts anderes läuft: der Gate-Import und der
`git ls-files`-Aufruf liegen hinter dem frühen Rücksprung. Dazu `dispatch.WORKTREE_FIELD` auf
**jeder** Lease (`_lease_worktree`: der Aufrufer nennt den Baum, sonst der Baum des
Zustandsverzeichnisses) und `--worktree` an `harness.py dispatch`.

**D's zwei Tests sind auf den neuen Vertrag umgeschrieben**, in diesem Strom:

- `test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` →
  `test_the_second_lease_is_refused_when_the_scopes_overlap` (verlangt, dass die Verweigerung den
  geteilten Pfad **nennt**, und dass der abgewiesene Auftrag auf READY stehen bleibt);
- `test_the_lease_carries_no_tree_of_its_own` →
  `test_the_lease_carries_the_tree_it_was_granted_for` (beide Enden: Vorgabe = Baum des
  Zustands, benannter Baum = der genannte);
- neu dazu `test_a_seam_both_orders_declare_lets_the_second_lease_through`, damit die Verweigerung
  nicht dadurch erfüllbar ist, dass sie alles verweigert.

**Gemessen** über einen echten git-Baum unter `tmp_path` mit Aufträgen, die der Kernel erfasst hat;
Verweigerungstext: „TSK-0002 and TSK-0001 — which holds a running lease — both own src/a.py …".
Lease-Schlüssel vorher: `agent_id, created, created_epoch, nonce, root_revision, task_id, ttl`;
nachher zusätzlich `worktree`.

**Rot ohne den Fix:**
`tools/test_parallel_streams.py::test_the_second_lease_is_refused_when_the_scopes_overlap` und
`tools/test_parallel_streams.py::test_the_lease_carries_the_tree_it_was_granted_for`
(beide grün rc 0 / mit Defekt rc 1).

---

## 3. Rot-zuerst, gemessen (Rig `redfirst_all.py`, Log `redfirst.log`)

Eine Kopie des Arbeitsbaums **ohne `.git`** unter `_round-scratch/TSK-0122/rig/copy-redfirst`, acht
Mutationen nacheinander, jede vor der nächsten zurückgesetzt, die Kopie am Ende verworfen.

| Kriterium | Test | ohne Mutation | mit wiederhergestelltem Defekt |
|---|---|---|---|
| AC-1 | `test_a_declared_regression_run_confirms_the_bug_it_names` | rc 0 | **rc 1** |
| AC-2 | `test_a_work_order_under_an_inbox_item_is_refused_at_creation` | rc 0 | **rc 1** |
| AC-2 | `test_the_inbox_counter_sees_an_archived_work_order_and_the_validator_only_a_live_one` | rc 0 | **rc 1** |
| AC-3 | `test_a_goal_of_an_unknown_class_is_asked_for_the_architect_step` | rc 0 | **rc 1** |
| AC-4 | `test_the_kernel_hands_out_the_hole_number_and_never_the_caller` | rc 0 | **rc 1** |
| AC-4 | `test_the_hole_exception_ending_is_reachable_only_from_a_judged_hole` | rc 0 | **rc 1** |
| AC-5 | `test_the_second_lease_is_refused_when_the_scopes_overlap` | rc 0 | **rc 1** |
| AC-5 | `test_the_lease_carries_the_tree_it_was_granted_for` | rc 0 | **rc 1** |

---

## 4. Was bewusst nicht geschlossen, sondern benannt wurde

- **H154** — die Migrationstür schreibt einen Endzustand (`VERIFIED` darunter) ohne die
  bestätigende Evidenz und ohne die Freigabe, die davor steht. Vier gebaute Bolzen als Begrenzung;
  der Datensatz landet im Archivbaum, wo `validate_state` nicht urteilt und kein Gate eine
  Autorisierung liest.
- **H155** — `class` ist Freitext, also hängt die SR-Pflicht an einer Ausnahmeliste. Ein Tippfehler
  kostet eine Architektenrunde (Über-Verweigerung, Abhilfe: ein `capture SR` plus `transition
  ACCEPTED`). Nicht begrenzt: dass das Feld Freitext bleibt.
- **H156** — die Überlappungsverweigerung sieht nur **laufende** Leases; zwei READY-Aufträge, die
  nie gleichzeitig geleast werden, kollidieren im Merge trotzdem. Begrenzt durch `check-scopes` vor
  dem Schnitt (DEC-0070 (1)); die zwei geerbten Grenzen des Prädikats sind H135 und H143.
- **Der eine schreibende Lauf gegen den kanonischen Zustand ist NICHT erfolgt** und konnte es
  nicht: `project_memory/**` steht im `forbidden_scope` dieses Auftrags, und Gate 1 verweigert den
  Schreibzugriff ohnehin jedem Aufrufer aus einer Sitzung heraus. Er ist eine Merge-Handlung und
  steht als Kommando in Abschnitt 7. **Solange er nicht gelaufen ist, sind die sieben umgestellten
  Gate-Knoten im Hauptrepo rot** — sie lesen einen leeren Bestand, und jeder von ihnen sagt das
  auch (der siebte tat es bis zur Nacharbeit nicht: er lief eine leere Schleife und blieb grün,
  Prüfbefund F6). Gemessen sind sie gegen die migrierte Kopie: **7 von 7 grün**. Umstellung und
  Lauf gehören in **denselben** Merge.
- **Nicht gemessen:** die volle Suite. DEC-0050 macht sie zum Lieferkriterium des Merges; dieser
  Strom hat nur die lesenden Suiten gefahren (Abschnitt 6).
- **Nicht gebaut:** die Board-Lane für offene Löcher (`kernel/board.py` gehört einem anderen
  Strom); PR-0005 führt sie unter `out_of_scope`.

---

## 5. Der verworfene Weg (FR-0084-Form)

Für AC-3 verworfen: die SR-Pflicht im Haken `gate_dispatch.py` der drei Kits statt im Kernel — sein
PreToolUse läuft am Spawn und ruft `validate_dispatch`, die Lease ist dann bereits gemintet und die
TSK steht auf `LEASED`, die Verweigerung käme also **nach** der Zustandsänderung; außerdem ist der
Haken dreifach gespiegelt und in diesem Repo, wo die beanstandete Praxis gemessen wurde, gar nicht
geladen.

---

## 6. Suitenläufe (nur die lesenden, DEC-0050)

| Lauf | Ergebnis |
|---|---|
| `tools/test_state.py test_backlog_types.py test_migrate_holes.py test_parallel_scopes.py test_parallel_streams.py test_report.py test_kernel.py` (Abschlusslauf nach Nacharbeit 3) | **417 passed, 88 s** |
| `tools/test_approvals_dispatch.py` | **194 passed, 82 s** |
| `.claude/hooks/test_gates.py -k "hole or holes or _hole or reference_to_a_measurement"` **gegen die migrierte Kopie** | **7 passed, 152 s** |
| `.claude/hooks/test_gates.py -k "claims_in_its_own_prose or names_only_code_that_exists"` | **2 passed** — nach einer Korrektur: ein Docstring dieses Blocks zitierte noch den alten Namen `test_every_test_the_hole_list_names_is_one_that_exists`, über zwei Zeilen umbrochen, und der Selbstprüfer des Apparats hat ihn gefunden |
| `.claude/hooks/test_gates.py -k "hole or holes or _hole or reference_to_a_measurement"` **gegen die migrierte Kopie** | **7 von 7 grün** (6 + 1 nach der Korrektur, 313,4 s bzw. 229,0 s) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed (nach `bump_kit_version.py`) |

Nicht gefahren: die volle Gate-Suite, `tools/test_hooks.py` vollständig, und die volle Suite —
alle drei gehören dem Merge.

---

## 7. Wie die Löcher der anderen drei Ströme ankommen

Die anderen Ströme legen ihre Löcher im **heutigen** Format ab: eine `### H<n>`-Überschrift in
Abschnitt 12 plus eine dreispaltige Zusammenfassungszeile. `tools/migrate_holes.py` liest genau
dieses Format und **übernimmt die im Eintrag stehende Nummer**, statt eine neue zu vergeben — die
Reservierungen H151–H153 und H157–H162 bleiben damit exakt die Nummern, die in den Items der Ströme
stehen. Der Lauf verträgt einen Abschnitt, der bereits ein Index ist **und** neue Einträge trägt;
gemessen von
`tools/test_migrate_holes.py::test_an_entry_that_arrives_later_is_migrated_with_the_number_it_was_reserved_under`.

**Das Merge-Kommando, einmal, aus der Repo-Wurzel — und aus einer Shell AUSSERHALB von Claude
Code:**

```
PYTHONPATH=team-kits python -B tools/migrate_holes.py --root project_memory --related-pr PR-0003 --apply
```

Warum außerhalb: Gate 1 (`gate_lead_write_scope.py`) verweigert **jedem** Aufrufer den
Werkzeug-Schreibzugriff auf `project_memory/` — gemessen vom Prüfer, dieselbe Zeile aus einer
Sitzung heraus ist rc 2. Das ist die Regel aus CLAUDE.md und kein Defekt dieses Stroms; sie ist
hier genannt, weil bis zu diesem Lauf **alle sieben** Gate-Knoten rot sind — seit der
F6-Nacharbeit auch der siebte, der bis dahin eine leere Schleife lief und grün blieb.

Danach sind die sieben Gate-Knoten grün (gemessen gegen die migrierte Kopie: **7 passed**). Ein
zweiter Lauf schreibt nichts (gemessen: 1,79 s, rc 0, Dokument byte-identisch), also ist er
gefahrlos wiederholbar.

**Ein Loch, das NACH der Migration erfasst wird**, kommt über die Kommandofläche
(`capture BUG --hole`, der Kernel vergibt die Nummer) in den Speicher; der Zeigerindex zieht mit
`python tools/migrate_holes.py --root project_memory --reindex` nach — ebenfalls aus einer Shell
außerhalb von Claude Code.

---

## 8. Nahtzeilen wörtlich für G4-3 (Verfassung / PM-Skill)

Drei Sätze in den Kit-Texten sind durch diese Runde **falsch geworden** und gehören G4-3. Sie
tragen den neuen Testnamen, weil das tote Zitat sonst überlebt: der alte Name
`test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` steht noch in **fünf** Dateien —
`team-kits/{dev,office,research}-team/constitution/AGENTS.md` und
`team-kits/{dev,research}-team/skills/parallel-streams/SKILL.md` — und der dev-Skill sagt dort
„If that test ever goes red, a refusal has been built and this paragraph is the one to correct":
der Test wurde nicht rot, er wurde **umbenannt**, der Stolperdraht hat nie ausgelöst.

1. Der Absatz, der sagt, dass die Disjunktheit paralleler Aufträge die Lesart des Leads ist und
   **nichts** ein überlappendes Paar verweigert. Neu, wörtlich:
   *„Der Kernel verweigert eine zweite Lease, wenn ein Auftrag eine Datei besitzt, die ein laufender
   Auftrag schon besitzt; die Naht, die beide Aufträge deklarieren, wird vorher abgezogen
   (`tools/test_parallel_streams.py::test_the_second_lease_is_refused_when_the_scopes_overlap` und
   `::test_a_seam_both_orders_declare_lets_the_second_lease_through`). Was er nicht sieht, sind
   zwei Aufträge, die nie gleichzeitig laufen — dafür gibt es `scripts/harness.py check-scopes` vor
   dem Schnitt."*
2. Der Satz, dass eine Lease keinen Baum kennt. Neu, wörtlich:
   *„Eine Lease trägt den Arbeitsbaum, für den sie erteilt wurde; ohne Angabe ist das der Baum, in
   dem das Zustandsverzeichnis liegt, und ein Pfad, an dem kein Verzeichnis liegt, wird verweigert
   (`tools/test_parallel_streams.py::test_the_lease_carries_the_tree_it_was_granted_for`,
   `::test_a_worktree_nobody_can_stand_in_is_refused`)."*
3. Der Architektenschritt. Neu, wörtlich:
   *„Ein Arbeitsauftrag unter einem Produktziel wird erst dispatcht, wenn unter demselben Ziel eine
   technische Anforderung (SR) im Status ACCEPTED hängt. Nicht gefragt werden Ziele der Klasse
   `small` und `technical_enabler` sowie Aufträge, deren Ursprung die Kriterien selbst trägt, gegen
   die sie gemessen werden — ein BUG, ein CR, ein EXP. Ein Auftrag, der von einer noch nicht
   angenommenen technischen Anforderung ableitet, wird gefragt wie jeder andere
   (`tools/test_approvals_dispatch.py::test_an_order_deriving_from_a_proposed_requirement_is_still_asked`,
   `::test_a_small_goal_is_not_asked_and_neither_is_a_bugfix_order`)."*

Dazu die Hierarchiezeile aus DEC-0066, die jetzt vom Kernel durchgesetzt wird:
*„Ein Arbeitsauftrag hängt an einem Ziel, einem BUG, einem CR oder einem EXP — nie an einem Wunsch
im Posteingang. Der Kernel verweigert das bei der Erstellung und nennt den Triage-Weg; ein Wunsch,
der schon triagiert ist, wird mit dem Item beantwortet, das er wurde
(`tools/test_approvals_dispatch.py::test_a_work_order_under_an_inbox_item_is_refused_at_creation`,
`::test_the_remedy_for_an_already_triaged_wish_names_what_it_became`)."*

---

## 9. Stempel, Dauer, Tokens

- **Vorläufiger Stempel:** `team-kits/{dev,office,research}-team/VERSION` = `2026.09.05-5`
  (nach dem ersten Kernel-Stand, nach den Folgebefunden und nach jeder der drei Nacharbeiten;
  der Merge stempelt neu).
- **Patch:** `_round-scratch/TSK-0122/stream-kernel.patch`, **4281 Zeilen / 268.876 Bytes**
  (gemessen), 0 CR-Bytes,
  18 Dateien, **ohne VERSION-Hunks** (das einzige Vorkommen von „VERSION" ist Prosa im Eintrag
  H148).
- **Nacharbeiten:** `project_memory/staging/TSK-0122/rework-round-1.md`, `rework-round-2.md`
  und `rework-round-3.md` — je Befund die Änderung, die Messzeile und der rote Test; die
  **(g)-Zeile des Stroms** und der Abschlussbefund N3' stehen am Ende von
  `rework-round-3.md`. Prüfurteil nach vier Runden: **PASS**.
- **Wandzeit:** vier Anläufe über zwei Kalendertage; die vier Host-Abstürze machen eine ehrliche
  Bruttozahl unmöglich. Gemessen ist die reine Rechenzeit der protokollierten Läufe: rund **55
  Minuten** (Migration 544 s + 313 s + 229 s, Suiten ~330 s, Rot-zuerst ~45 s, plus die
  Einzelmessungen).
- **Tokens (Umsetzer):** rund **530 k**, geschätzt aus dem Kontextverbrauch dieser Sitzung; die
  drei abgebrochenen Anläufe sind darin nicht enthalten.
