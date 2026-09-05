# TSK-0122 (PR-0005, Strom G4-2) — Prüfbericht Runde 4 (Nacharbeit 3, nur N1–N4)

Rolle: `harness-verifier`. Read-only am Repo; frische Kopien unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0122/verify/`: `wt4` (Arbeitsbaum ohne `.git`),
`base4` (75a00d1), `mut4` (Mutationskopie), `pilots_r4/**`. Alles außer N1–N4 steht aus Runde 3.

| Befund | Urteil |
|---|---|
| **N1** — H155 und Docstring behaupteten eine Begrenzung, die die Messung widerlegt | **PASS** |
| **N2** — die CLI-Prüfstelle war von ihrem benannten Test nicht gemessen | **PASS** |
| **N3** — `hole_type()` las eine schmalere Quelle als sein Satz | **PASS im Verhalten, FAIL in der Deckung** (N3′) |
| **N4** — falsche Nennung in der Nahttabelle | **PASS** |

**ABSCHLUSSURTEIL TSK-0122: PASS mit einer benannten Nacharbeit (N3′).** Das Paket erfüllt AC-1
bis AC-5 und die Pflichten 6–8; es steht kein Loch im Code offen, dessen Kette in einer Sitzung
durchläuft. Übrig ist ein Testdefekt: die N3-Korrektur ist von nichts gemessen, und der Test, der
sie halten soll, prüft noch die alte Quelle. Das ist ein Zweizeiler und kein Grund, das Paket
zurückzuhalten — aber es gehört vor dem Merge erledigt oder als Nacharbeit benannt.

---

## N1 — PASS

Beide Texte tragen jetzt genau die Kette, die ich in Runde 3 gemessen habe.
`team-kits/kernel/dispatch.py:2013-2027` und `docs/POST_V2_WISHLIST.md` (H155, zweite Restklasse,
als dreizeilige Tabelle) sagen: Universum ist `_known_acceptance_ids_locked` (Wurzel, Ursprung und
genehmigte Amendments), die **Lease wird in allen drei Fällen erteilt**, verweigert wird am
**Spawn**, und der Rest ist die eine Zeile „leerer Ursprung + Referenz der Wurzel".

Nachgemessen gegen `wt4` (`verify/s4/r3.py`, ausgelieferter `dev-team/hooks/gate_dispatch.py` als
echter Prozess):
```
BUG criteria filled, refs AC-1 (in bug and root)   owed=False lease GRANTED | hook rc=0
BUG criteria EMPTY,  refs AC-1 (only in root)      owed=False lease GRANTED | hook rc=0
BUG criteria EMPTY,  refs AC-9 (nowhere)           owed=False lease GRANTED | hook rc=2 "references criteria that exist nowhere: AC-9"
BUG criteria filled, refs AC-9 (nowhere)           owed=False lease GRANTED | hook rc=2
BUG criteria EMPTY,  refs []                       owed=False lease GRANTED | hook rc=2 "carries no acceptance_refs"
```
Zeile für Zeile deckungsgleich mit der Tabelle im Eintrag. `_known_acceptance_ids_locked` existiert
und ist das genannte Universum (`team-kits/kernel/dispatch.py:1903`, `known = _criteria_ids(root)`
plus Ursprungs-Hop plus `_amendment_criteria_locked`).

**Rot-zuerst, selbst nachgestellt** (`verify/s4/mut.py n1-origin-only`, Kopie `mut4` ohne `.git`;
die Auflösung auf den Ursprung verengt, indem `known = _criteria_ids(root)` durch `known = set()`
ersetzt wird):
```
test_an_empty_origin_excuses_the_step_while_the_root_criteria_measure_it
        clean=0  mutated=1 (1 failed in 1.95s)  restored=0
```
Der Test hält außerdem beide begrenzenden Fälle (keine Referenz, Referenz ins Leere) und sagt in
seinem Docstring, dass die Lease erteilt und erst der Spawn verweigert — die Unterscheidung, deren
Fehlen der Runde-3-Befund war.

## N2 — PASS

`tools/test_migrate_holes.py::test_only_a_hole_can_be_filed_as_one_from_the_command_surface` prüft
für den TSK-Fall jetzt den Verweigerungstext **und** dass kein `TSK` im Speicher steht
(`assert "a hole is a BUG" in order.stderr`, `assert not list(state.iter_active_items("TSK"))`).

**Rot-zuerst** (`verify/s4/mut.py n2-cli-removed`, `cli.py:1414-1415` entfernt):
```
test_only_a_hole_can_be_filed_as_one_from_the_command_surface
        clean=0  mutated=1 (1 failed in 1.41s)  restored=0
```
In Runde 3 war derselbe Schnitt **grün**. Warum er wirkt, ist unabhängig gemessen
(`verify/s4/clisite.py`, derselbe gültige TSK-Körper):
```
WITH the CLI check     rc=1 "a hole is a BUG and TSK is not one" | TSK items in the store: []
WITHOUT the CLI check  rc=1 Traceback ... KeyError: 'hole_number' | TSK items: ['TSK-0001'] | hole_number: [None]
```
Der Auftrag wird ohne die Prüfstelle geschrieben und das Flag still ignoriert; genau das sieht die
zweite Assertion jetzt. Welcher Beweis welche Stelle trifft, steht im Nacharbeitsbericht — der
Punkt aus Runde 3 ist damit erledigt.

## N3 — Verhalten PASS, Deckung FAIL (N3′)

**Verhalten geschlossen.** `backlog_types.hole_type()` liest jetzt `_contract_fields()`. Gemessen
(`verify/s4/n3b.py`, echte Unterprozesse gegen `mut4`):
```
== unmutated                                    rc=0  carriers(contract)=['BUG']  hole_type()=BUG
== A) PROC declares hole_number as REQUIRED     rc=1  IMPORT OK, dann
        AssertionError: 2 types declare hole_number ... ['BUG', 'PROC']
== B) PROC declares hole_number as OPTIONAL     rc=1  dieselbe AssertionError
== restored                                     rc=0  ['BUG'] / BUG
```
Beide Hälften des Vertrags lösen den lauten Abbruch aus, und er liegt am **Aufruf**, nicht am
Import — in Runde 3 lief Fall A noch mit rc 0 durch.

**N3′ (neuer Befund, nicht blockierend).** Die Korrektur ist von **nichts** gemessen, und der Test,
der sie halten soll, prüft noch die Quelle, von der sie weggezogen ist:

`tools/test_state.py:1240-1244`
```python
    from kernel.backlog_types import HOLE_NUMBER_FIELD, OPTIONAL_FIELDS, hole_type
    carriers = [item_type for item_type, fields in OPTIONAL_FIELDS.items()
                if HOLE_NUMBER_FIELD in fields]
    assert carriers == [hole_type()], carriers
```

Gemessen (`verify/s4/n3.py`, `hole_type()` auf die alte Quelle zurückgedreht, drei Suiten):
```
clean                      : (0, '122 passed in 13.97s')
reverted to OPTIONAL_FIELDS: (0, '122 passed in 11.88s')
restored                   : (0, '122 passed in 11.89s')
```
Ein Rückbau der N3-Korrektur bleibt also vollständig grün. Die Behauptung im Nacharbeitsbericht
(„rc 0 → rc 1") trifft auf die **Vertragsmutation** zu (ein zweiter Typ bekommt das Feld), nicht
auf die Korrektur selbst — und die Vertragsmutation wäre auch ohne die Korrektur an Fall B rot
geworden.

**Minimalfix:** in `tools/test_state.py` `_contract_fields()` statt `OPTIONAL_FIELDS` lesen und die
zweite Hälfte dazu — ein Typ, der das Feld als REQUIRED deklariert, muss `hole_type()` abbrechen
lassen. Dann misst der Test die Eigenschaft, die der Kommentar behauptet, statt der alten
Schreibweise.

## N4 — PASS

`stream-protocol.md:40` führt `_over_refusal` jetzt ausdrücklich als „in BEIDEN Ständen
unverändert" und in keiner der drei Listen. Mein eigener AST-Vergleich gegen ein reines 75a00d1
(`verify/s4/astdiff.py`, `base4` nach Rückwärts-Patch) ergibt unverändert **18 entfernt / 10 neu /
5 geändert** mit denselben fünf geänderten Definitionen wie in Runde 3 — die Nahttabelle deckt sich
damit vollständig.

---

## Paket, gegengemessen

| Prüfung | Ergebnis |
|---|---|
| `git apply --check` gegen 75a00d1 | **rc 0**, danach `git apply` sauber |
| Arbeitsbaum vs. gepatchtes 75a00d1 | identisch bis auf die drei `VERSION`-Dateien (`2026.09.05-5`) |
| Patch | **4262 Zeilen / 267 798 Bytes / 18 Dateien / 0 CR-Bytes**; „VERSION" nur zweimal in einer Prosazeile (H148), **kein VERSION-Hunk** |
| Quelldateien | 0 CR-Bytes in allen 18 |
| Bereich | alle 18 Dateien in `allowed_scope`; `kitupdate.py`, `gate_dispatch.py`, `.claude/hooks/gate_*.py`, `_harness.py`, `settings.json`, `constitution/**`, `agents/**`, `skills/**`, `templates/repo/**` unberührt; keine gespiegelte Datei geändert |
| AST-Vergleich `test_gates.py` | 18/10/5, unverändert gegenüber Runde 3 |
| `module::test`-Zitate in den 17 geänderten Python-Dateien | **keins unaufgelöst** |
| Lesende Suiten | **417 passed** (79,2 s) und **194 passed** (77,7 s) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Dokument | **9313** Zeilen, 143 `### H`-Einträge; Trockenlauf der Migration `143 written`, kein unbekanntes Urteilswort |
| `tools/migrate_holes.py` | byte-identisch zu Runde 3 — die Migrationsmaschine hat sich nicht bewegt |

**Nicht gemessen in dieser Runde** (Runde 3 gilt, gleicher Code): der vollständige
Migrationslauf 143/143 → 2441 Zeilen mit zweitem Lauf und `validate 0/66`, die sieben Gate-Knoten
gegen die migrierte Kopie, die AC-1/AC-2/AC-5-Regression. Dauerhaft nicht gemessen: die volle
Suite und `tools/test_hooks.py` (DEC-0050, Lieferkriterium des Merges), `gate_dispatch.py` von
office- und research-team als Prozess, der EINE schreibende Migrationslauf gegen den kanonischen
Zustand, die Wirkung von ~178 aktiven `BUG`-Items auf Board/`session_brief`/Rollups,
`tools/bump_kit_version.py` mit `docs/holes/`, die Laufzeit von `_iter_every_stored_item` bei jedem
`capture` in einem großen Speicher.

---

## Abschluss TSK-0122

Über vier Runden gemessen: **AC-1 PASS, AC-2 PASS, AC-3 PASS, AC-4 PASS, AC-5 PASS; Pflicht 6
PASS (bis auf N3′), Pflicht 7 PASS, Pflicht 8 PASS.**

Geschlossen und je einzeln von mir nachgestellt: die SR-Pflicht, die an der Schreibweise von
`derives_from` hing (F1); der fehlende Weg, ein neues Loch zu erfassen (F2); die Abhilfe, die
nichts tat (F3); die Nummernkollision, die einen Eintrag mit rc 0 löschte (F4); der Gate-Knoten,
der über leerem Bestand nichts maß (F6); `capture --hole` auf jedem Typ (R1); `--reindex`, das
einen vollen Index leerte (R2); und zuletzt die falsche Begrenzung in H155 (N1) und die ungemessene
CLI-Prüfstelle (N2).

**Offen als benannte Reste, mit Kette und Begrenzung im Dokument:** H154 (Migrationstür schreibt
einen Endzustand ohne Evidenz; zweite Klasse: ein unlesbares Loch-Item ist für alle Prüfer
unsichtbar), H155 (`class` ist Freitext; zweite Klasse: leerer Ursprung + Referenz der Wurzel),
H156 (die Überlappungsverweigerung sieht nur laufende Leases; zweite Klasse: `--worktree` prüft nur
die Existenz eines Verzeichnisses).

**Vor dem Merge zu erledigen:** N3′ (zwei Zeilen in `tools/test_state.py`) und der EINE schreibende
Migrationslauf aus einer Shell außerhalb von Claude Code — bis dahin sind alle sieben Gate-Knoten
im Hauptrepo rot, was Protokoll §7 korrekt so sagt.

**Eigene Irrtümer über die vier Runden, benannt:** F13 hatte ich in Runde 1 als offen gemeldet,
obwohl der Satz nur über zwei Zeilen umbrochen war. In Runde 3 war meine erste Lesart der
R1-Rot-zuerst-Behauptung zu eng — an der Kernel-Stelle reproduziert die Mutation, und das ist die
naheliegende Lesart. Beide Male hatte der Umsetzer recht.
