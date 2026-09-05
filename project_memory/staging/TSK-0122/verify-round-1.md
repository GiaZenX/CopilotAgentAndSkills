# TSK-0122 (PR-0005, Strom G4-2) — Prüfbericht Runde 1

Rolle: `harness-verifier`. Read-only am Repo; gemessen in Kopien unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0122/verify/` (`wt` = Arbeitsbaum ohne `.git`,
`base` = 75a00d1, `mut` = Mutationskopie, `mig` = migrierte Kopie, `pilots*` = gescaffoldete
Piloten, `store75` = `project_memory` bei 75a00d1).

**URTEIL: FAIL.** AC-1, AC-2 und AC-5 halten jedem meiner Angriffe stand. AC-3 ist gebaut, aber
gegen die Schreibweise, die die Kits selbst vorschreiben, wirkungslos — und der Satz, der dazu
wörtlich an G4-3 geht, behauptet Schutz, den der Code nicht baut. AC-4 ist gebaut und gemessen
korrekt, hat aber keinen ausführbaren Weg für ein NEUES Loch und verliert bei einer
Nummernkollision im Merge stillschweigend einen Eintrag.

---

## Blockierend

### F1 — AC-3: die SR-Pflicht greift bei 3 von 120 Aufträgen, und der G4-3-Satz behauptet das Gegenteil

`team-kits/kernel/dispatch.py:1975`

```python
    origins = {str(one) for one in field_elements(task.get("derives_from"))}
    if origins - {str(root.get("id"))}:
        return False
```

Die Pflicht wird für JEDEN Auftrag übersprungen, dessen `derives_from` etwas anderes als die Wurzel
nennt — auch für einen SR unter derselben Wurzel, und ohne dessen Status anzusehen.

Gemessen (`verify/s/ac3.py`, echte Kernel-Aufrufe, gescaffoldete Piloten):

```
== normal_sr_proposed        | class=normal sr=PROPOSED derives=PR-0001  -> REFUSED
== derives_from_proposed_sr  | class=normal sr=PROPOSED derives=SR-0001  -> GRANTED
```

Derselbe Zustand, nur die Schreibweise von `derives_from` unterschiedlich: einmal verweigert,
einmal erteilt. `derives_from = [PR-0001, SR-0001]` ist ebenfalls **GRANTED**
(`verify/s/ac3b.py`).

Wie oft das trifft, gemessen über `store75` (`verify/s/decnums.py`):

```
TSK derives_from prefix at 75a00d1: {'PR': 3, 'SR': 29, 'BUG': 53, 'FR': 35, ...}
```

3 von 120. Und `team-kits/dev-team/skills/backend-developer/SKILL.md:15` schreibt genau die
Schreibweise vor, die die Pflicht ausschaltet: *„Your `TSK` — `derives_from` names the SR"*
(ebenso `frontend-developer/SKILL.md:16`). In einem dev-team-Projekt feuert die Regel damit nie.

Der Buchstabe von DEC-0072 (c) deckt das ab („die Pflicht gilt nur, wenn die TSK von ihrem
Wurzelziel selbst ableitet"). Blockierend ist deshalb nicht die Abweichung von der Entscheidung,
sondern zweierlei:

1. **Der Satz, der wörtlich an G4-3 geht** (Protokoll §8 Nr. 3) ist falsch:
   *„… wird erst dispatcht, wenn unter demselben Ziel eine technische Anforderung (SR) im Status
   ACCEPTED hängt. Nicht gefragt werden Ziele der Klasse `small` und `technical_enabler` sowie
   Aufträge, die von einem BUG, CR oder EXP ableiten."* — Gegenbeispiel oben: ein Auftrag unter
   einem PROPOSED SR ist weder `small`/`technical_enabler` noch BUG/CR/EXP und wird dispatcht.
   Dieser Satz soll in drei Verfassungen. Hausregel 3.
2. **Die gemessene Wirkungslosigkeit steht in keinem Loch.** H155 nennt nur die Freitext-Klasse.
   Der eigentliche Mechanismus — *die Pflicht hängt an der Schreibweise von `derives_from`, nicht
   am Zustand des Architektenschritts* — ist gemessen und nicht aufgeschrieben.

Auch der Docstring darüber ist eine Aufzählung statt einer Definition
(`team-kits/kernel/dispatch.py:2005`: „a task whose `derives_from` names a BUG, a CR or an EXP"),
während der Code „alles außer der Wurzel" meint.

**Minimalfix:** die Ausnahme an das binden, was sie meint — ein Ursprung, der selbst ein
Architekturartefakt ist (`SR`), erfüllt die Pflicht nur im akzeptierten Status; ein Ursprung vom
Typ BUG/CR/EXP befreit. Plus H157-Eintrag (Nummer außerhalb der Reservierung → gehört in die
Nacharbeit abgestimmt) und den korrigierten G4-3-Satz.

### F2 — AC-4: es gibt keinen Weg, ein NEUES Loch zu erfassen

`tools/migrate_holes.py:253` schreibt in den GENERIERTEN Index des Dokuments:

> „Neue Nummern vergibt der Kernel (`capture --hole`), nicht die Hand."

Gemessen im migrierten Repo (`verify/mig`):

```
$ PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory capture BUG --hole
python scripts/harness.py: error: unrecognized arguments: --hole
```

`cli.py` kennt kein `--hole` (der einzige CLI-Zusatz dieser Runde ist `dispatch --worktree`).
`state.capture(..., hole=True)` ist ausschließlich aus Python erreichbar. Damit behauptet ein
generiertes, ausgeliefertes Dokument ein Kommando, das es nicht gibt (Hausregel 3), und der
einzige tatsächlich funktionierende Weg für ein neues Loch ist der handvergebene `### H<n>`-Eintrag
— genau der Defekt, gegen den FR-0087/DEC-0073 geschrieben wurden.

**Minimalfix:** `capture --hole` in `cli.py` (in `allowed_scope`), oder den Satz im Index auf den
Weg ändern, der wirklich existiert.

### F3 — AC-4: der Prüfer nennt eine Abhilfe, die nichts tut

`.claude/hooks/test_gates.py:4664-4671`, Assertionstext:

> „Remedy: re-run `python tools/migrate_holes.py --root project_memory --related-pr <goal>
> --apply`, which rewrites this section from the store."

Gemessen (`verify/s/ac4index.py`) auf einer migrierten Kopie, in der ein Loch im Speicher steht,
das der Index nicht führt:

```
store holes: 144
H151 in store: True
H151 in the document index: False
the remedy command: 0   0 written, 0 already in the store, 0 prose files
H151 in the document index AFTER the remedy: False
document index == generated index: False
```

Ursache: `tools/migrate_holes.py:281` — `if not entries: return report`. Der Neu-Schrieb des
Abschnitts wird nur erreicht, solange das Dokument noch `### H<n>`-Überschriften trägt. Nach der
einmaligen Migration ist er tot. Folge: jedes Loch, das über den Kernel erfasst wird (also der laut
F2 vorgesehene Weg), macht `test_the_hole_index_in_the_document_is_the_one_the_items_generate`
dauerhaft rot, ohne dass ein Kommando das repariert.

**Minimalfix:** die Index-Regeneration aus der Eintrags-Schleife herauslösen (`--reindex` oder
bedingungsloser Neu-Schrieb am Ende von `migrate()`).

### F4 — AC-4: eine Nummernkollision im Merge löscht einen Eintrag mit rc 0

`tools/migrate_holes.py:301-304` (`existing = state.hole_by_number(name)` → `report["already"]`,
`continue`).

Gemessen (`verify/s/ac4door2.py`) gegen die migrierte Kopie: der Speicher führt H151, das Dokument
bringt einen INHALTLICH ANDEREN H151-Eintrag im heutigen Format — genau die Lage, die Protokoll §7
für den Merge beschreibt (vier Ströme, handreservierte Nummern):

```
store already carries H151: BUG-0235 | eine Luecke, die ein anderer Strom gemessen hat
rc: 0
stdout: 0 written, 1 already in the store, 0 prose files
index rows naming H151: 1
the SECOND entry's prose survived anywhere: False
```

Der zweite Eintrag wird beim Neu-Schrieb des Abschnitts aus dem Dokument entfernt, in keine
`docs/holes/`-Datei geschrieben und in kein Item — rc 0, kein Wort. Das ist Datenverlust an dem
einen Lauf, auf dem das ganze AC-4 steht.

Der `already`-Zweig wird für den WIEDERAUFNAHME-Fall gebraucht; er unterscheidet ihn aber nicht vom
Kollisionsfall.

**Minimalfix:** `hole_by_number` liefert das Item; Titel/`observed` gegen den gelesenen Eintrag
vergleichen und bei Abweichung mit `SystemExit` verweigern statt zu überspringen.

---

## Mittel

### F5 — AC-2: die Zahl im Kommentar ist falsch über die eigene Funktion

`team-kits/kernel/report.py:2016`: „on 75a00d1 this repository holds 21 such work orders".

Gemessen (`verify/s/count21.py`) gegen `store75`:

```
tasks_under_an_inbox_item() at 75a00d1 = 35
TSK files: 120 | product_requirement=FR: 21 | derives_from=FR: 35
```

`_inbox_origins_of` liest BEIDE Elternfelder, die Funktion liefert 35. Zwei Zeilen darüber steht
„The number belongs in a round's report, not in a second comment here" — und dann steht sie da.
(Item-AC-2 verlangt „counts TSKs whose root is an FR (21 today)"; geliefert ist die breitere
Zählung. Das ist besser, aber dann muss die Zahl weg oder stimmen.)

### F6 — AC-4: der siebte Gate-Knoten kann nicht scheitern

Protokoll §4: „Solange er nicht gelaufen ist, sind die sieben umgestellten Gate-Knoten im
Hauptrepo rot."

Gemessen gegen `verify/wt` (unmigrierter Bestand):

```
6 failed, 1 passed, 483 deselected in 32.49s
```

Grün bleibt `test_every_reference_to_a_measurement_leads_to_one`. Fünf Geschwister tragen ein
`assert holes, "no hole item in ..."`; dieser nicht. Die Zeichenkette `assert holes` steht in
seinem Körper nur als `assert holes & set(...)` — dort ist `holes` bereits durch
`holes, sections = _anchors(here)` überschrieben. Über einem leeren Bestand läuft die
Löcher-Schleife null Mal und der Knoten misst nichts.

**Minimalfix:** dasselbe `assert holes` wie bei den Geschwistern, und die überschattende Variable
umbenennen.

### F7 — drei Zeiger auf eine Funktion, die es nicht gibt

`report._check_triage_result_link` existiert nirgends; die Funktion heißt `_check_fr_result_link`
(`team-kits/kernel/report.py:2268`). Zitiert an:

- `team-kits/kernel/backlog_types.py:954`
- `team-kits/kernel/dispatch.py:152`
- `team-kits/kernel/report.py:2023`

(gemessen mit einem AST-Index über alle definierten Namen, `verify/s/cites2.py`).

### F8 — ein benannter Test, den es nicht gibt

`team-kits/kernel/state.py:1016` zitiert
`tools/test_state.py::test_a_second_migration_run_writes_nothing`. Über den ganzen Baum: kein Test
dieses Namens. Gemeint ist offenbar
`tools/test_migrate_holes.py::test_a_second_run_over_the_same_document_writes_nothing`.
Ein benannter Test, der nicht auflösbar ist, ist die teurere der beiden Deckungsbehauptungen
(Item-Pflicht 6).

### F9 — eine Behauptung, die DEC-0071 aufgehoben hat, steht unverändert da

`team-kits/kernel/backlog_types.py:460-462`:

> „ONLY THE PASS SIDE IS FILTERED … so a `pass` from a selection opens nothing."

Gemessen (`verify/s/ac1.py`): eine bestandene `selection`, die den BUG nennt, lässt
`FIXED -> VERIFIED` laufen. Sie öffnet also etwas. Die Datei wurde in dieser Runde geändert, der
Absatz nicht — und DEC-0071 wird dort nicht genannt.

### F10 — der Loch-Vertrag gilt nur auf der Leseseite

`team-kits/kernel/backlog_types.py:518-525` sagt, ein Loch schulde `expected`, `repro` und
`acceptance_criteria` NICHT. Gemessen:

```
kernel.state.StateError: capture BUG is missing required fields: expected, repro,
acceptance_criteria (spec II.2 Pflichtfelder).
```

aus `state.capture({...}, hole=True)`. `capture_preflight` fragt `REQUIRED_FIELDS["BUG"]`, nicht
`required_fields_of`. Nur `capture_migrated_hole` (das an `capture_preflight` vorbeigeht) und
`report.validate_state` kennen den engeren Vertrag. Der Kommentar beschreibt eine Hälfte als das
Ganze.

### F11 — die Nahttabelle ist über die geteilte Datei unvollständig

AST-Vergleich `.claude/hooks/test_gates.py` 75a00d1 → Paket (`verify/s/astdiff.py`):
18 Definitionen entfernt, 10 neu, **5 geändert**. Protokoll §1 nennt „ausschließlich den Block …
plus zwei Zeilen in `_anchors` und eine in `test_every_reference_to_a_measurement_leads_to_one`".

Nicht genannt: `test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`
(Docstring, 2 Zeilen). Und `test_every_reference_to_a_measurement_leads_to_one` ist nicht „eine
Zeile", sondern 3 entfernt / 7 hinzugefügt. G4-1 und G4-4 teilen sich diese Datei.

### F12 — die G4-3-Naht nennt die fünf Dateien mit dem toten Testzitat nicht

`test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` ist in diesem Strom umbenannt und
existiert nicht mehr. Zitiert wird der Name noch in:

- `team-kits/dev-team/constitution/AGENTS.md:219`
- `team-kits/office-team/constitution/AGENTS.md`
- `team-kits/research-team/constitution/AGENTS.md`
- `team-kits/dev-team/skills/parallel-streams/SKILL.md:86`
- `team-kits/research-team/skills/parallel-streams/SKILL.md`

Protokoll §8 übergibt drei SÄTZE; die Ersatzsätze tragen kein Testzitat, also überlebt das tote
Zitat, wenn G4-3 nur die Sätze tauscht. Der dev-Skill sagt dort außerdem: „If that test ever goes
red, a refusal has been built and this paragraph is the one to correct" — der Test wurde nicht rot,
er wurde umbenannt, der Stolperdraht hat nie ausgelöst.

### F13 — das Merge-Kommando aus §7 ist aus einer Sitzung heraus verweigert

Gemessen im Hauptrepo:

```
$ cd "C:/Offline Repos/AgentAndSkills" && PYTHONPATH=team-kits python -B tools/migrate_holes.py \
    --root project_memory --related-pr PR-0003
[harness gate] no tool call in this repo may write C:/Offline Repos/AgentAndSkills\project_memory.
```

(Dieselbe Verweigerung trifft auch `python -B -m kernel.cli --root project_memory validate`, also
jeden Schreibweg auf den kanonischen Zustand — das ist Gate 1 wie in CLAUDE.md beschrieben und kein
Defekt dieses Stroms.) Das Protokoll stellt die Zeile als „einmal, aus der Repo-Wurzel" dar, ohne zu
sagen, dass sie aus einer Shell AUSSERHALB von Claude Code laufen muss. Da sechs Gate-Knoten bis
dahin rot sind, gehört das in §7.

---

## Klein

- **F14** Zahlen in Kommentaren, die dieser Merge selbst ungültig macht:
  `backlog_types.py:554` („91 `BUG` records" → nach der Migration 234; gemessen: 178 aktiv + 56
  archiviert), `backlog_types.py:520-521` („140 entries … 140/121/85"), `state.py:1031` („the 140
  entries"), H154 („140 Eintraege"). Gemessen liefert das AUSGELIEFERTE Dokument **143** Einträge
  und 143 Items (`143 written, 0 already in the store, 143 prose files`). Das Protokoll sagt 140.
- **F15** `report.py:1491` behauptet, die Bestätigungsfrage sei „bounded by the ONE item the caller
  names". Gemessen (`verify/s/claims.py`): eine bestandene `selection`, die eine TSK nennt, die
  unter dem BUG hängt, lässt den BUG laufen — `evidence_covers` läuft unverändert über die
  Nachfahren. DEC-0071 sagt das ehrlich, der Kommentar nicht.
- **F16** `dispatch.py:2005` und `report.py:2023`/`backlog_types.py:954`: Aufzählung statt
  Definition (siehe F1, F7).
- **F17** Keine der beiden Dateien, die DEC-0071 und DEC-0072 verkörpern, nennt deren Nummer:
  `report.py` und `dispatch.py` enthalten weder `DEC-0071` noch `DEC-0072`. DEC-0071 selbst sagt in
  `consequences`: „die Nummer dieser Entscheidung steht an beiden Stellen". CLAUDE.md verlangt es
  ebenfalls.
- **F18** AC-2, Abhilfetext für einen bereits CONVERTED FR: gemessen wird derselbe Text ausgegeben
  („`transition FR-0001 TRIAGED`, then `transition FR-0001 CONVERTED` …"), obwohl `resulting_item`
  schon gesetzt ist und die Transition aus einem Terminal nicht geht. Er sollte auf das gewordene
  Item zeigen.
- **F19** `--worktree` wird nicht geprüft: `Z:/does/not/exist at all` wird übernommen, ein Pfad
  INNERHALB des Repos ebenso, und zwei Leases auf denselben Baum werden beide erteilt
  (`verify/s/ac5.py`, Abschnitt F). Der Vertrag behauptet nichts anderes — gehört als Rest benannt,
  nicht als Fehler.
- **F20** Ein Loch-Item, das nicht mehr parst, verschwindet lautlos aus allen drei Prüfern
  (`state._iter_every_stored_item` schluckt die Leseausnahme). Gemessen: H156 mit kaputtem YAML →
  `test_every_hole_states_a_verdict_and_an_unclosed_one_names_its_limit` rc 0 („1 passed").
  Für ein ARCHIVIERTES Loch sieht es auch `validate_state` nicht.
- **F21** Protokoll §9: „3376 Zeilen". Gemessen: `wc -l stream-kernel.patch` = **3387**.
- **F22** `team-kits/kernel/migrate.py:1259-1261` bricht einen Testnamen über eine Zeilengrenze
  (`…_can_produce_a_status_an` / `# _approval_commits`) — die Lesart, die dieser Strom dem
  Löcher-Prüfer gerade abgewöhnt hat.

---

## Ausdrückliche Negativbefunde

### Gemessen und in Ordnung

**AC-1** (`verify/s/ac1.py`, echte Kernel-Aufrufe): Auswahl nennt den BUG → WALKED; nennt einen
ANDEREN BUG → REFUSED; nennt BEIDE → WALKED; nennt nur die WURZEL → REFUSED; `fail`-Auswahl →
REFUSED; `fail` dann `pass` → WALKED; `pass` dann `fail` (full) → REFUSED. Merge-Leser unverändert:
`delivery={} confirmation={'test': 'pass'}`. Dritte Frage → `ValueError`. `evidence --help`
(`cli.py:507`) behauptet weiterhin nur „does NOT open a merge" und bleibt damit wahr.

**AC-2**: FR in beiden Elternfeldern / nur `derives_from` / nur `product_requirement` / bereits
CONVERTED → alle vier REFUSED, jeweils mit `CONVERTED` und `resulting_item` im Text. Bestehende
Aufträge bleiben gültig: `validate_state` über den echten Speicher liefert mit und ohne Patch
identisch `{'warning': 67}` / 0 Fehler (`verify/s/ac2store.py`).

**AC-3, Prozess**: der ausgelieferte, UNBERÜHRTE Kit-Haken erreicht die neue Verweigerung —
`dev-team/hooks/gate_dispatch.py` als echter Prozess auf einer Lease, deren Ziel nachträglich
`normal` wurde: **rc 2**, Text nennt den Architektenschritt. `small` und `technical_enabler` werden
nicht gefragt, ein unbekannter Klassenwert (`nomal`) wird gefragt, ein ACCEPTED SR unter einer
ANDEREN Wurzel wird nicht anerkannt, ein Bugfix-Auftrag wird nicht gefragt.
`conftest.satisfy_the_architect_step` maskiert nichts: die beiden messenden Tests rufen
`create_lease` selbst.

**AC-4, Migration** gegen `verify/mig` (Kopie ohne `.git`, `project_memory` von 75a00d1):
`143 written, 0 already, 143 prose files`, rc 0; Dokument 9272 → 2441 Zeilen; zweiter Lauf 0,435 s,
`0 written`, SHA256 des Dokuments identisch; `validate` danach 0 Fehler / 66 Warnungen (= vorher);
Gate-Knoten `-k "hole or holes or reference_to_a_measurement"` **7 passed** (398 s). Ein später
eingereichter Eintrag im heutigen Format wird mit seiner reservierten Nummer übernommen
(`H151 -> BUG-0235`, Prosa geschrieben, Indexzeile ergänzt). Die Prüfer lesen wirklich ITEMS:
`limits` eines TRIAGED-Lochs geleert → rc 1; `regression_tests` auf einen nicht existierenden Test
gezeigt → rc 1; jeweils nach Rückbau wieder rc 0. Ein handgeändertes Feld im Index macht den
Index-Test rot. `ACCEPTED_EXCEPTION` ist ohne Mint unerreichbar (blanke Transition: „refused
(fail-closed)"), eine `scope`-Freigabe läuft die ANDERE Kante (→ APPROVED), der
`hole_exception`-Mint auf einem TRIAGED-Loch läuft sie, aus OPEN läuft er nicht.
`hole_number` lückenlos und ohne Doppel (H1, H2, next H3).

**AC-5**: Überlappung außerhalb jeder Naht → REFUSED, der geteilte Pfad wird genannt; Überlappung
nur innerhalb einer Naht, die BEIDE deklarieren → GRANTED; Naht nur von EINEM deklariert →
REFUSED; disjunkt → GRANTED; abgelaufene Lease → GRANTED; der abgewiesene Auftrag bleibt READY.

**Rot-zuerst, selbst nachgestellt** (`verify/s/redfirst.py`, Kopie `mut` ohne `.git`, je Mutation
Lauf / Mutation / Rückbau):

| AC | Mutation | sauber | mutiert | zurück |
|---|---|---|---|---|
| AC-1 | Frage-Filter wieder bedingungslos | rc 0 | **rc 1** | rc 0 |
| AC-2 | `_assert_the_origins_are_not_inbox_items` entfernt | rc 0 | **rc 1** | rc 0 |
| AC-2 | Zähler nur über aktive Items | rc 0 | **rc 1** | rc 0 |
| AC-3 | Pflicht als Aufzählung `("normal","large")` | rc 0 | **rc 1** | rc 0 |
| AC-4 | Aufrufer darf `hole_number` mitgeben | rc 0 | **rc 1** | rc 0 |
| AC-4 | `ACCEPTED_EXCEPTION` aus jedem Status | rc 0 | **rc 1** | rc 0 |
| AC-5 | Überlappungsprüfung aus `create_lease` entfernt | rc 0 | **rc 1** | rc 0 |
| AC-5 | `worktree` nicht auf die Lease geschrieben | rc 0 | **rc 1** | rc 0 |

**Paket / Pflicht 8**: 18 Dateien, alle in `allowed_scope`; `kitupdate.py`, `gate_dispatch.py`,
`.claude/hooks/gate_*.py`, `_harness.py`, `settings.json`, `constitution/**`, `agents/**`,
`skills/**`, `templates/repo/**` unberührt; keine gespiegelte Datei geändert; keine VERSION-Hunks
(einziges „VERSION" im Patch ist Prosa in H148); 0 CR-Bytes in allen 18 Quelldateien;
`git apply --check` gegen 75a00d1 rc 0; Arbeitsbaum == 75a00d1 + Patch + genau die drei
VERSION-Dateien (`2026.09.05-2`); `project_memory` im Arbeitsbaum unverändert. Lesende Suiten
**409 passed** (179 s) und **190 passed** (169 s); `ruff check .` „All checks passed";
`tools/validate.py` „all structural checks passed". H154–H156 liegen im reservierten Bereich,
tragen Mechanismus, gemessene Kette, Urteil und Begrenzung, und jedes Testzitat darin trägt sein
Modulpräfix.

### Nicht gemessen

- Die volle Suite (gehört laut DEC-0050 dem Merge) und `tools/test_hooks.py`.
- Der Rest von `.claude/hooks/test_gates.py` außerhalb von `-k "hole or holes or
  reference_to_a_measurement"`.
- `gate_dispatch.py` von office-team und research-team als Prozess (nur dev-team gemessen).
- Der EINE schreibende Migrationslauf gegen den kanonischen Zustand (verboten in diesem Auftrag).
- Wirkung von 178 aktiven `BUG`-Items auf Board, `session_brief` und die Rollups.
- `tools/bump_kit_version.py` / der Kit-Hash mit dem neuen Verzeichnis `docs/holes/`.
- Laufzeit von `_iter_every_stored_item` bei jedem `capture` in einem großen Speicher.
- Ob `related_pr: PR-0003` für 143 Löcher die Abnahme dieses Ziels beeinflusst.

---

## Einordnung der Befunde

**Rundenblockierend:** F1 (der falsche G4-3-Satz UND das fehlende Loch), F2, F3, F4.
Alle vier haben eine Kette, die innerhalb einer Sitzung durchläuft, und drei davon sitzen auf dem
Merge-Lauf, von dem AC-4 abhängt.

**In die Löcherliste als benannter Rest** (falls nicht geschlossen): F6 (ein Prüfer, der über
leerem Bestand nichts misst), F19 (`worktree` ungeprüft, zwei Leases auf einem Baum), F20 (ein
unlesbares Loch-Item ist für alle Prüfer unsichtbar). Jeweils Mechanismus benennen, nicht die
Schreibweise, die ich zufällig probiert habe.

**Nacharbeit ohne Loch:** F5, F7, F8, F9, F10, F11, F12, F13, F14–F18, F21, F22.
