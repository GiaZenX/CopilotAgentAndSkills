# TSK-0122 (PR-0005, Strom G4-2) — Prüfbericht Runde 2 (Nacharbeit 1)

Rolle: `harness-verifier`. Read-only am Repo; alles gemessen in **frischen** Kopien unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0122/verify/`: `wt2` (Arbeitsbaum ohne `.git`),
`base2` (75a00d1), `mut2` (Mutationskopie), `mig2` (frisch migriert), `pilots_r2/**` (neue
gescaffoldete Piloten), `store75` (`project_memory` bei 75a00d1).

**URTEIL: FAIL — eine blockierende Neuöffnung.** Die vier blockierenden Befunde der Runde 1
(F1–F4) sind geschlossen und von mir einzeln nachgemessen. Der F2-Fix hat dabei ein neues Loch
derselben Klasse aufgemacht, die er schließen sollte: `capture --hole` prüft den Typ als
**Aufzählung von einem** und lässt jeden anderen durch — ein einziges rc-0-Kommando setzt einen
Gate-Knoten dauerhaft rot und schreibt einen `DEC` als Loch in das ausgelieferte Dokument.

| | Runde 1 | Runde 2 |
|---|---|---|
| AC-1 (BUG-0090/DEC-0071) | PASS | **PASS** |
| AC-2 (BUG-0091/DEC-0066) | PASS | **PASS** |
| AC-3 (FR-0085/DEC-0072) | FAIL | **PASS** |
| AC-4 (FR-0087/DEC-0073) | FAIL | **FAIL** — R1 |
| AC-5 (C-2/C-3) | PASS | **PASS** |
| Pflicht 6 (rot-zuerst / Eigenschaftsbehauptungen) | FAIL | **teilweise** — rot-zuerst PASS, zwei Behauptungen falsch (R3, R5) |
| Pflicht 7 (Nähte) | FAIL | **PASS mit Korrektur** (R5) |
| Pflicht 8 (Paket/Handover) | PASS | **PASS mit Korrektur** (R4) |

---

## Blockierend

### R1 — `capture --hole` nimmt jeden Typ außer `TSK`; ein `DEC` als Loch setzt den Gate-Prüfer dauerhaft rot

`team-kits/kernel/cli.py:1414`
```python
            if args.hole and args.item_type == "TSK":
                raise SystemExit("a work order is not a hole: ...")
```
Das ist die einzige Typprüfung. `team-kits/kernel/state.py:965` (`capture(..., hole: bool = False)`)
stempelt `hole_number` auf jeden Typ, den man ihr gibt.

Gemessen als **Prozess** (`verify/s2/ac4cli.py`, echter Kernel-CLI-Aufruf gegen einen Piloten):
```
6) --hole on an FR (unrelated type):
    (0, 'FR-0001 OPEN H3', '[hole] FR-0001 is H3. Regenerate the pointer index ...')
7) --hole on a DEC:
    (0, 'DEC-0001 VALID H4', '[hole] DEC-0001 is H4. ...')
store contents:
   BUG-0001 OPEN H1 a measured gap
   BUG-0002 OPEN H2 another gap
   DEC-0001 VALID H4 d
   FR-0001 OPEN H3 a wish
```

Die Kette läuft innerhalb einer Sitzung durch. Gegen die **migrierte** Kopie (`verify/s2/poison.py dec`):
```
capture DEC --hole -> 0 DEC-0071 VALID H157
judge over the poisoned store -> 1 1 failed in 1.55s
    E  AssertionError: H157 (DEC-0071) stands in 'VALID', which is no status of its type
index_rows now: 144 | last: ('H157', 'DEC-0071', 'VALID', 'a decision, filed as a hole')
```

Also: ein Kommando → `.claude/hooks/test_gates.py::test_every_hole_states_a_verdict_and_an_unclosed_one_names_its_limit`
rot, eine Löchernummer verbrannt, und `render_index` würde die Entscheidung als Loch in
`docs/POST_V2_WISHLIST.md` schreiben. Es gibt **kein** Kernel-Kommando, das ein Item löscht, und
Gate 1 verweigert jeden Werkzeug-Schreibzugriff auf `project_memory/` — die Reparatur braucht eine
Shell außerhalb von Claude Code. Ein `FR --hole` ist die leisere Variante: `OPEN` ist ein
`BUG`-Status, also fällt es erst über die fehlende `limits`-Pflicht auf.

Das ist Hausregel 1 in Reinform: eine Aufzählung mit **einem** Eintrag, wo die Definition
danebenliegt — ein Loch IST ein `BUG` (`backlog_types.py`, Block „WHAT A HOLE IS, AND WHY IT IS
NOT ITS OWN TYPE"; `AUTOMATA["BUG"]` trägt `ACCEPTED_EXCEPTION`; `STATUS_DEPENDENT_FIELDS` hat den
Schlüssel `("BUG", …)`; `state.capture_migrated_hole:1030` setzt `item_type = "BUG"` fest).

**Minimalfix:** die Verweigerung in `state.capture` statt in der CLI, abgeleitet statt aufgezählt —
`hole=True` ist nur für den Typ zulässig, für den der Loch-Vertrag geschrieben ist (aus
`STATUS_DEPENDENT_FIELDS`/`HOLE_EXCEPTION_STATUS` ableitbar), mit einem roten Test, der einen
zweiten Typ probiert. Danach kann die TSK-Sonderregel in `cli.py` weg.

---

## Nicht blockierend, aber aufzuschreiben

### R2 — `--reindex` gegen einen Speicher ohne Löcher leert den ausgelieferten Zeigerindex mit rc 0

`tools/migrate_holes.py:373`. Gemessen (`verify/s2/ac4f3.py`, Schritt 4) gegen die migrierte Kopie
mit 143 Löchern im Dokument und einem **leeren** Zustandsverzeichnis als `--root`:
```
4) --reindex against an empty store: (0, 'index rewritten from the store: 0 hole(s)', '')
   the section after it: ['## 12. Loecherliste der Repo-Gates -- GENERIERTER ZEIGERINDEX', ''] ... rows: 0
```
Ein vertippter `--root` kostet den Zeigerindex des ausgelieferten Dokuments, mit einer
Erfolgsmeldung. Begrenzt: die Items und `docs/holes/*.md` sind die Quelle, ein Lauf mit dem
richtigen `--root` stellt ihn wieder her, und die Datei liegt unter git. Das ist eine **neue**
Fläche, die es vor dem F3-Fix nicht gab.
**Minimalfix:** einen leeren Index nicht über einen nicht-leeren schreiben, außer mit einem
ausdrücklichen Flag.

### R3 — `_carries_its_own_criteria` fragt, ob der TYP die Kriterien tragen DARF, der Docstring sagt, der Ursprung BRINGE sie

`team-kits/kernel/dispatch.py:2001` / `:2036` („an origin excuses the architect step when it BRINGS
ITS OWN CRITERIA"). Gemessen (`verify/s2/ac3bug.py`):
```
acceptance_criteria filled | architect_step_owed=False | lease GRANTED | hook rc=0
acceptance_criteria EMPTY  | architect_step_owed=False | lease GRANTED | hook rc=0
```
Ein `BUG` mit `acceptance_criteria: []` (der Kernel lässt das zu — `acceptance_criteria` steht für
`BUG` nicht in `NONEMPTY_FIELDS`) befreit vom Architektenschritt, und der ausgelieferte Kit-Haken
lässt den Spawn mit rc 0 durch, obwohl `acceptance_refs: ["AC-1"]` dort gegen nichts auflöst.
Die Typ-Ebene ist als Entscheidung vertretbar („DERIVED FROM THE FIELD CONTRACT"); falsch ist der
Satz darüber.
**Minimalfix:** entweder den Satz („ein Ursprung, dessen Typ die Kriterien tragen KANN") oder eine
Wertprüfung — und wenn Typ-Ebene bleibt, ein Rest in H155/H156-Form.

### R4 — Zahlen im Protokoll, die zum ausgelieferten Paket nicht passen

Gemessen gegen `wt2`/`mig2`:

| Stelle | steht dort | gemessen |
|---|---|---|
| `stream-protocol.md:43` (Nahttabelle) | `2026.09.05-2` | **`2026.09.05-3`** in allen drei `VERSION` |
| `stream-protocol.md:187-192` | `140 written … 140 prose files` | **143 / 143** |
| `stream-protocol.md:189` | `document lines: 2438 (was 9199)` | **2441 (war 9289)** |
| `stream-protocol.md:156` | „über die 140 Einträge" | **143** Einträge im ausgelieferten Dokument |
| `stream-protocol.md:351` | „sechs der sieben Gate-Knoten rot" | **sieben von sieben** (der F6-Fix hat den siebten rot gemacht) |
| `rework-round-1.md:120` | „Dokument 9199 → 2441" | **9289 → 2441** (9199 ist der Stand 75a00d1, nicht das ausgelieferte Dokument) |

Die Zahlen sind aus dem CODE entfernt (F14, nachgemessen: „91 `BUG` records", „140 entries" ×2,
„names a BUG, a CR or an EXP" alle weg) — im Protokoll, wo sie hingehören, stehen aber noch die
Läufe der Runde 1. Der Merge liest das Protokoll.

### R5 — die Nahttabelle sagt „gemessen als AST-Vergleich", und die Aufschlüsselung stimmt nicht

`stream-protocol.md:39`. Die Kopfzahlen sind richtig — mein eigener AST-Vergleich
(`verify/s2/astdiff.py`, `base2` = pristine 75a00d1 gegen `wt2`) liefert **18 entfernt / 10 neu /
5 geändert**, und die fünf geänderten sind `_anchors`,
`test_every_cell_a_closed_hole_names_is_one_the_table_carries`,
`test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`,
`test_every_reference_to_a_measurement_leads_to_one`,
`test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`.

Falsch ist die Aufschlüsselung:
* „Neu sind … `_assert_it_is_the_same_hole`-Leser" — diese Funktion steht in
  `tools/migrate_holes.py`, **nicht** in `test_gates.py`; unter den 10 neuen Definitionen der Datei
  ist sie nicht.
* „plus die beiden Konstantenblöcke `OVER_REFUSAL_HOLE`/`TABLE_TEST` und `SUBJECTS_RX`/`TILDE_TEST`"
  unter *geändert*: `TABLE_TEST`, `SUBJECTS_RX`, `TILDE_TEST` und `CELLS_RX` sind gegen 75a00d1
  **byte-identisch** (gemessen), `OVER_REFUSAL_HOLE` ist **neu** (der alte hieß
  `OVER_REFUSAL_ENTRY` und ist entfernt).

G4-1 und G4-4 lösen ihre Konflikte in dieser Datei an dieser Tabelle auf.

### R6 — die eine Zahl der F14-Klasse, die stehen geblieben ist

`team-kits/kernel/dispatch.py:2075`: „This repository holds 9 SRs against 120 work orders."
Gemessen an 75a00d1 heute richtig (9 SR, 120 TSK) — aber es ist genau der Zähler, den die Hausregel
meint, und die vier Nachbarn derselben Klasse sind entfernt worden.

### R7 — der `--hole`-Hinweis nennt eine Flagge, die derselbe Fix optional gemacht hat

`team-kits/kernel/cli.py:1440` schreibt auf stderr
`... migrate_holes.py --root <state> --related-pr <goal> --reindex`, während
`tools/migrate_holes.py` seit dieser Runde sagt „`--related-pr` is required **unless** `--reindex`".
Gemessen: `--reindex` ohne `--related-pr` läuft rc 0. Der Hinweis verlangt etwas, das der Befehl
nicht braucht.

---

## Ausdrückliche Negativbefunde

### Gemessen und geschlossen (Runde-1-Befunde)

**F1 (blockierend, geschlossen).** `verify/s2/ac3.py`, frische Piloten:
```
== B normal/SR PROPOSED/derives=SR         -> REFUSED  (Runde 1: GRANTED)
== E normal/SR PROPOSED/derives=[PR,SR]    -> REFUSED  (Runde 1: GRANTED)
== C normal/SR ACCEPTED/derives=SR         -> GRANTED
== D normal/SR ACCEPTED/derives=root       -> GRANTED
== F derives=BUG mit Kriterien             -> GRANTED
== H small / I technical_enabler           -> GRANTED
== J unbekannte Klasse 'nomal'             -> REFUSED
== K ACCEPTED SR unter ANDERER Wurzel      -> REFUSED
== M product_requirement PR-B, derives_from SR unter PR-A -> REFUSED at creation
== N derives_from 'not-an-id'              -> REFUSED at creation
```
Die Menge, die befreit, ist gemessen `{PR, RQ, BUG, CR, EXP}`; `SR`, `PROC`, `HYP`, `MST`, `TSK`,
`FR` befreien nicht (`verify/s2/probe_types.py`). Reichweite über `store75`: `derives_from` nennt
SR 29 + PR 3 = **32 von 120** wie behauptet; `_carries_its_own_criteria` befreit insgesamt 50 der
120, gefragt würden 70 — die Differenz sind die 35 FR-Aufträge, die `create_task` jetzt ohnehin
bei der Erstellung verweigert.
**Als Prozess** (`verify/s2/ac3proc.py`), der UNBERÜHRTE, dreifach gespiegelte Kit-Haken
`dev-team/hooks/gate_dispatch.py` gegen eine Lease, deren Ziel nachträglich `normal` wurde:
`SR PROPOSED, derives SR` → **rc 2** mit dem Architektenschritt; `SR ACCEPTED, derives SR` → **rc 0**;
dasselbe für `derives root`. Kernel und Haken stimmen in allen vier Fällen überein.
(Mein direkter `validate_dispatch`-Aufruf hatte wie in Runde 1 die falsche Signatur — der Haken ist
hier der Schiedsrichter, und er geht durch `validate_dispatch`.)

**F2 (geschlossen, aber siehe R1).** `capture BUG --hole` → rc 0, `BUG-0001 OPEN H1`, Item im
Speicher, `--reindex`-Hinweis auf stderr. Zweiter Aufruf → `H2` (lückenlos). Ein Körper mit
`hole_number` → rc 1, mit **und** ohne `--hole`. `--hole` auf einer `TSK` → rc 1. `--help` trägt den
Vertrag.

**F3 (geschlossen).** `verify/s2/ac4f3.py`:
```
1) capture BUG --hole in the migrated store: (0, 'BUG-0235 OPEN H157', ...)
   index in step right after: False
   --reindex -> (0, 'index rewritten from the store: 144 hole(s)', '')
   index in step after --reindex: True
   --apply (die alte Abhilfe) wirkt jetzt ebenfalls -> (0, '0 written, ...')
2) handgeänderter Index, dann --reindex: (0, 'index rewritten ... 144 hole(s)') -> in step: True
3) --reindex ohne '## 12.'-Abschnitt: (1, '', "no '## 12.' section ... -- nothing to migrate")
5) --apply ohne --related-pr: (2, 'error: --related-pr is required unless --reindex is given')
```

**F4 (geschlossen).** `verify/s2/ac4f4.py`, gegen die migrierte Kopie:
```
A) H160 zum ersten Mal:                       (0, '1 written, 1 prose files')
B) gleiche Nummer, SELBER Titel, ANDERES observed: (1, ... "`observed` in the store reads ... the document reads ...")
C) gleiche Nummer, Titel nur in der GROSS-/KLEINSCHREIBUNG anders: (1, ...)
D) gleiche Nummer, Titel nur mit Leerzeichen am Ende:            (0, '0 written, 1 already ...')
E) identischer Eintrag (Wiederaufnahme):                          (0, '0 written, 1 already ...')
F) nach der Verweigerung: H160 -> BUG-0236, Prosadatei da, Speicher unverändert
```
Die Verweigerung schreibt das Dokument nicht um, also bleibt der neue Eintrag im Text stehen und
ein korrigierter Lauf nimmt ihn auf — der Wiederaufnahmefall bleibt wortlos.

**F6 (geschlossen, beide Richtungen).**
Über leerem Bestand (`wt2`): `7 failed, 483 deselected in 11.72s` — in Runde 1 waren es
`6 failed, 1 passed`. Über der migrierten Kopie: `7 passed in 165.42s`. Und mit einem zerstörten
Messzeiger (`docs/holes/H30.md`, `docs/reviews/…` → `docs/reviews/no-such-…`):
`test_every_reference_to_a_measurement_leads_to_one` **rc 1**, nach dem Rückbau rc 0.

**F5, F7, F8, F9, F14, F16, F17, F22** — gegen den laufenden Text geprüft
(`verify/s2/textcheck.py`): „21 such work orders" weg, „opens nothing" weg, „91 `BUG` records" weg,
„140 entries" (×2) weg, „names a BUG, a CR or an EXP" weg, der umbrochene Testname in `migrate.py`
weg; `report._check_triage_result_link` und `test_a_second_migration_run_writes_nothing` kommen
nirgends mehr vor; `DEC-0071` steht in `report.py`, `state.py` und `backlog_types.py`, `DEC-0072`
in `dispatch.py`. **Kein einziges `module::test`-Zitat in den 17 geänderten Python-Dateien bleibt
unaufgelöst** (AST-Index über alle definierten Namen).

**F10, F18, F19** — je ein eigener roter Test, von mir nachgestellt (Tabelle unten). F18 gemessen
am Text: eine bereits CONVERTED FR wird jetzt mit
„FR-0001 has already been triaged and became PR-0001 -- create the task under PR-0001" beantwortet.
F19: ein `--worktree`, an dem kein Verzeichnis liegt, wird verweigert; die TSK bleibt **READY** und
**keine Lease-Datei** wird geschrieben; ein Dateipfad wird ebenfalls verweigert; ein Pfad im Repo
und eine zweite Lease auf demselben Baum sind erlaubt und in H156 ausdrücklich als **kein** Rest
benannt.

**F11, F12, F13** — F11 siehe R5 (Kopfzahlen richtig, Aufschlüsselung falsch). F12: das tote Zitat
`test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` steht noch in genau den fünf
benannten Dateien (`{dev,office,research}-team/constitution/AGENTS.md`,
`{dev,research}-team/skills/parallel-streams/SKILL.md`) und ist als G4-3-Naht übergeben; **alle
acht Testnamen in den Ersatzsätzen von §8 lösen auf** (AST-Prüfung).
F13: **eigener Irrtum aus Runde 1 — ich hatte zu wörtlich gegrept.** Der Satz steht im
Assertionstext, über eine Zeile umbrochen: „from a shell OUTSIDE Claude \n Code, because gate 1
refuses every tool write into the state tree." F13 ist erledigt, und die dort genannte Abhilfe
(`--reindex`) habe ich als wirksam gemessen.

**F20, F21** — H154 trägt die zweite Restklasse mit gemessener Kette (unlesbares Loch-Item → Prüfer
rc 0) und Begrenzung; H156 die zu `--worktree`. Patch: `wc -l` = **3927**.

### Rot-zuerst, von mir selbst nachgestellt (`verify/s2/redfirst.py`, Kopie `mut2` ohne `.git`)

| Befund | Test | sauber | mutiert | zurück |
|---|---|---|---|---|
| F1 | `test_an_order_deriving_from_a_proposed_requirement_is_still_asked` | rc 0 | **rc 1** | rc 0 |
| F1 (eigene Mutation: `CRITERIA_FIELDS` um `contract` erweitert) | `test_only_an_origin_that_carries_criteria_excuses_the_architect_step` | rc 0 | **rc 1** | rc 0 |
| F2 | `test_a_new_hole_can_be_filed_from_the_command_surface` | rc 0 | **rc 1** | rc 0 |
| F3 | `test_a_hole_captured_after_the_migration_reaches_the_generated_index` | rc 0 | **rc 1** | rc 0 |
| F4 | `test_a_number_collision_at_the_merge_is_refused_not_skipped` | rc 0 | **rc 1** | rc 0 |
| F10 | `test_the_hole_contract_is_the_reading_side_and_capture_still_asks_the_full_one` | rc 0 | **rc 1** | rc 0 |
| F18 | `test_the_remedy_for_an_already_triaged_wish_names_what_it_became` | rc 0 | **rc 1** | rc 0 |
| F19 | `test_a_worktree_nobody_can_stand_in_is_refused` | rc 0 | **rc 1** | rc 0 |
| F6 | `test_every_reference_to_a_measurement_leads_to_one` | **rc 1 über leerem Bestand** | rc 0 über der migrierten Kopie | zusätzlich rc 1 mit zerstörtem Zeiger |

Die Mutation für F1 ersetzt die Eigenschaft durch eine Aufzählung; die zweite Zeile ist meine
eigene und trifft den Vertrag selbst — `CRITERIA_FIELDS` um ein Feld erweitert, das `SR` deklariert
(`contract`), und der benannte Test sieht es. Alle zehn Namen der Nacharbeit lösen auf
(`verify/s2/names.py`).

### AC-1, AC-2, AC-5 — Regression gegen den neuen Stand

AC-1 unverändert korrekt: nennt den BUG → WALKED; anderen BUG → REFUSED; beide → WALKED; nur die
Wurzel → REFUSED; `fail`-Auswahl → REFUSED; `pass` dann `fail` (full) → REFUSED;
`delivery={} confirmation={'test': 'pass'}`; dritte Frage → `ValueError`.
AC-2 unverändert korrekt in allen vier FR-Schreibweisen, Zähler 35, Validator-Warnung nur aktiv.
AC-5: Überlappung außerhalb der Naht REFUSED (mit Pfad), Naht beidseitig deklariert GRANTED,
einseitige Naht REFUSED, disjunkt GRANTED, abgelaufene Lease GRANTED.

### Paket

18 Dateien, identisch zur Runde-1-Liste, alle in `allowed_scope`; `kitupdate.py`,
`gate_dispatch.py`, `.claude/hooks/gate_*.py`, `_harness.py`, `settings.json`, `constitution/**`,
`agents/**`, `skills/**`, `templates/repo/**` unberührt; keine gespiegelte Datei geändert.
`git apply --check` gegen 75a00d1 **rc 0**; Arbeitsbaum == 75a00d1 + Patch + genau die drei
`VERSION`-Dateien (`2026.09.05-3`). **Der Patch selbst trägt jetzt 0 CR-Bytes** (Runde 1: durchgängig
CRLF), die 18 Quelldateien ebenfalls 0. Einziges „VERSION" im Patch ist Prosa in H148.
Migration Ende zu Ende gegen `mig2`: **143 written / 143 prose files**, Dokument 9289 → 2441 Zeilen,
zweiter Lauf **1,0 s, 0 written**, SHA256 identisch, `validate` **0 Fehler / 66 Warnungen**.
Lesende Suiten **414 passed** (77,5 s) und **193 passed** (76,7 s); `ruff check .` „All checks
passed"; `tools/validate.py` „all structural checks passed". Nur H154–H156 als neue Nummern im
Dokument.

### Nicht gemessen

- Die volle Suite und `tools/test_hooks.py` (DEC-0050: Lieferkriterium des Merges).
- Der Rest von `.claude/hooks/test_gates.py` außerhalb von `-k "hole or holes or
  reference_to_a_measurement"`.
- `gate_dispatch.py` von office-team und research-team als Prozess (nur dev-team gemessen).
- Der EINE schreibende Migrationslauf gegen den kanonischen Zustand (in diesem Auftrag verboten).
- Wirkung von ~178 aktiven `BUG`-Items auf Board, `session_brief` und die Rollups.
- `tools/bump_kit_version.py` / der Kit-Hash mit dem neuen Verzeichnis `docs/holes/`.
- Laufzeit von `_iter_every_stored_item` bei jedem `capture` in einem großen Speicher.
- Ob `related_pr: PR-0003` für 143 Löcher die Abnahme dieses Ziels beeinflusst.

---

## Einordnung

**Rundenblockierend: R1.** Ein Kommando, rc 0, und ein ausgelieferter Gate-Knoten ist rot, während
das ausgelieferte Dokument eine Entscheidung als Loch führt; die Reparatur liegt außerhalb der
Sitzung. Der Mechanismus — `--hole` prüft den Typ als Aufzählung von einem statt gegen den Vertrag,
für den der Loch-Datensatz geschrieben ist — gehört benannt, nicht die zwei Typen, die ich
zufällig probiert habe.

**In die Löcherliste als benannter Rest, falls nicht geschlossen:** R2 (`--reindex` gegen einen
leeren Speicher leert den Index mit einer Erfolgsmeldung) und R3 (die Befreiung fragt den Typ, der
Satz behauptet den Wert).

**Nacharbeit ohne Loch:** R4 (sechs Zahlen in Protokoll und Nacharbeitsbericht), R5 (die
Aufschlüsselung der Nahttabelle), R6, R7.

**Eigener Irrtum aus Runde 1:** F13 war bereits erledigt; mein Prüfstring war zu wörtlich für einen
über zwei Zeilen umbrochenen Satz. Der Umsetzer hat recht, ich hatte unrecht.
