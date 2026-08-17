# Das Backlog-Board: gemessene Runde zu TSK-0071 (aus FR-0030, Wurzel PR-0002)

**Runde:** TSK-0071 · **Datum:** 2026-08-16 · **Rolle:** harness-implementer

FR-0030 verlangt vier Dinge: (1) Kanban-Spalten nach Status über **alle** Item-Typen des Kits,
(2) automatische Regeneration, damit die Ansicht nicht veralten kann, (3) ausgeliefert von **allen
drei** Kits mit kit-passenden Typen, (4) **read-only**, kein neuer Schreiber. Dieses Dokument hält
fest, was gemessen wurde, was gebaut wurde, welcher Test ohne den Fix rot wird — und was
**offen benannt** und nicht geschlossen ist.

---

## 1. Messung und Entscheidung: der Renderer gehört in den Kernel

### 1.1 Jeder Index-Schreibpfad des Kernels (abgeleitet, nicht aufgezählt)

Über den AST der Kernel-Module, nach jedem Aufruf von `_regenerate_index_locked` /
`generate_index`, mit der umschließenden Funktion (Stand nach der Nacharbeit — im ersten
Durchgang waren es 15 Stellen, die zwei mit dem Vermerk sind in 7.1 dazugekommen):

| Datei:Zeile | Funktion |
|---|---|
| `state.py:786` | `capture` |
| `state.py:886` | `capture_migrated_archive` |
| `state.py:958` | `capture_migrated_unresolved` |
| `state.py:1029` | `_update_item_locked` |
| `state.py:1100` | `_transition_locked` |
| `state.py:1152` | `archive` |
| `state.py:1159` | `generate_index` (das CLI-Kommando) |
| `approvals.py:1175` | `mint` |
| `approvals.py:1216` | `revoke` — **in der Nacharbeit hinzugefügt** (7.1) |
| `dispatch.py:234` | `create_lease` |
| `dispatch.py:316` | `_validate_lease_locked` — **in der Nacharbeit hinzugefügt** (7.1) |
| `dispatch.py:428` | `reconcile_unstarted_dispatches` |
| `dispatch.py:793` | `spawn_outcome` |
| `dispatch.py:826` | `sweep_expired_leases` |
| `dispatch.py:1135` | `submit_result` |
| `staging.py:219` | `freeze_wireframe` |
| `staging.py:267` | `freeze_architecture` |

**Alle** laufen durch `ProjectState._regenerate_index_locked`. Damit gibt es genau **einen** Punkt,
an dem eine mitgeführte Ansicht hängen muss; ein zweiter Auslöser wäre ein zweites Ding, das man
vergessen kann — und genau das ist der gemessene Ausgangszustand von FR-0030 (das Pilot-3-Projekt
hat sein Dashboard nie erzeugt, weil nichts es startet).

### 1.2 Warum **nicht** ein Kit-Skript, das der Kernel aufruft

Drei Gründe, jeder gemessen oder strukturell:

1. **Fremdcode-Ausführung aus der Zustandsschicht.** Ein Kit-Skript liegt im Projekt unter
   `scripts/` — ein Bereich, den `gate_write_scope` **nicht** schützt (geschützt sind `.claude/`
   und `project_memory/`). Der Kernel würde also bei jedem `capture`, jedem `transition` und jedem
   Mint eine Datei starten, die jede Rolle vorher überschreiben kann.
2. **Kosten.** Ein Interpreterstart pro Zustandsschreibvorgang. Gemessen kostet der jetzige
   Renderer bei 199 Items **0,011 s** von 0,274 s einer kompletten Index-Regeneration (Mittel aus
   3 Läufen, `kernel.board.render` einmal aktiv, einmal durch eine Attrappe ersetzt).
3. **Dreifachpflege.** Ein Kit-Skript existiert dreimal und fiele unter die Spiegelregel; der
   Kernel ist **shared** (`kernel.hashing.kit_hash_inputs` hasht ihn in jede Kit-VERSION), also
   eine Datei für alle drei Kits.

**Entscheidung:** kernelseitiger Renderer `team-kits/kernel/board.py`, aufgerufen aus
`state._regenerate_index_locked`. Ausgabe ausschließlich unter `generated/`
(`ProjectState.generated_path`), das `kernel.layout.kernel_written_subtrees` bereits als
kernelgeschriebenen Bereich führt — es entsteht **kein neuer Schreiber** (FR-0030/4).

### 1.3 Warum die Datei `board.html` heißt und nicht `dashboard.html`

`team-kits/dev-team/templates/repo/scripts/generate_dashboard.py:340` schreibt weiterhin
`generated/dashboard.html`. Zwei Schreiber auf einem Pfad würden sich bei jedem Zustandsschreiben
gegenseitig überschreiben. Das Dashboard bleibt unangetastet (es trägt die Vitals-Tafel, die aus
`scripts/kit_checks.py` kommt — Kit-Code, den der Kernel nicht importieren darf). **Residuum
benannt in Abschnitt 5.1.**

---

## 2. Was gebaut wurde

| Ort | Was |
|---|---|
| `team-kits/kernel/board.py` (neu, 395 Z.) | der Renderer: `FILENAME:52`, `VALUE_MAX_DEPTH:75`, `NESTED_MARKER:85`, `status_columns:94`, `types_present:112`, `_Ink:124`, `_emit:152`, `_flat:200`, `_card:236`, `_section:274`, `render:349` |
| `team-kits/kernel/state.py:65` | `from . import board` |
| `team-kits/kernel/state.py:1161-1213` | `_regenerate_index_locked` sammelt die schon gelesenen Item-Bodies mit, nimmt **eine** Uhrzeit für beide Dateien (`:1209`) und ruft `_write_board` (`:1212`); der Schreibvorgang selbst mit seiner Fail-Soft-Regel steht in `_write_board:1215` |
| `team-kits/kernel/cli.py:52,298-302,766-770` | `generate-index` nennt beide Artefakte in der Hilfe und druckt beide Pfade (`:769`) |
| `team-kits/*/templates/project_memory/README.md` | `generated/`-Zeile + ein Regel-Punkt, in allen drei Kits (dev `:30,:39`, office `:25,:34`, research `:27,:36`) |
| `tools/test_board.py` (neu, 21 Tests) | die Messung, siehe Abschnitte 4 und 7 |

**Abgeleitet statt aufgezählt, an den zwei Stellen, an denen eine Liste verrottet:**

* **Welche Typen ein Kit hat** = die Typen, für die die Zustandsablage ein Verzeichnis hat
  (`types_present`, gelesen über `ACTIVE_DIRS` + `os.path.isdir`). Es gibt keine Pro-Kit-Typtabelle,
  die damit uneins werden könnte.
* **Welche Spalten ein Typ hat** = sein eigener Automat (`status_columns`): Kette in Kettenreihen-
  folge, dann Nebenzustände, dann Terminale. Gemessen z. B. TSK →
  `DRAFT READY LEASED IN_PROGRESS SUBMITTED DONE VALIDATED | FAILED | CANCELLED`;
  DEC (kein Automat) → `VALID SUPERSEDED`; EVD (kein Status per Vertrag) → eine Spalte `(no status)`.

**Karten:** `<details>` ohne jedes JavaScript — die Stirnseite trägt Id und Titel, der Falz **jedes
Feld, das die Stirnseite nicht trägt** (`FACE_FIELDS:76`). Damit erscheint ein neues Item-Feld am
Tag seines Erscheinens auf der Karte.

**Nichts fällt weg:** ein Status, den kein deklarierter Spaltensatz kennt, bekommt eine eigene
Spalte **plus** eine Warnung auf der Seite; eine unlesbare Item-Datei landet in `(unreadable)` plus
Warnung; ein Record-Typ ohne Status (EVD/APR/ARC/WFR/DSN) bekommt `(no status)` **ohne** Warnung —
das ist sein Vertrag, keine Störung.

---

## 3. Messung auf allen drei Kits und auf diesem kit-losen Repo

### 3.1 Die drei Kit-Templates (in `tmp`, echter Kernel-Schreibvorgang)

`tools/test_board.py:283` kopiert `team-kits/<kit>/templates/project_memory/` und captured ein
kit-passendes Item. Gerendert wird genau die Typmenge, die das Kit-Template ausliefert:

| Kit | gerenderte Sektionen | ausdrücklich **nicht** vorhanden |
|---|---|---|
| dev-team | APR ARC BUG CR DEC DSN EVD FR INV PR SR TSK WFR | RQ, HYP, EXP, PROC |
| research-team | APR BUG CR DEC EVD EXP FR HYP INV RQ TSK | PR, PROC, ARC |
| office-team | APR BUG CR DEC EVD FR INV PROC TSK | PR, RQ, HYP, EXP, ARC |

### 3.2 Dieses Repo, kit-los, Kernel direkt aufgerufen

**Nicht** im Repo ausgeführt: eine Kopie des Arbeitsbaums außerhalb (`%TEMP%\tsk0071-clone`),
damit kein Werkzeug in `project_memory/` schreibt.

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index
→ …\generated\index.yaml
→ …\generated\board.html
board.html: 323 275 Bytes, 199 Karten, 13 Sektionen, 0 Warnungen
Sektionen: APR 0 · ARC 0 · BUG 55 · CR 0 · DEC 44 · DSN 0 · EVD 43 · FR 44 · INV 0 · PR 3 · SR 8 · TSK 2 · WFR 0
```

---

## 4. Die Tests und ihr Rot-Lauf (Klon außerhalb des Repos)

Alle Prüfungen lesen die **gerenderte Seite als HTML** (`tools/test_board.py:75`, `HTMLParser` über
`data-type` / `data-status` / `data-item` / `data-warning`) — dieselben Knoten, die ein Browser
anzeigt. Es gibt bewusst **keinen** JSON-Block im Artefakt: ein Test, der eine eingebettete Nutzlast
liest, misst etwas, das niemand ansieht.

Rot-Läufe in `C:\Users\zenti\AppData\Local\Temp\tsk0071-clone` (Kopie ohne `.git`), Defekt jeweils
wiederhergestellt, gemessen, danach zurückgesetzt (`13 passed` bzw. `14 passed` nach jeder
Rücknahme).

### Defekt 1 — der Index-Schreibpfad schreibt kein Board (der Zustand VOR dieser Runde)

`state._regenerate_index_locked` auf seinen alten Rumpf zurückgesetzt.

```
12 failed, 1 passed in 7.43s
FileNotFoundError: …\project_memory\generated\board.html
```

Rot u. a.: `test_every_state_write_leaves_a_board_as_fresh_as_the_index` (a),
`test_each_kit_renders_the_types_its_own_template_ships[dev-team|research-team|office-team]` (b),
`test_the_documented_command_writes_and_names_both_artefacts`.
Grün blieb nur der Test, der `board.render` direkt aufruft — korrekt, denn `board.py` war intakt.

### Defekt 2 — nur deklarierte Spalten erreichen die Seite (die Aufzählungs-Variante)

`extra = []` in `_section`.

```
4 failed, 9 passed in 10.24s
AssertionError: ZZZ-0001 appears 0 time(s) on the board
AssertionError: BUG-0001 appears 0 time(s) on the board
AssertionError: EVD-0001 appears 0 time(s) on the board
AssertionError: SR-0001 appears 0 time(s) on the board
```

Rot: `test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning` (c),
`test_a_status_off_its_types_vocabulary_still_appears_and_warns`,
`test_a_record_type_without_a_status_is_not_reported_as_a_defect`,
`test_an_item_file_that_cannot_be_read_is_shown_rather_than_dropped`.

### Defekt 3 — die Gegenrichtung: ein Record-Typ wird als Defekt gemeldet

`elif column == NO_STATUS:` ohne `and declared`.

```
1 failed, 12 passed in 3.06s
AssertionError: [['missing-status', 'EVD', 'EVD: 1 item(s) carry no status although EVD declares ']]
```

Rot: `test_a_record_type_without_a_status_is_not_reported_as_a_defect`. Das ist die
Über-Alarm-Richtung: eine Warnung, die auf jedem Projekt mit einer einzigen Evidence feuert, ist
Rauschen und macht die echte Warnung unsichtbar.

### Defekt 4 — der Defekt, den **diese Runde selbst** eingebaut hatte

Beim Nachprüfen des eigenen Codes gefunden, nicht vom Prüfer: `_flat` lief ohne Tiefenbegrenzung
über den Item-Body. Ein YAML-Anker, der auf seinen eigenen Container zeigt
(`repro: &loop [step, *loop]`), ist eine gültige Datei, die `yaml.safe_load` in ein
selbstreferenzielles Objekt auflöst. Gemessen gegen den Klon **vor** dem Fix:

```
RAISED: RecursionError maximum recursion depth exceeded
index exists: True
```

Weil der Renderer am **Ende jedes Zustandsschreibvorgangs** läuft und dieser über **alle** aktiven
Items liest, hätte **eine** solche Datei jedes spätere `capture` im Projekt scheitern lassen — ein
Schaden, den der Index allein nie hatte (`yaml.safe_dump` schreibt den Anker klaglos).
Fix: `VALUE_MAX_DEPTH` (`board.py:75`); an der Grenze steht seit der Nacharbeit `NESTED_MARKER`
statt `str()` (7.3c). Rot ohne den Fix:

```
1 failed, 13 passed in 4.93s
RecursionError: maximum recursion depth exceeded  (in `board._flat`)
FAILED tools/test_board.py::test_a_self_referential_item_body_does_not_stop_the_state_write
```

---

## 5. Was **nicht** geschlossen ist — benannt, nicht weggeschrieben

### 5.1 dev-team hat jetzt zwei Übersichten

`generated/board.html` (Kernel, automatisch) **und** `generated/dashboard.html`
(`scripts/generate_dashboard.py`, nur auf Zuruf). Das Dashboard trägt zwei Dinge, die das Board
nicht hat: die Vitals-Tafel aus `scripts/kit_checks.source_files()` und die 50-Items-pro-Seite-
Grenze aus Spec II.7. Beides ist Kit-Code, den der Kernel nicht importieren darf, also ist die
Zusammenlegung **kein** Handgriff, sondern eine Produktentscheidung (Vitals abgeben oder das
Dashboard behalten). **Nicht entschieden, nicht angefasst.** Office und research haben nur das
Board — dort gab es vorher gar nichts.

### 5.2 Items ohne `title` zeigen nur ihre Id auf der Stirnseite

`TSK`, `EVD`, `HYP`, `EXP` führen laut `REQUIRED_FIELDS` **kein** `title`. Die Karte zeigt dann die
Id, alles Weitere liegt im Falz. Eine „Ersatzüberschrift" wäre eine Pro-Typ-Entscheidung (welches
Feld ist das Gesicht eines TSK?) — genau die Art Aufzählung, die diese Runde vermeiden sollte.
Benannt, nicht geraten.

### 5.3 Der Falz zeigt **jedes** Feld — auch `mint_code` einer verbrauchten APR

Gemessen: `iter_active_items("APR")` liest **nur** `approvals/*.yaml`, nicht `approvals/pending/`;
die **lebenden** Mint-Codes stehen also nicht auf der Seite. Auf einer geminteten
`approvals/APR-nnnn.yaml` steht der bereits verbrauchte Code (`approvals.py:1123`), und den zeigt
das Board. Der Code allein mintet nichts (`mint` liest die Pending-Datei, die nach dem Mint
verschoben ist), und `generated/` ist in allen drei Kits ignoriert. Eine Feldunterdrückung nach
Namen wäre eine Aufzählung ohne Definition — deshalb **benannt statt gebaut**.

### 5.4 Dieses Repo bekommt eine neue, nicht ignorierte Datei

`project_memory/generated/index.yaml` ist hier **getrackt**, und die Wurzel-`.gitignore` nennt
`generated/` nicht. Nach dieser Runde legt der nächste Kernel-Schreibvorgang in diesem Repo
`project_memory/generated/board.html` (~320 KB) als **untracked** Datei ab. `.gitignore` liegt
außerhalb des `allowed_scope` dieses Auftrags (erlaubt sind `team-kits/**`, `tools/**`,
`docs/reviews/**`), also ist das eine Entscheidung des Leads: Datei mitcommitten oder Ignore-Regel
ergänzen. `tools/test_repo_hygiene.py` schlägt dadurch **nicht** an (es misst getrackt ∩ ignoriert).

### 5.5 Seitengröße wächst linear mit dem Store

323 KB bei 199 Items (≈1,6 KB/Item), pro Feldwert auf `VALUE_MAX_CHARS` (600) begrenzt. Es gibt
**keine** Obergrenze für die Kartenzahl — bewusst: eine Grenze, die Karten verschwinden lässt, ist
genau der Fehler, gegen den FR-0030 geschrieben ist (Erledigtes verschwindet über das Archiv, nicht
über eine Seitenzahl). Bei einem Store in der Größenordnung 10 000 Items ist das eine Seite von
mehreren MB; dann ist die richtige Antwort die App aus FR-0024, nicht ein Deckel hier.

### 5.6 Die beiden Sentinel-Spalten sind Zeichenketten und damit im Prinzip kollidierbar

`(no status)` und `(unreadable)` sind Spaltenschlüssel wie jeder Status auch. Eine **von Hand**
geschriebene Item-Datei mit exakt `status: (no status)` landete damit in der Sentinel-Spalte statt
in einer eigenen. Gefolgt bis zum Ende: der Schaden ist kosmetisch (das Item ist sichtbar, nur in
der falsch beschrifteten Spalte), der Aufwand für unterscheidbare Schlüssel zieht sich durch
Renderer und Tests. Bewusst **nicht** gebaut, hier benannt.

### 5.7 Abweichung vom Item-Wortlaut

`expected_outputs` Schritt 3 (c) verlangt „ein Item-Typ, den die **Views** nicht kennen (der
`Other`-Warnpfad)". Ein Board, das für **jeden** Typ eine eigene Sektion baut, hat keine
View-Zuordnung, gegen die ein Typ unbekannt sein könnte — die Eigenschaft rutscht eine Ebene
tiefer: unbekannt ist jetzt der **Status**, den kein Spaltensatz des Typs beschreibt. Genau das
messen die beiden Tests in Abschnitt 4/Defekt 2, in beiden Richtungen (Fremdtyp `ZZZ` direkt durch
den Renderer; handgeschriebener Status durch den echten Schreibpfad). Das ist derselbe Fehlermodus
(„ein Item verschwindet lautlos aus der einzigen Übersicht"), aber **nicht** derselbe Wortlaut —
hiermit ausdrücklich benannt, damit der Lead das Item nachziehen kann.

---

## 6. Abschluss

Ein Zwischenlauf war rot und gehört ins Protokoll: `11 failed, 2761 passed` — alle elf mit
„does not hash to the `content:` in its own VERSION". Ursache war ausschließlich, dass in diesem
Lauf `board.py` **nach** dem Stempel noch einmal (nur an Kommentaren) geändert wurde. Nach
erneutem `bump_kit_version.py` grün, siehe Tabelle.

| Schritt | Ergebnis |
|---|---|
| `python tools/bump_kit_version.py` | dev/office/research → **2026.08.16-15** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python -B -m pytest tools/ -q` | **2772 passed, 13 skipped** in 2006,71 s (0:33:26), rc 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **243 passed** in 1720,75 s — nicht vom Auftrag verlangt, aber der Kernel liegt im Importpfad der Gates |
| Spiegel | keine gespiegelte Datei berührt: der Kernel ist **shared** (eine Kopie), die drei `templates/project_memory/README.md` sind per Konstruktion kit-verschieden und in keiner Spiegelliste (`tools/validate.py` MIRROR_*, `tools/test_hooks.KIT_SPECIFIC_HOOKS` decken `hooks/` und `templates/repo/scripts/` ab) |

---

## 7. Nacharbeit nach dem Prüferurteil (FAIL, 2026-08-17)

Der Prüfer hat zwei blockierende Befunde, zwei benannte Löcher und zwei leichte gemeldet. Was
davon wie geschlossen wurde, mit der Messung daneben. **Alle Zeilennummern in diesem Dokument sind
am Ende dieser Nacharbeit neu abgeleitet** (Abschnitt 7.7) — die aus dem ersten Durchgang waren um
eine Zeile verschoben, weil nach dem Stempel noch ein Kommentar geändert wurde (Befund B7).

### 7.1 B2 (blockierend) — die Frischezusage war in drei READMEs und auf der Seite selbst falsch

Zwei Kernel-Schreibwege schrieben eine Datei, die das Board rendert, **ohne** den Index neu zu
bauen:

1. `approvals.revoke` — die APR-Datei wird auf `revoked: True` gesetzt, die Karte zeigte weiter
   `False`. Board-spezifisch, weil `revoked` in **keiner** Indexzeile steht: nur die Karte kann es
   überhaupt zeigen.
2. der Freigabepfad einer **abgelaufenen Lease** in `dispatch._validate_lease_locked` — die Aufgabe
   steht auf der Platte wieder auf `READY`, Index und Board sagten weiter `LEASED`. Das war
   zugleich eine vorbestehende Index-Lücke.

**Beide Richtungen gemessen, bevor entschieden wurde.** Eine eigene AST-Ableitung über das
Kernel-Paket (jede Funktion, die `_write_yaml_atomic`/`_write_text_atomic` aufruft, gegen die, die
`_regenerate_index_locked` aufruft) findet **genau diese zwei** und keine dritte: `freeze_design`
regeneriert über `_update_item_locked` am Wurzelitem, `_release_lease_locked` über seine vier
Aufrufer (drei taten es, einer nicht — das war Nr. 2), alles Übrige schreibt Leases,
Pending-Anfragen, Checkpoints, Kit-Dokumente oder `generated/` selbst.

**Entschieden: Code reparieren, nicht Prosa abschwächen** — die Regeneration liegt in beiden Fällen
auf einem **seltenen** Zweig, der ohnehin schon Dateien schreibt (ein Widerruf ist eine Nutzeraktion,
eine Lease läuft einmal ab), und eine bestandene Lease-Prüfung bleibt ein reiner Lesevorgang. Kosten
einer Regeneration, gemessen am 199-Item-Store dieses Repos: 0,274 s, davon 0,011 s Board.

Die Prosa wurde **zusätzlich** auf das zurückgeführt, was der Code baut — denn mit der neuen
Fail-Soft-Regel (7.3) kann ein Neubau ausfallen: die drei READMEs und die Seitenfußnote sagen jetzt
„zusammen mit `index.yaml` bei jedem Zustandsschreibvorgang; scheitert der Neubau, sagt er es auf
der Fehlerausgabe und lässt Seite **und Zeitstempel** stehen" statt „kann nicht älter sein als der
Zustand".

**Rot ohne den Fix** (Klon, je einzeln zurückgebaut):

```
Regeneration aus `revoke` entfernt:
  FAILED test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind
  FAILED test_a_revoked_approval_shows_as_revoked_on_the_board — assert 'False' == 'True'
  2 failed, 19 passed
Regeneration aus `_validate_lease_locked` entfernt:
  FAILED test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind
         — ('dispatch.py', '_validate_lease_locked') releases a lease ...
  FAILED test_an_expired_lease_puts_the_task_back_on_the_board_as_ready
         — assert ('TSK', 'LEASED') == ('TSK', 'READY')
  2 failed, 19 passed
```

Der erste Test ist der Stolperdraht für die **Klasse**: er leitet die Schreiber aus dem Paket ab
und trägt die Ausnahmen mit Begründung; ein Eintrag, dessen Funktion nichts mehr schreibt, wird
ebenso rot wie ein Schreiber ohne Regeneration.

### 7.2 B3 (blockierend) — der Falz-Test maß seine eigene Konstante

`test_the_fold_carries_every_field_the_face_does_not` verglich `set(fold)` mit
`set(item) - set(board.FACE_FIELDS)` — also die Konstante mit sich selbst. Die Mutationen des
Prüfers liefen beide grün, obwohl die erste ein Feld **komplett** von der Karte nimmt.

Ersetzt durch `test_every_field_of_an_item_is_on_its_card_exactly_once`: die drei **gerenderten
Orte** werden in der geparsten Seite nachgeschlagen (Karten-Id, Titel auf der Stirnseite, Spalte)
und zählen nur, wenn dort wirklich der Wert des Items steht; alles andere muss im Falz sein, und
nichts darf doppelt sein. Beide Mutationen jetzt rot:

```
FACE_FIELDS = ("id", "title", "status", "priority")  → FAILED ... Extra items in the right set: 'priority'
FACE_FIELDS = ("id",)                                → FAILED ... 'title', 'status'
```

### 7.3 B1 + B5 (empfohlen, gebaut) — das Board darf einen Zustandsschreibvorgang nie zum Scheitern bringen

Vier Teile, jeder einzeln rot gemessen:

**(a) Fail-Soft um Render und Schreiben** (`ProjectState._write_board`). Der Index ist Zustand und
muss hart scheitern; das Board ist ein **Bericht darüber** und wird **nach** Item und Index
geschrieben — eine Ausnahme dort meldet einen bereits erfolgten Schreibvorgang als gescheitert, und
zwar ab dann bei **jedem** weiteren, weil der Renderer alle Items liest. Jetzt: Warnung auf stderr,
Zustandsschreibvorgang geht durch. Rot ohne den Fix (Zielpfad durch ein Verzeichnis blockiert):

```
PermissionError: [WinError 5] Zugriff verweigert: ...board.html.tmp-48988 -> ...board.html
FAILED test_a_board_that_cannot_be_written_does_not_fail_the_state_write
```

Gemessen auf diesem Host, weil der Prüfer den Windows-Fall nannte: ein **gewöhnlicher Lesehandle**
auf `board.html` lässt `os.replace` mit genau diesem `PermissionError` scheitern (eigene Sonde). Der
Test benutzt ein Verzeichnis an Stelle der Datei — dieselbe Klasse, auf jeder Plattform.

**(b) Surrogat** — `"\uD800"` ist gültiges YAML und in UTF-8 nicht kodierbar. Der
Board-Schreibvorgang (und **nur** er) kodiert jetzt mit `errors="replace"`; wo die Bytes der Zustand
sind, bleibt es strikt. Rot ohne den Fix:

```
[board] ...board.html was NOT rebuilt (UnicodeEncodeError: 'utf-8' codec can't encode character
        '\ud800' in position 2643: surrogates not allowed); the state write itself went through ...
FAILED test_a_surrogate_in_an_item_does_not_stop_the_state_write — FileNotFoundError
```

(Der Auszug zeigt beide Hälften auf einmal: ohne `errors="replace"` fängt die Fail-Soft-Regel den
Fehler, der Zustandsschreibvorgang überlebt — aber es gibt kein Board, und **das** macht den Test
rot.)

**(c) Alias-Bombe** — `yaml.safe_load` löst Aliase in **geteilte** Objekte auf; wenige hundert Bytes
beschreiben eine Struktur, deren Abflachung riesig ist. Die erste Fassung traf das doppelt: sie gab
den Container an der Tiefengrenze an `str()` (das den ganzen Graphen darunter wieder entfaltet) und
schnitt den Text erst **nach** dem Bauen. Jetzt: `NESTED_MARKER` statt `str()`, und `_Ink` gibt
jedem Feldwert ein Zeichenbudget, das die **Wanderung** stoppt. Gemessen an einem 1 894-Byte-Item
(drei Alias-Ebenen à 150):

| | Speicher (tracemalloc, Spitze) | Dauer | Board-Zuwachs |
|---|---|---|---|
| erste Fassung | **281,6 MB** | 13,94 s | wenige KB (der Schnitt kam ja danach) |
| jetzt | **< 8 MB** (Schranke des Tests) | 0,34 s | 2,9 KB |

```
FAILED test_an_alias_bomb_cannot_stretch_a_state_write
       — rendering a 1894-byte item allocated 281.6 MB
```

Die Wanduhr ist hier bewusst **nicht** das Maß: sie trennt die beiden Fassungen erst bei Breiten,
deren Zwischenstring hunderte MB kostet. Gemessen wird, was die Arbeit verbraucht (Speicher), was
auf die Seite darf (Bytes) und dass der tiefe Container **markiert** statt entfaltet wurde.

**(d) pro Karte** — `board._card` fängt zusätzlich je Item und macht daraus eine Karte, die den
Ausfall **mit Item-Id** zeigt, plus eine Warnung auf der Seite. Rot ohne den Fix:

```
AttributeError: 'list' object has no attribute 'items'
FAILED test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else
```

**Ein Nebenbefund aus dieser Nacharbeit, gemessen:** die Warnung ging zuerst über
`sys.stderr.write`, und das machte
`test_approvals_dispatch.test_the_store_has_exactly_one_writer_for_this_derivation_to_rest_on` rot
(`kernel/state.py puts data on disk from ['_write_board', …]`) — jene Ableitung erkennt einen
Schreiber an der Form seines Aufrufs, und `.write` sieht aus wie einer. Die Meldung läuft jetzt über
`print(..., file=sys.stderr)`, dieselbe Schreibweise, die `kernel/cli.py` für dieselbe Ausgabe
benutzt; der Grund steht als Kommentar daneben und nennt den Test.

### 7.4 B4 (leicht) — die Begründung neben `VALUE_MAX_CHARS`

Die Behauptung „die gemessenen Kosten dieses Imports stehen im Rundenbericht" war doppelt falsch:
im Bericht stand keine solche Messung, und ein Modulimport fällt einmal pro Prozess an, nicht pro
Schreibvorgang. Ersetzt durch den **strukturellen** Grund, der nachprüfbar ist: `kernel/report.py`
importiert `state` auf Modulebene, `state` importiert `board` — ein Rückimport nach `report` wäre
ein Importzyklus. Dieses Modul ist ein Blatt, und das ist der Grund.

### 7.5 B6 — die Abweichung ist vom Lead ins Item übernommen

`expected_outputs` Schritt 3(c) liest jetzt auf Status-Ebene. Die beiden Tests, die das messen,
sind unverändert (`test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning`,
`test_a_record_type_without_a_status_is_not_reported_as_a_defect`). Abschnitt 5.7 bleibt als
Protokoll der Abweichung stehen.

### 7.6 Was in dieser Nacharbeit **nicht** geschlossen wurde

* Die Residuen 5.1 bis 5.6 stehen unverändert.
* **Neu und benannt:** die Fail-Soft-Regel macht die Frischezusage bedingt. Ein Board, dessen
  Neubau scheitert, bleibt stehen, und die **Seite selbst** kann das nicht sagen — sie wurde ja
  nicht geschrieben. Was sie kann, ist ihren eigenen Zeitstempel zeigen; die Warnung steht auf der
  Fehlerausgabe des auslösenden Kommandos. In einem Hook-Unterprozess landet diese Ausgabe dort, wo
  der Hook seine Meldungen hinschreibt — gelesen wird sie also nur, wenn jemand hinschaut.
* Der Renderer läuft in Kit-Hooks (`gate_approval`, `gate_dispatch`) mit, deren Registrierungen in
  der Kit-`settings.json` **kein** `timeout` nennen. Das ist eine Eigenschaft dieser Registrierungen
  und liegt außerhalb dieser Runde: der Renderer ist jetzt in Speicher und Ausgabe begrenzt und
  fällt weich aus, aber ein Zeitlimit gibt ihm nur die Registrierung.

### 7.7 Zeilenzeiger, am Ende neu abgeleitet (Befund B7)

Die Zeiger des ersten Durchgangs waren um eine Zeile verschoben und die Größenangabe zu `board.py`
um eine Zeile zu klein: nach dem Versionsstempel wurde dort noch ein Kommentar geändert, und der
Bericht war vor dieser Änderung geschrieben. Beides ist korrigiert, und diesmal maschinell:

* Jeder Symbolzeiger (`FILENAME`, `status_columns`, `_Ink`, `_write_board`, …) ist aus dem AST der
  jeweiligen Datei gelesen, nicht abgetippt.
* Die Tabelle der Index-Regenerationsstellen in Abschnitt 1.1 ist aus demselben AST-Lauf neu
  erzeugt; sie hat durch die Nacharbeit **zwei** Einträge mehr (`approvals.revoke`,
  `dispatch._validate_lease_locked`), beide dort vermerkt.
* Zum Schluss wurde jeder `datei:zeile`-Zeiger dieses Dokuments (25 Stück) dagegen geprüft, dass
  die Datei existiert und die Zeile in ihr liegt.
* Eine Zeilennummer, die zu einem **historischen** Rot-Lauf gehört (der Traceback der
  Rekursionsmessung), steht jetzt ohne Nummer da und nennt nur die Funktion: sie zeigte auf einen
  Klon-Stand, den es nicht mehr gibt, und eine solche Zahl wird nie wieder wahr.

`board.py` hatte nach jener Nacharbeit 382 Zeilen; nach Runde 2 (Abschnitt 8) sind es **395**, und die Zeiger oben sind erneut maschinell nachgezogen.

### 7.8 Abschluss der Nacharbeit

| Schritt | Ergebnis |
|---|---|
| `python tools/bump_kit_version.py` | dev/office/research → **2026.08.17-1** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python -B -m pytest tools/ -q` | **2779 passed, 13 skipped** in 1796,32 s (0:29:56), rc 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **243 passed** in 1570,11 s (0:26:10), rc 0 — nicht vom Auftrag verlangt, aber der Kernel liegt im Importpfad der Gates |
| Spiegel | unverändert: der Kernel ist shared (eine Kopie), die drei `templates/project_memory/README.md` sind per Konstruktion kit-verschieden und in keiner Spiegelliste |

---

## 8. Nacharbeit nach Prüfrunde 2 (FAIL, eng: C1 + C2)

### 8.1 C1 — die Tiefengrenze hatte keinen Test, der rot werden konnte

**Der Befund, nachvollzogen:** `NESTED_MARKER` war `"…"` — dieselbe Ellipse, die `_flat` beim
Budgetschnitt anhängt. Damit war `assert NESTED_MARKER in fold` schon durch den Schnitt erfüllt, und
die alte Bombe hatte ihren **kleinsten** Container an der Tiefengrenze (unter `str()` dort ganze
14 Zeichen wert). Beides zusammen: der Rückbau auf `str(value)` an der Grenze — genau der Defekt
aus Runde 1 — lief **grün** durch.

**Drei Teile geändert:**

1. `NESTED_MARKER` ist jetzt `"[…]"` und damit vom Schnitt unterscheidbar. Der Schnitt hängt `"…"`
   an, und `"[…]" in text` ist davon nicht erfüllbar.
2. Der Test trägt jetzt **zwei** Bomben in einem Item, weil die zwei Grenzen verschieden versagen:
   * `deep` wächst nach außen (`l1 = [x, x]`, jede Ebene verdoppelt die vorige, `l24` steht für
     2**23 Blätter in ~500 Byte Datei). Der **größte** Container liegt damit genau **auf** der
     Tiefengrenze — dort entfaltet `str()` den ganzen Graphen in **einem** Aufruf, den kein
     Zeichenbudget unterbrechen kann.
   * `wide` (drei Ebenen à 150) hält seine Masse **unterhalb** der Grenze, wo die Markierung nie
     greift und nur das Budget der Wanderung bremst.
3. Drei Prosastellen korrigiert: `board._emit` sagt nicht mehr „`_Ink` ist, was das stoppt" und
   nicht mehr „keine der beiden Grenzen hängt davon ab, dass die andere hält" — sie sagt jetzt,
   dass die beiden **nicht** unabhängig sind und warum; der Testdocstring sagt, dass die
   Markierung nur deshalb ein Beleg ist, weil sie nicht die Ellipse des Schnitts ist.

**Rot ohne den Fix, je einzeln im Klon gemessen** (Item: 4 695 Byte):

| Mutation | Ergebnis |
|---|---|
| `str(value)` an der Tiefengrenze (Defekt aus Runde 1), Marker distinkt | **rot: 128,0 MB / 22,55 s** |
| Budget entfernt (`_Ink` praktisch unbegrenzt), Marker intakt | **rot: 91,7 MB / 10,02 s** |
| ausgelieferter Code | grün: **0,04 MB / 0,017 s**, Board-Zuwachs 1 586 B |

```
FAILED test_an_alias_bomb_cannot_stretch_a_state_write
       — rendering a 4695-byte item allocated 128.0 MB   (str() an der Grenze)
       — rendering a 4695-byte item allocated 91.7 MB    (ohne Budget)
```

Beide Mutationen werden von **je einer** der beiden Bomben gefangen — die Abdeckung der Breiten-
Grenze aus Runde 1 ist also nicht verloren gegangen, sondern steht neben der neuen.

**Und die Blindheit selbst, gegengemessen:** mit ausgeliefertem Code, aber `NESTED_MARKER = "…"`
läuft der Test grün — die Marker-Zusicherung allein trägt nichts. Was den Defekt fängt, ist die
Speicherschranke; die Markierung ist Beleg dafür, **dass** markiert wurde, und der Docstring sagt
jetzt genau das.

### 8.2 C2 — die fünfte Prosastelle

`state._regenerate_index_locked` behauptete weiter „so the human-readable view cannot be older than
the index", zwanzig Zeilen über der eigenen Fail-Soft-Regel, die genau den Gegenfall baut. Jetzt:
„is REBUILT WITH the index" plus ein Absatz, der sagt, warum nicht „never older than" — und der
auf `_write_board` zeigt, wo die ehrliche Fassung steht. Damit tragen alle fünf Stellen (drei
READMEs, Seitenfußnote, dieser Docstring) dieselbe bedingte Zusage.

Ein Test für eine Prosakorrektur gibt es nicht; der Beleg ist der Diff und die Tatsache, dass
`test_a_board_that_cannot_be_written_does_not_fail_the_state_write` den Gegenfall festhält, den der
Satz vorher bestritt.

### 8.3 C3 — nicht meins

Der offene Lesehandle, der die Seite für die Sitzung einfriert, geht laut Lead als Mechanismus +
Kette in `docs/POST_V2_WISHLIST.md`; diese Datei bleibt für mich gesperrt. In diesem Bericht steht
er als 7.6 benannt.

### 8.4 Läufe dieser Runde

| Schritt | Ergebnis |
|---|---|
| `python tools/bump_kit_version.py` | dev/office/research → **2026.08.17-2** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python -B -m pytest tools/ -q` | **2779 passed, 13 skipped** in 1839,72 s (0:30:39), rc 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **243 passed** in 1678,89 s (0:27:58), rc 0 |

**Warum der volle Lauf und nicht ein enger:** geändert sind `team-kits/kernel/board.py` (eine
Konstante plus Kommentare), ein Docstring in `team-kits/kernel/state.py` und `tools/test_board.py`
— aber der Versionsstempel wandert mit, und genau der hat in Runde 1 elf Tests in vier Modulen
rot gemacht (`test_hooks`, `test_hooks_v2`, `test_kitupdate`, `test_presets`), die mit dem Board
nichts zu tun haben. Ein enger Lauf hätte also die Klasse ausgelassen, die hier real getroffen hat.

**Warum `test_gates.py` trotzdem mitläuft:** `.claude/hooks/_harness.py:2043` importiert
`kernel.state`, und `kernel.state` importiert `kernel.board` — das Modul liegt also im Importpfad
der Gates dieses Repos. Verhalten hat sich dort nichts geändert (eine Anzeigekonstante und
Kommentare), aber „liegt im Importpfad" ist die Regel, nach der die Frage entschieden wird, nicht
„hat sich verhaltensrelevant geändert".
