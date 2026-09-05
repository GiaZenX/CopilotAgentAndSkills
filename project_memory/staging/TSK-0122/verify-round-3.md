# TSK-0122 (PR-0005, Strom G4-2) — Prüfbericht Runde 3 (Nacharbeit 2)

Rolle: `harness-verifier`. Read-only am Repo; alles in **frischen** Kopien unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0122/verify/`: `wt3` (Arbeitsbaum ohne `.git`),
`base3` (75a00d1), `mut3` (Mutationskopie), `mig3` (frisch migriert), `pilots_r3/**`.

**URTEIL: FAIL — kein blockierendes Loch im Code mehr, aber Pflicht 6 ist verletzt.**
R1 und R2 sind geschlossen und von mir einzeln nachgemessen; AC-1 bis AC-5 halten allen Angriffen
stand. Was FAIL macht, sind zwei Sätze und eine Deckungslücke: der Löcher-Eintrag **H155** und der
Docstring, aus dem er stammt, behaupten eine Begrenzung, die die Messung **in beide Richtungen**
widerlegt; und die Prüfstelle, die diese Runde neu eingebaut hat (die CLI), wird von ihrem eigenen
benannten Test nicht gemessen.

| | R1 | R2 | R3 |
|---|---|---|---|
| AC-1 | PASS | PASS | **PASS** |
| AC-2 | PASS | PASS | **PASS** |
| AC-3 | FAIL | PASS | **PASS** (Verhalten) — der benannte Rest ist falsch, siehe N1 |
| AC-4 | FAIL | FAIL | **PASS** |
| AC-5 | PASS | PASS | **PASS** |
| Pflicht 6 | FAIL | teilweise | **FAIL** — N1, N2 |
| Pflicht 7 | FAIL | PASS m. K. | **PASS** |
| Pflicht 8 | PASS | PASS m. K. | **PASS** |

---

## Befunde

### N1 (FAIL-Grund) — H155 und der Docstring behaupten eine Begrenzung, die es so nicht gibt, und benennen einen Rest, den es nicht gibt

`docs/POST_V2_WISHLIST.md:9269` (H155, zweite Restklasse) und
`team-kits/kernel/dispatch.py:2013-2016`:

> „`dispatch.validate_dispatch` löst jede `acceptance_ref` gegen den **Ursprung** auf und verweigert
> eine, die ins Leere zeigt — der Rest trifft also nur den Auftrag, dessen Ursprung eine leere
> Liste trägt **UND** der selbst keine Referenz nennt."
>
> „What the two together do NOT catch is the order whose origin carries an EMPTY list AND whose own
> `acceptance_refs` are empty."

Gemessen (`verify/s3/r3.py`, gescaffoldete Piloten, der ausgelieferte, unberührte Kit-Haken
`dev-team/hooks/gate_dispatch.py` als echter Prozess):

```
BUG criteria filled, refs AC-1 (in bug and root)   owed=False lease GRANTED | hook rc=0
BUG criteria EMPTY,  refs AC-1 (only in root)      owed=False lease GRANTED | hook rc=0
BUG criteria EMPTY,  refs AC-9 (nowhere)           owed=False lease GRANTED | hook rc=2  "references criteria that exist nowhere: AC-9"
BUG criteria filled, refs AC-9 (nowhere)           owed=False lease GRANTED | hook rc=2  "references criteria that exist nowhere: AC-9"
BUG criteria EMPTY,  refs []                       owed=False lease GRANTED | hook rc=2  "carries no acceptance_refs -- a task nobody can check against"
```

Beide Sätze sind falsch, und zwar gegenläufig:

1. **Der benannte Rest existiert nicht.** Ein Auftrag, dessen Ursprung eine leere Liste trägt und
   der selbst keine Referenz nennt, wird **rc 2** abgewiesen („carries no acceptance_refs"). Genau
   der Fall, den H155 als das Übrigbleibende ausweist, ist der einzige der fünf, der zusätzlich
   noch an einer zweiten Prüfung scheitert.
2. **Der Rest, den es wirklich gibt, steht nirgends.** Er ist die Zeile 2: Ursprung mit leerer
   Liste, `acceptance_refs` lösen gegen die **WURZEL** auf → rc 0. Die Auflösung geht also nicht
   „gegen den Ursprung", wie beide Texte sagen, sondern akzeptiert auch die Kriterien des Ziels —
   und damit wird ein Auftrag gegen das Ziel gemessen, dessen Architektenschritt wegen des BUG
   übersprungen wurde.

Das ist die Hausregel „kein Kommentar darf Schutz behaupten, den der Code nicht baut", und sie
schneidet hier in beide Richtungen. Ein Löchereintrag, dessen Begrenzung falsch ist, ist teurer als
keiner: er ist der Datensatz, mit dem das Projekt diese Lücke führt.

**Minimalfix:** beide Stellen auf die gemessene Kette umschreiben — verweigert wird eine Referenz,
die **nirgends** auflöst (Ursprung oder Wurzel), und leere `acceptance_refs`; der Rest ist der
Auftrag, dessen Ursprung eine leere Liste trägt und dessen Referenzen gegen die WURZEL auflösen.
Ein roter Test, der genau diese Zeile hält, gehört dazu.

### N2 (FAIL-Grund) — die neue CLI-Prüfstelle wird von ihrem eigenen benannten Test nicht gemessen

`team-kits/kernel/cli.py:1414-1415`. Der Kommentar dort sagt, warum die Stelle existiert:

> „ASKED BEFORE THE PRODUCER IS CHOSEN, because `capture TSK` does not go through `state.capture`
> at all -- the flag would be silently ignored there."

Gemessen (`verify/s3/mut.py cli-removed`, Mutation in `mut3` ohne `.git`, je Lauf/Mutation/Rückbau):
```
== cli-removed (team-kits/kernel/cli.py)
   test_only_a_hole_can_be_filed_as_one_from_the_command_surface   clean=0 mutated=0 (1 passed) restored=0
   test_only_the_type_a_hole_is_can_be_captured_as_one             clean=0 mutated=0 (1 passed) restored=0
```

Die Stelle ist **tatsächlich tragend** — ohne sie ändert sich das Verhalten
(`verify/s3/clisite.py`, derselbe gültige TSK-Körper, den der Test benutzt):
```
WITH the CLI check     capture TSK --hole -> rc=1  "a hole is a BUG and TSK is not one"
                       TSK items in the store: []
WITHOUT the CLI check  capture TSK --hole -> rc=1  Traceback ... KeyError: 'hole_number'
                       TSK items in the store: ['TSK-0001'] | any hole_number: [None]
```
Der Auftrag **wird geschrieben**, das Flag wird still ignoriert, und der von-Null-verschiedene
Rückgabecode kommt aus einem ungefangenen `KeyError` in `cli.py:1434`
(`str(item[HOLE_NUMBER_FIELD])` in der stdout-Zeile), nicht aus einer Verweigerung. Der Test prüft
für den TSK-Fall nur `returncode != 0` und ist damit durch den Absturz erfüllt — er kann für die
Stelle, für die er geschrieben wurde, nicht scheitern. Das ist genau die Klasse, die Pflicht 6
benennt („a named test must be able to fail").

**Minimalfix:** im TSK-Zweig zusätzlich auf den Refusaltext prüfen (`"a hole is a BUG" in stderr`)
und darauf, dass **kein** `TSK` im Speicher steht.

**Zur Rot-zuerst-Behauptung des Umsetzers, präzise:** „die Ableitung durch die alte Aufzählung
ersetzt → der Prozess-Test rc 1" **reproduziert an der Kernel-Stelle** — ersetzt man in
`state.assert_capturable_as_hole` `hole_type()`/`!=` durch `"BUG"`/`== "TSK"`, werden **beide**
Knoten rot (gemessen, `verify/s3/mut2.py`). An der Stelle, an der der beanstandete Defekt der
Runde 2 wirklich saß — in der CLI —, bleibt derselbe Austausch **grün** (gemessen,
`verify/s3/mut.py old-enumeration`: clean=0, mutated=0). Beides ist wahr; der Bericht sollte sagen,
welche Stelle gemeint ist.

### N3 (Rest oder Einzeiler) — `hole_type()` liest eine schmalere Quelle, als sein Satz sagt

`team-kits/kernel/backlog_types.py:539` ff. Der Docstring sagt „read off the field contract:
exactly one type declares `HOLE_NUMBER_FIELD`"; der Code liest `OPTIONAL_FIELDS.items()`, während
die Schwesterableitung derselben Runde (`dispatch._carries_its_own_criteria`) `_contract_fields()`
liest — die Vereinigung aus `REQUIRED_FIELDS`, `OPTIONAL_FIELDS` und `kernel/schemas/`.

Gemessen, `hole_number` einem zweiten Typ in **`REQUIRED_FIELDS`** gegeben:
```
rc 0
hole_type()= BUG
contract carriers= ['BUG', 'PROC']
```
Der laute Abbruch, der die Weitung verhindern soll, feuert also nicht, wenn die zweite Deklaration
außerhalb von `OPTIONAL_FIELDS` steht. Heute stimmen beide Quellen überein (`['BUG']`), die Lücke
ist also potenziell, nicht aktiv.
**Minimalfix:** `_contract_fields()` statt `OPTIONAL_FIELDS` — dieselbe Quelle wie die
Schwesterableitung.

### N4 (Kleinigkeit) — eine Nennung in der korrigierten Nahttabelle stimmt nicht

`stream-protocol.md:39` führt unter ENTFERNT „`_over_refusal`-Vorgänger". Gemessen: `_over_refusal`
existiert in 75a00d1 **und** im Paket und steht in keiner der drei AST-Listen (unverändert). Der
Rest der Tabelle deckt sich exakt mit meinem Vergleich.

---

## Ausdrückliche Negativbefunde

### R1 geschlossen — gemessen als Prozess, gegen eine frische Kopie UND gegen die migrierte

`verify/s3/r1.py` (frischer Pilot, echter `python -m kernel.cli`):
```
next_hole_number before anything: H1
FR --hole    rc=1  a hole is a BUG and FR is not one: ...
DEC --hole   rc=1  a hole is a BUG and DEC is not one: ...
TSK --hole   rc=1  a hole is a BUG and TSK is not one: ...
EVD --hole   rc=1  ...
SR --hole    rc=1  ...
next_hole_number after the refusals: H1
BUG --hole  rc=0 out='BUG-0001 OPEN H1'
next_hole_number after it: H2
lower-case 'bug --hole'  rc=2  (argparse choices)
body is a LIST           rc=2  "an item is a JSON OBJECT of field -> value"
```
`verify/s3/mig_probe.py` gegen die **migrierte** Kopie: `FR`, `DEC`, `TSK` je rc 1,
`next_hole_number` bleibt `H157` vor und nach den drei Versuchen; die sieben Gate-Knoten danach
**7 passed**.

**Die Ableitung, angegriffen** (`verify/s3/holetype.py`): ein zweiter Typ mit
`HOLE_NUMBER_FIELD` in `OPTIONAL_FIELDS` →
```
   import               rc=0  IMPORT OK
   hole_type()          rc=1  AssertionError: 2 types declare hole_number ... ['BUG', 'PROC']
   capture BUG --hole   rc=1  (dieselbe AssertionError)
   capture CR --hole    rc=1  (dieselbe)
   validate             rc=1  (dieselbe)
```
Der Abbruch liegt also **am Aufruf, nicht am Import**, ist laut, und nimmt `validate` mit — die
fail-closed-Richtung. (Er ist ein explizites `raise AssertionError`, kein `assert`, also überlebt
er auch `python -O`.)

**Rot-zuerst, selbst nachgestellt:**

| Mutation | Knoten | sauber | mutiert | zurück |
|---|---|---|---|---|
| Kernel-Prüfung entfernt | `test_only_the_type_a_hole_is_can_be_captured_as_one` | rc 0 | **rc 1** | rc 0 |
| Kernel-Prüfung entfernt | `test_only_a_hole_can_be_filed_as_one_from_the_command_surface` | rc 0 | rc 0 (die CLI fängt es) | rc 0 |
| Kernel-Ableitung → alte Aufzählung | beide Knoten | rc 0 | **rc 1 / rc 1** | rc 0 |
| CLI-Prüfung entfernt | beide Knoten | rc 0 | rc 0 / rc 0 → **N2** | rc 0 |
| `_write_index`-Verweigerung ausgeschaltet | `test_an_empty_store_does_not_empty_a_full_index` | rc 0 | **rc 1** | rc 0 |

`capture_migrated_hole` erzeugt weiterhin `BUG`s: die Migration schreibt **143 written, 143 prose
files**, rc 0.

### R2 geschlossen — beide Enden gemessen

`verify/s3/r2.py` gegen die migrierte Kopie:
```
0) rows in the document: 143 | holes in the store: 143
A) EMPTY store over a full document:  rc=1  "the store under this --root carries no hole at all,
   and the document carries 143 ... would delete every pointer with a success message"
   rows after: 143
B) store one hole SMALLER (142) than the document (143): rc=0 "index rewritten ... 142 hole(s)"
   rows after: 142
C) capture BUG --hole (store 144 vs document 143):       rc=0 "index rewritten ... 144 hole(s)"
   rows after: 144
D) store full, document has no '## 12.' section:         rc=1 "no '## 12.' section ... nothing to migrate"
```
Also: schrumpfen ✔, wachsen ✔, leeren ✘, fehlender Abschnitt ✘ — genau die enge Regel, die der
Docstring behauptet.

### R3–R7 geschlossen (bis auf N1)

- **R3** Der Docstring fragt jetzt „CAN an item of this type hold …" und trennt Typ- von Wertfrage;
  die Verhaltensmessung bestätigt die Typebene (`BUG` mit leeren Kriterien befreit weiterhin).
  Was daran noch falsch ist, ist N1 — nicht die Umstellung.
- **R4** Alle sechs Zahlen nachgemessen und richtig: Nahttabelle und §9 `2026.09.05-4` (Dateien:
  `2026.09.05-4`), `143 written / 143 prose files`, `document lines: 2441` bei einem
  ausgelieferten Dokument von **9300** Zeilen (gemessen), „die Einträge des ausgelieferten
  Dokuments (heute 143)", §7 „**alle sieben** Gate-Knoten rot", Patch **4162 Zeilen** (`wc -l`).
- **R5** Nahttabelle deckt sich mit meinem eigenen AST-Vergleich (`verify/s3/astdiff.py`,
  `base3` = pristine 75a00d1): **18 entfernt / 10 neu / 5 geändert**, und die fünf geänderten sind
  exakt die genannten (`_anchors`, `test_every_reference_to_a_measurement_leads_to_one`,
  `test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`,
  `test_every_cell_a_closed_hole_names_is_one_the_table_carries`,
  `test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`);
  `TABLE_TEST`, `TILDE_TEST`, `CELLS_RX`, `SUBJECTS_RX` byte-identisch; `_assert_it_is_the_same_hole`
  richtig nach `tools/migrate_holes.py` verwiesen. Einzige Unschärfe: N4.
- **R6** „9 SRs against 120 work orders" ist entfernt (gemessen).
- **R7** Der stderr-Hinweis lautet jetzt
  `tools/migrate_holes.py --root <state> --reindex`, ohne `--related-pr`.

### AC-Regression gegen den neuen Stand

**AC-3** (`verify/s3/ac3.py`): A REFUSED, B (PROPOSED SR als Ursprung) REFUSED, C (ACCEPTED SR)
GRANTED, D GRANTED, E `[PR, PROPOSED SR]` REFUSED, F BUG GRANTED, G BUG mit leeren Kriterien
GRANTED (N1), H/I exempt GRANTED, J unbekannte Klasse REFUSED, K/L REFUSED, M und N bei der
Erstellung verweigert.
**AC-1**: alle sieben Fälle wie in Runde 1/2, `delivery={}` / `confirmation={'test': 'pass'}`,
dritte Frage `ValueError`.
**AC-2**: alle vier FR-Schreibweisen REFUSED, der bereits triagierte Wunsch mit
„FR-0001 has already been triaged and became PR-0001", Zähler 35, Validator-Warnung nur aktiv.
**AC-5**: Naht beidseitig GRANTED, einseitig REFUSED, außerhalb REFUSED, disjunkt GRANTED,
abgelaufene Lease GRANTED; `--worktree` ohne Verzeichnis und mit Dateipfad REFUSED, TSK bleibt
READY, **keine** Lease-Datei geschrieben; zwei Leases auf einem Baum erlaubt (in H156 als kein Rest
benannt).

### Paket

18 Dateien, identische Liste wie in Runde 1/2, alle in `allowed_scope`; `kitupdate.py`,
`gate_dispatch.py`, `.claude/hooks/gate_*.py`, `_harness.py`, `settings.json`, `constitution/**`,
`agents/**`, `skills/**`, `templates/repo/**` unberührt; keine gespiegelte Datei geändert.
`git apply --check` gegen 75a00d1 **rc 0**; Arbeitsbaum == 75a00d1 + Patch + genau die drei
`VERSION`-Dateien (`2026.09.05-4`). **Patch 4162 Zeilen, 0 CR-Bytes**, die 18 Quelldateien
ebenfalls 0; einziges „VERSION" im Patch ist Prosa in H148. Nur H154–H156 als neue Nummern.
Migration Ende zu Ende gegen `mig3`: **143 written / 143 prose files**, 9300 → **2441** Zeilen,
zweiter Lauf **1,785 s, 0 written**, SHA256 identisch, `validate` **0 Fehler / 66 Warnungen**,
Gate-Knoten **7 passed**; über leerem Bestand **7 failed**. Lesende Suiten **417 passed** (78,9 s)
und **193 passed** (76,3 s), Selbstprüfung `test_gates -k "claims_in_its_own_prose or
names_only_code_that_exists"` **2 passed**; `ruff check .` „All checks passed";
`tools/validate.py` „all structural checks passed". **Kein `module::test`-Zitat in den 17
geänderten Python-Dateien bleibt unaufgelöst.**

### Nicht gemessen

- Die volle Suite und `tools/test_hooks.py` (DEC-0050: Lieferkriterium des Merges).
- Der Rest von `.claude/hooks/test_gates.py` außerhalb der beiden `-k`-Auswahlen.
- `gate_dispatch.py` von office-team und research-team als Prozess (nur dev-team gemessen).
- Der EINE schreibende Migrationslauf gegen den kanonischen Zustand (hier verboten).
- Wirkung von ~178 aktiven `BUG`-Items auf Board, `session_brief`, Rollups.
- `tools/bump_kit_version.py` / der Kit-Hash mit `docs/holes/`.
- Laufzeit von `_iter_every_stored_item` bei jedem `capture` in einem großen Speicher.
- Ob `related_pr: PR-0003` für 143 Löcher die Abnahme dieses Ziels beeinflusst.

---

## Einordnung

**Kein blockierendes Loch im Code.** Die Angriffskette, die in Runde 2 innerhalb einer Sitzung
durchlief (`capture DEC --hole` → roter Gate-Knoten), ist geschlossen und von mir gegen beide
Bestände nachgemessen.

**Rundenblockierend im Sinne der Hausregeln bleiben N1 und N2** — beide billig: ein Absatz in
H155 plus derselbe Absatz im Docstring auf die gemessene Kette umschreiben, und zwei Zeilen mehr
Assertion im Prozess-Test. N1 fällt unter „kein Kommentar/Dokument darf Schutz behaupten, den der
Code nicht baut", N2 unter „ein benannter Test muss scheitern können".

**Als benannter Rest oder Einzeiler:** N3 (`hole_type()` liest `OPTIONAL_FIELDS` statt
`_contract_fields()`). **Reine Textkorrektur:** N4.

**Eigene Irrtümer, benannt:** In Runde 1 hatte ich F13 als offen gemeldet, obwohl der Satz nur über
zwei Zeilen umbrochen war — der Umsetzer hatte recht. In dieser Runde hat sich meine erste Lesart
der Rot-zuerst-Behauptung zu R1 als zu eng erwiesen: an der Kernel-Stelle reproduziert die
Mutation, und das ist die naheliegende Lesart von „die Ableitung". Der Befund N2 bleibt davon
unberührt, weil er eine andere Stelle misst.
