# TSK-0123 — Prüfbericht Runde 2 (harness-verifier), PR-0006 AC-1..AC-4

| | |
|---|---|
| Gegenstand | Arbeitsbaum `C:/Offline Repos/v2-testbed/_worktrees/g4-procedure` (22 geändert + 1 neu), Patch `_round-scratch/TSK-0123/stream-procedure.patch` (20 Köpfe, 124 698 B), Protokoll `project_memory/staging/TSK-0123/stream-protocol.md`, Journal `redfirst.log` (33 × rc 1, 3 Basisläufe) |
| Gemessen in | **frische** Kopie `_round-scratch/TSK-0123/verify/tree` (ohne `.git`), Referenz `verify/head` (`git archive 75a00d1` + Patch, `-c core.autocrlf=false`), Pilot `verify/pilot`, Rigs `rig_r2*.py`, `probe_*.py`, `eolcheck2.py` — je ein Fall pro Aufruf, binäres I/O, Verweigerung außerhalb des eigenen Verzeichnisses |
| Suiten (eine nach der anderen) | `test_review_procedure` **18 passed** · `test_role_contracts` **30 passed** · `test_shortening_net` **36 passed** · `test_repo_hygiene::test_every_test_pointer_this_repo_writes_resolves` **1 passed** (53 s) · `ruff` clean · `validate.py` clean |
| **Urteil** | **PASS** — alle vier blockierenden Befunde der Runde 1 sind geschlossen und je einzeln rot nachgemessen; zwei neue, **nicht blockierende** Reste (N1, N2), die als benannte Reste ins Protokoll gehören, plus zwei Nits |

---

## Urteil je Kriterium und Pflicht

| | Runde 1 | Runde 2 | Grund |
|---|---|---|---|
| AC-1 (FR-0084) | FAIL | **PASS** | zweite Hälfte GEBAUT: ein byte-gleicher Verfassungsabsatz in allen drei Kits, mit eigenem Test, der in beide Richtungen rot wird; im scaffolded Piloten (meiner, office-team) in der installierten `AGENTS.md` angekommen |
| AC-2 (FR-0005) | FAIL | **PASS** | die Zeigerzeile steht in allen drei Kits an einer Satzgrenze; der Positions-Leser macht die Runde-1-Stelle rot |
| AC-3 (FR-0010) | PASS | **PASS** | unverändert; Löschen einer Form weiter rot |
| AC-4 (DEC-0070) | FAIL | **PASS** | Regelnummern als MENGE gegen `{1,2,5}` plus Mechanismus-Term je Regel; Lektionen als eigene Aussagen mit je einem Datensatz — beide Runde-1-Mutationen jetzt rot |
| Pflicht 5 (rot-zuerst, gemessene Behauptungen) | FAIL | **PASS** | jeder Fix hat seinen roten Fall, von mir unabhängig reproduziert; die verbleibenden Grenzen sind im Protokoll §6 benannt — bis auf N1/N2 |
| Pflicht 6 (Nähte) | PASS | **PASS** | Nahttabelle um die zwei NEUEN geteilten Dateien ergänzt (`team-kits/*/constitution/AGENTS.md`, `tools/lead_package_sizes.json`); der wörtliche Satz an G4-1 steht unverändert |
| Pflicht 7 (Übergabe) | PASS, ein Rest | **PASS** | Tokens jetzt in §8 (~575 k); Patch, Bereich, Zeilenenden, Stempel, kein Commit/Push/Install nachgemessen |

---

## Was ich von Runde 1 nachgemessen habe (jede Mutation in meiner eigenen Kopie, mit Rückstellung)

| Runde-1-Befund | meine Mutation | rc | rot geworden |
|---|---|---|---|
| **B1** | Zeigerzeile zurück in die Mitte des Satzes (office) | **1** | `test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix` |
| **B2** | alle drei Lektionen gelöscht, Überschrift bleibt | **1** | `test_every_harness_role_text_answers_for_the_lessons_it_was_given` |
| **B2** | EINE Lektion gelöscht | **1** | dito |
| **B2** | zwei Lektionen in EINE Aussage gefaltet (beide Zeiger in einem Punkt) | **1** | dito (`assert not ['- **Two lessons in one statement** …']`) |
| **B2** | eine Lektion in eine andere Datei verschoben | **1** | dito |
| **B3** | Regel 2 gelöscht, Regel 1 verdoppelt | **1** | `test_the_lead_role_text_carries_the_orchestrator_rules_with_their_pointers` |
| **B3** | Regel 5 in eine Parole umgeschrieben, Zeiger bleibt | **1** | dito |
| **B4** | Verfassungsabsatz in allen drei Kits entfernt | **1** | `test_every_constitution_asks_a_plan_for_the_way_it_rejected`, `test_the_rejected_alternative_rule_claims_no_enforcement_it_does_not_have` |
| **B4** | Absatz in EINEM Kit entfernt / in EINEM Kit umformuliert | **1** / **1** | `…asks_a_plan_for_the_way_it_rejected` |
| **B4** | Überbehauptung in den Absatz eingefügt | **1** | `test_the_rejected_alternative_rule_claims_no_enforcement_it_does_not_have` |
| **R1** | „gate_dispatch refuses an order that skipped either reading" (meine Runde-1-Mutation) | **1** | `test_the_order_reading_claims_no_enforcement_it_does_not_have` |
| **R1** | dieselbe Überbehauptung **in Backticks** (neue Schreibweise) | **1** | dito |
| **R2** | die drei Zeilen für den Nutzer in allen drei Kits gelöscht | **1** | `test_the_auditing_role_of_every_kit_runs_a_retrospective_and_it_is_one_text` |
| **R2** | Aufzeichnungspflicht („RECORD THE CHOICE") in allen drei Kits gelöscht | **1** | `test_every_kit_lead_is_given_the_ways_a_work_order_line_goes_wrong` |
| **R3** | Sonde über `docs/POST_V2_WISHLIST.md` | — | der tote Knoten `…::test_no_such_test_at_all` ist **weg** (`ValueError: substring not found`); nur `H157`–`H159`, keine Nummer darüber |
| **R4** | Protokoll §8 | — | `Tokens … zusammen ~575 k` steht da |
| **R5** | Protokoll §4 | — | Kanal-Abweichung erklärt und gegen `kernel/report.generate_session_brief` gemessen |

Damit sind **B1, B2, B3, B4 geschlossen** und **R1 geschlossen**, **R2 zur Hälfte** (wie behauptet),
**R3/R4/R5 erledigt**.

---

## Neue Befunde — Angriff auf die FIXES (beide nicht blockierend)

### N1 — `tools/test_review_procedure.py:518-531`: der Positions-Leser hat zwei unbenannte Ausgänge

`_torn_sentence_above` nimmt `next(one for one, line in enumerate(lines) if names in line)` — die
**erste** Zeile, die die Überschrift nennt — und geht von dort zur nächsten **fett** beginnenden
Zeile hoch. Zwei Zerrisse bleiben damit grün, beide von mir gemessen:

```
CASE b1_torn_insertion_below_a_clean_pointer -> rc 0
18 passed in 7.45s
   (saubere Zeigerzeile bleibt stehen; eine ZWEITE, fett beginnende Aussage mit derselben
    Überschrift wird weiter unten mitten in den Satz „…in a directory that is empty today. Wishes
    whose file lists / overlap are merged…" gesetzt)

CASE b1_attack_non_bold_pointer_in_the_middle_of_a_sentence -> rc 0
18 passed in 7.36s
   (dieselbe Stelle wie Befund B1 der Runde 1, nur ohne Fettung:
    „…Verify outputs against REALITY / Before this order goes out it gets ONE reading: see …")
```

Der Docstring des Tests benennt eine **andere** Grenze („whether the position is the RIGHT one among
the boundaries"), und Protokoll §6 (7) wiederholt genau diese. „Nur die erste Nennung" und „nur
fett eingeleitete Einschübe" stehen nirgends.
**Schwere:** Rest, nicht blockierend — heute trägt jedes Kit genau eine, saubere Nennung; der
Ausgang wird erst relevant, wenn jemand eine zweite einfügt. **Minimalfix (einzeilig):** über ALLE
Zeilen laufen, die die Überschrift nennen (`any(... for one, line in enumerate(lines) if names in
line)`), statt über die erste; die Fettungs-Hälfte als Grenze ins Protokoll schreiben.

### N2 — `tools/test_review_procedure.py:170-186`: das Vokabular kommt jetzt aus JEDER Datei in `hooks/`, nicht aus den registrierten Haken

`_mechanism_words` ergänzt `_enforcement_words` um `glob(hooks/*.py)` — also auch um Helfer, die
kein Haken sind (`_root`, `_compat`, `format_on_write`, `_stdlib_guard` …). Damit hängt die
Ehrlichkeitsprüfung an **Dateinamen**, und ein künftiger Haken mit einem gewöhnlichen englischen
Wort als Namen macht unveränderte, ehrliche Blöcke rot. Gemessen mit einer plausiblen neuen Datei
`team-kits/dev-team/hooks/reading.py` (nur angelegt, nirgends registriert):

```
CASE a_new_hook_file_named_after_a_common_word -> rc 2 Fehlschläge
FAILED tools/test_review_procedure.py::test_the_retrospective_step_states_the_limit_it_runs_under
FAILED tools/test_review_procedure.py::test_the_order_reading_claims_no_enforcement_it_does_not_have
2 failed, 16 passed in 13.25s
```

Richtung: **Falschalarm** (fail-closed), also kein Loch — aber die Meldung spricht dann von
„claiming enforcement", während die Ursache eine fremde neue Datei ist.
**Schwere:** Rest, nicht blockierend. **Minimalfix:** die Dateinamen aus den **registrierten**
Haken der `settings.json` ableiten (dieselbe Quelle wie das Basisvokabular) statt aus dem
Verzeichnis — oder die Grenze in §6 (5) mit dieser Messung ergänzen.

### Nits (keine Nacharbeit nötig, nur beim Merge nicht weitertragen)

* **Protokoll §3**, Zeile „`docs/reviews/phase0-disposition.md` … (13 Journalzeilen)": gemessen sind
  es **16 neue** Zeilen (13 vom Pin-Skript — 6+4+3, wie §7 richtig sagt — und 3 vom
  Größen-Skript; eine vierte Größenzeile wurde nur verschoben). Die Zahl in §3 zählt die zweite
  Quelle nicht mit, die derselbe Satz nennt.
* Der Stempel steht auf `2026.09.05-2` (die Runde lief über Mitternacht); der Release stempelt
  ohnehin neu.

---

## Ausdrücklich GEMESSENE Negativbefunde

* **Patch.** `git -c core.autocrlf=false apply` auf einen unberührten `75a00d1`-Baum: **rc 0**;
  `diff -r` gegen den Arbeitsbaum: Unterschiede **nur** in den drei `VERSION`-Dateien. Damit ist die
  Selbstkorrektur des Umsetzers bestätigt — das CRLF-Artefakt der Runde 1 war sein Rig, nicht der
  Patch. 20 Köpfe, **keine** `VERSION`-Hunks (das Wort steht nur in einer Kontextzeile von `H148`),
  0 CR im Patch.
* **Bereich.** Alle 20 Patch-Pfade liegen im `allowed_scope` (`team-kits/*/constitution/**` ist
  darin enthalten); kein Pfad im `forbidden_scope`; unter `tools/` nur das neue Modul und die zwei
  von Werkzeugen geschriebenen Datensätze.
* **Zeilenenden.** 23 berührte Dateien, **0 CR-Bytes**.
* **Stempel.** `bump_kit_version.py --check`: alle drei „unchanged (2026.09.05-2)".
* **Ratsche.** `record_lead_package_sizes.py` ohne `--write`: „3 kits, every size is the one on
  record"; die Deltas gegen `75a00d1` sind exakt **+886 B je Kit** (dev 49208→50094, office
  54779→55665, research 52213→53099), mit Begründungszeile im Journal; `validate.py` grün.
* **Scaffolded Pilot, von mir gefahren** (`verify/pilot`, eigenes HOME unter
  `_round-scratch/TSK-0123/verify/fakehome`, diesmal **office-team**, um nicht den Piloten des
  Umsetzers zu wiederholen): `init_project_memory.sh` + `scaffold_team.sh` rc 0 → die Pflicht
  „verworfener Weg" steht in der installierten `AGENTS.md` (1), die Anlassregel in
  `.claude/agents/project-auditor.md` (1), der Rückschau-Schritt in
  `.claude/skills/project-auditor/SKILL.md` (1), die Auftragslesung in
  `.claude/skills/office-manager/SKILL.md` (2) — und die Zeigerzeile sitzt dort **hinter** dem
  abgeschlossenen Satz („…before advancing."), der Runde-1-Riss ist im installierten Text weg.
* **Globaler Speicher unberührt**: `~/.claude/team-kits/dev-team/VERSION` = `2026.09.02-10`, die
  Pflicht „REJECTED" kommt dort nicht vor (0 Treffer).
* **Naht.** Die zwei neuen geteilten Dateien sind in §3 als „NEU seit Nacharbeit 1" eingetragen —
  das ist genau die Klasse, die `DEC-0070` (1) als Zuschnitt-Befund führt, und sie ist hier von
  selbst gemeldet. Alle fünf Generation-4-Ströme tragen `team-kits/*/constitution/**` im
  `allowed_scope`, die Verfassung ist also eine erwartete Merge-Naht und keine stille Kollision.
* **Grenzen, die grün BLEIBEN und im Protokoll §6 benannt sind** (von mir nachgemessen, damit die
  Behauptung nicht ungeprüft steht): eine Regel mit Zeiger UND Mechanismus, aber invertiertem Satz
  („**A \"queued\" SendMessage IS a delivery** … Never run a `ListAgents` check") → rc 0; eine
  Lektion mit Fett-Einleitung und Zeiger, inhaltlich ins Gegenteil verkehrt → rc 0; eine gelöschte
  Lektion, deren Datensatz von einer fremden Aussage getragen wird → rc 0; dieselbe falsche
  Umformulierung einer Frage in allen drei Kits → rc 0; ein Verfassungsabsatz, in allen drei Kits
  gleich ausgehöhlt → rc 0; eine Überbehauptung, die gar keinen Mechanismus nennt → rc 0. Alle
  sechs stehen als §6 (4) und §6 (5) im Protokoll.
* **Satzgrenzen-Leser** (`_ends_a_sentence`), direkt gesondert: `:` und `)` ohne Punkt gelten als
  „nicht beendet" (also Falschalarm-Richtung), `.`/`?`/`!` auch hinter `**`, `` ` ``, `"`, `)` als
  beendet — deckt sich mit dem Docstring.
* **Suiten** in meiner Kopie: siehe Kopfzeile; die Zeiger-Sweep von `test_repo_hygiene` läuft grün,
  obwohl die drei Verfassungen jetzt einen Test-Knoten zitieren
  (`tools/test_review_procedure.py::test_every_constitution_asks_a_plan_for_the_way_it_rejected` —
  existiert, Zeile 627).

## Ausdrücklich NICHT gemessen

* Volle Suite (gehört zum Merge, `DEC-0050`) sowie `test_parallel_streams`, `test_reference_skills`,
  `test_kit_neutrality`, `test_shared_skill_contract`, `test_routine_feed`, `test_repo_hygiene` als
  Ganzes — die „197 passed" des Protokolls bleiben insoweit ungeprüft (zwei Tests von
  `test_repo_hygiene` scheitern in einer Kopie ohne `.git` grundsätzlich an `git ls-files`).
* `.claude/hooks/test_gates.py` (unberührter Bereich); Haken-Fristen sind kein Thema, weil keine
  Registrierung angefasst wurde.
* Ob in einer echten Sitzung die drei Zeilen beim Nutzer ankommen (kein Live-Auditorlauf); der
  dev-/research-Scaffold (nur office-team gefahren, dev in Runde 1).
* Die Innereien der Rigs des Umsetzers; `redfirst.log` nur stichprobenartig gegen eigene Messungen
  gehalten (33 × rc 1, 3 Basisläufe — Zählung stimmt).

---

## Verdikt

**PASS.** Die Nacharbeit trifft alle vier blockierenden Befunde an der Wurzel statt an ihren
Beispielen: die Position einer eingefügten Aussage wird jetzt gelesen statt nur ihre Anwesenheit,
die Lektionen sind einzelne Aussagen mit je einem Datensatz, die Regeln werden als **Menge** von
Nummern mit einem benannten Mechanismus gelesen, und die zweite Hälfte von FR-0084 ist **gebaut** —
ein byte-gleicher Absatz in allen drei Verfassungen, im einzigen Text, den jede Sitzung lädt, mit
einem Test, der in beide Richtungen rot wird, und im installierten Projekt angekommen (selbst
gescaffoldet). Jede dieser Aussagen habe ich in meiner eigenen Kopie mutiert und rot gesehen; der
Patch reproduziert den Arbeitsbaum aus `75a00d1` byte-genau bis auf die Stempel. Offen bleiben zwei
Reste, beide nicht blockierend und beide bloß aufzuschreiben: der Positions-Leser sieht nur die
erste und nur die fett eingeleitete Nennung (N1), und das erweiterte Ehrlichkeitsvokabular hängt an
jeder Datei in `hooks/`, sodass ein künftiger Haken mit einem Allerweltsnamen zwei ehrliche Blöcke
falsch rot macht (N2). Beide gehören in Protokoll §6 — und N1 ist ein Einzeiler, falls der Lead ihn
in dieser Runde noch mitnehmen will.
