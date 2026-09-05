# TSK-0123 — Prüfbericht Runde 1 (harness-verifier), PR-0006 AC-1..AC-4

| | |
|---|---|
| Gegenstand | Arbeitsbaum `C:/Offline Repos/v2-testbed/_worktrees/g4-procedure`, Patch `_round-scratch/TSK-0123/stream-procedure.patch`, Protokoll `project_memory/staging/TSK-0123/stream-protocol.md` |
| Gemessen in | `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0123/verify/` — `tree/` (Kopie des Arbeitsbaums OHNE `.git`), `head/` (`git archive 75a00d1` + Patch), `pilot/` (scaffolded dev-team), Rigs `rig.py`, `rig2.py`, `rig3.py`, `rig4.py`, `eolcheck.py`, `probe_citation*.py` |
| Rig-Eigenschaften | ein Fall pro Aufruf, binäres Lesen/Schreiben, Verweigerung außerhalb des eigenen Verzeichnisses, Rückstellung aus `head/` |
| Suiten (eine nach der anderen, nur lesende) | `test_review_procedure` 14 passed · `test_role_contracts` 30 passed · `test_shortening_net` 36 passed · `test_repo_hygiene` 17 passed / 6 skipped / 2 failed (beide Artefakte meiner Kopie ohne `.git`) |
| **Urteil** | **FAIL** — vier blockierende Befunde (B1–B4), fünf benannte Reste (R1–R5) |

---

## Urteil je Kriterium

| Kriterium | Urteil | Grund |
|---|---|---|
| AC-1 (FR-0084) | **FAIL** | B4: die zweite Hälfte des Wunsches (verworfener Weg in JEDEM TSK-Plan) steht nur als Prosa in `harness-implementer.md`, in keinem Kit, ohne Test, ohne Pilot — und in keiner Restliste. Rückschau-Schritt selbst: gebaut, rot-zuerst nachgemessen |
| AC-2 (FR-0005) | **FAIL** | B1: die Zeigerzeile zerreißt im office-Kit einen Satz der Arbeitsschleife. Sektion, drei Auflagen und Aufnahme in die Sequenz sonst gebaut und rot-zuerst nachgemessen |
| AC-3 (FR-0010) | **PASS** | fünf Formen als Prüfschritte mit je einem Entscheidungs-Item, Löschen einer Form ist rot (nachgemessen). Rest R2 |
| AC-4 (DEC-0070) | **FAIL** | B2 und B3: beide Leser der Rollentexte zählen, statt zu identifizieren — Regel 2 löschen und Regel 1 verdoppeln bleibt grün, alle drei Lektionen löschen bleibt grün |
| Pflicht 5 (rot-zuerst, gemessene Behauptungen) | **FAIL** | B2 ist genau die Klasse „ein benannter Test, der nicht scheitern kann"; dazu zwei gemessene, nirgends aufgeschriebene Grenzen (R1, R2) |
| Pflicht 6 (Nähte) | **PASS** | Nahttabelle mit „empfangen: keine / erwartet: G4-1, G4-2" und der wörtliche Satz an G4-1 stehen im Protokoll §3; Verfassungen unberührt, `test_role_contracts` grün |
| Pflicht 7 (Übergabe) | **PASS**, ein Rest | Patch, Bereich, Zeilenenden, Stempel, kein Commit/Push/Install alles nachgemessen; R4: die Token-Zahl fehlt im Protokoll |

---

## Blockierende Befunde

### B1 — `team-kits/office-team/skills/office-manager/SKILL.md:118-121`: die Zeigerzeile zerreißt einen Satz

Die zwei eingefügten Zeilen landen mitten in einem Satz der Delegier-Stufe:

```
118:   files to read, and the scope it may write. Verify outputs against REALITY
119:   **Before this order goes out it gets ONE reading**, and it is the section below —
120:   "Before the order goes out: a smaller plan, and the five ways a line goes wrong".
121:   (the archive tree against `filing_plan.yaml`, catalog entries, register entries) — never trust "done"
```

„Verify outputs against REALITY" verliert seine Klammer, die Klammer beginnt einen Absatz. Im dev- und
im research-Kit sitzt dieselbe Zeile sauber an einer Satzgrenze (`…project-manager/SKILL.md:195` bzw.
`:111`). Kein Test sieht das: `test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix`
fragt nur, ob die Überschrift IRGENDWO in der Arbeitsschleife steht.

**Schwere:** blockierend (ausgeliefertet Kit-Text). **Minimalfix:** die zwei Zeilen hinter
`… never trust "done" strings.` setzen.

### B2 — `tools/test_review_procedure.py:534-547`: ein benannter Test, der die Eigenschaft seines Docstrings nicht messen kann

Der Docstring behauptet (Zeile 538-540): „What a check CAN hold is that each of the three texts still
answers for them by naming the verdict they came out of, **so deleting the block is visible instead of
quiet**." Der Test ist eine Zeichenkettensuche über die GANZE Datei (`"`DEC-0070`" not in text`) — und
`harness-implementer.md` nennt die Entscheidung genau einmal, nämlich in der **Überschrift** (Zeile 72).

Gemessen (jeweils mutiert, Suite gefahren, zurückgestellt):

```
CASE implementer_all_three_lessons_deleted_heading_kept -> rc 0
14 passed in 4.32s
CASE one_of_three_implementer_lessons_deleted -> rc 0
14 passed in 7.06s
CASE verifier_lesson_replaced_by_nonsense_keeping_the_pointer -> rc 0
14 passed in 5.57s
```

Der komplette Lektionsblock des Umsetzer-Textes kann verschwinden, solange die Überschrift stehen
bleibt. Zusätzlich widerspricht der Test dem Modul-Docstring (Zeile 4-8): „every one of them is asked
of the text a ROLE really receives, **parsed into the unit** … and never as a string search over a
whole file."

**Schwere:** blockierend — das ist die Klasse, die `DEC-0070` (Kontext, „a named test that cannot
fail", vier Fälle) und die Pflicht 5 des Items ausdrücklich verbieten.
**Minimalfix:** je Lektion ein Aufzählungspunkt mit eigenem Zeiger, gelesen wie die Regeln
(`_BULLET_SPLIT_RX` + Zeiger), Untergrenze 3 je Datei — oder die Eigenschaftsbehauptung aus dem
Docstring streichen und die Grenze als Rest benennen.

### B3 — `tools/test_review_procedure.py:487-517` mit `:66-77`: der Zähler zählt Zeiger, nicht Regeln

Die Selbstkorrektur des Umsetzers (Erwähnung → Zeiger mit Regelnummer) ist echt und wirkt, aber sie
bleibt ein **Zähler**: `len(rules) >= 3` über Aufzählungspunkte, die IRGENDEINE Regelnummer nennen.
AC-4 verlangt die Regeln **1, 2 und 5**.

```
CASE ac4_one_rule_deleted -> rc 1                        (Kontrolle: Löschen ohne Ersatz ist rot)
FAILED …::test_the_lead_role_text_carries_the_orchestrator_rules_with_their_pointers
CASE rule2_replaced_by_a_second_copy_of_rule1 -> rc 0    (Regel 2 gelöscht, Regel 1 doppelt)
14 passed in 7.65s
CASE rule5_reworded_but_keeps_its_pointer -> rc 0        (Regel 5 durch „Send whatever, whenever" ersetzt)
14 passed in 5.30s
```

Der Docstring sagt dazu (Zeile 505): „THE FLOOR IS THREE **because the decision puts three rules into
this file**" — die Zahl drei ist erreicht, die drei Regeln sind es nicht.

**Schwere:** blockierend (dieselbe Defektklasse eine Ebene höher als der schon behobene Fall).
**Minimalfix:** `_rule_pointer_rx` bekommt eine Gruppe für die Nummer, der Test sammelt die Menge der
Nummern und verlangt `{1, 2, 5} ⊆ gefunden`. Die Umformulierung bei erhaltenem Zeiger bleibt dann
eine bewusst benannte Grenze (siehe R2).

### B4 — AC-1, zweite Hälfte (FR-0084 (2)): der „verworfene Weg" ist im Kit nirgends und hier ohne Test

FR-0084 verlangt zwei Hälften; die zweite lautet wörtlich: „EVERY TSK PLAN (implementer, before
building) names in one line the alternative way it rejected and why … Where it lives: dev/office/research
constitutions + project-auditor role (kits), .claude/agents/harness-lead.md". PR-0006 AC-1 schreibt
dafür die Planprüfung vor, das Item lässt ersatzweise „the skill's own step with a measured pilot" zu.

Gebaut ist: **ein Aufzählungspunkt** in `.claude/agents/harness-implementer.md:77` („**Your PLAN names
the way it REJECTED**"). Gemessen im ausgelieferten Baum:

```
$ grep -rn "rejected" --include=*.md team-kits/*/skills/project-manager/ \
      team-kits/office-team/skills/office-manager/ team-kits/*/constitution/
… nur zwei Treffer, beide Prosa der neuen Sektion („the reviewer rejected the ORDER as too coarse")
$ grep -n "rejected\|REJECT" tools/test_review_procedure.py
(keine Ausgabe)
```

Also: keine Pflicht in einem der drei Kits (die Verfassungen liegen im `allowed_scope` und sind
unberührt), kein Test, kein Pilot, und die Lücke steht **weder** in §6 des Protokolls („was bewusst
nicht geschlossen") **noch** in der Löcherliste. Die Sektion „(1) A SMALLER plan" deckt sie nicht ab:
sie feuert nur bei ihrem mechanischen Auslöser, FR-0084 verlangt die Zeile in JEDEM Plan.

**Schwere:** blockierend, bis eines von beidem gilt — gebaut (ein Satz in den drei Verfassungen plus
ein Leser, beides im erlaubten Bereich) **oder** als benannte Ausnahme mit Grund im Protokoll §6 und
in der Löcherliste geführt. Der dritte Zustand („bekannt, kommt später") existiert in diesem Repo
nicht.

---

## Benannte Reste (nicht blockierend, aber aufzuschreiben)

### R1 — die Ehrlichkeitsprüfung ist blind für die Schreibweise, in der die neuen Texte ihre Haken nennen

`tools/test_role_contracts.py:814` sucht `\b<wort>\b`, und die Vokabeln sind `gate`, `guard`, `hook`
(aus `settings.json` abgeleitet). Ein Unterstrich ist ein Wortzeichen, also matcht `\bgate\b` **nicht**
in `gate_dispatch` — und genau so nennen die neuen Blöcke ihre Mechanik.

```
CASE overclaim_bare_vocabulary_word -> rc 1
E    assert not [' A gate']
FAILED …::test_the_order_reading_claims_no_enforcement_it_does_not_have
CASE overclaim_hook_file_name -> rc 0     ("gate_dispatch refuses an order that skipped either reading.")
14 passed in 4.67s
```

Beide Male in alle drei Lead-SKILLs eingefügt, direkt vor „**(1) A SMALLER plan**". Das Protokoll §6.7
benennt die Grenze als „eine Überbehauptung, die keines dieser Wörter benutzt" — gemessen ist sie
weiter: eine Überbehauptung, die den Haken beim **Dateinamen** nennt, benutzt das Wort sichtbar und
fällt trotzdem durch. **Minimalfix:** die zwei neuen Ehrlichkeitstests fragen zusätzlich die
Unterstrich-Schreibweise ab, oder der Satz landet in `H157` unter „Begrenzt durch" (neue Nummern sind
nicht frei: das Item reserviert H157–H159).

### R2 — was in den neuen Blöcken steht, ist nur der Form nach gedeckt

Die Gleichheitsprüfung vergleicht die Kits **untereinander**; die Inhaltsprüfung ist eine Formprüfung
(≥4 Anlassmarken, ≥4 Fragezeilen, ≥5 nummerierte Formen, ≥3 Aufzählungspunkte). Drei Mutationen, alle
grün:

```
CASE all_three_kits_reworded_the_same_wrong_way -> rc 0        (Frage 3 in allen drei Kits durch Unsinn ersetzt)
CASE ac1_three_lines_to_the_user_deleted_in_all_three -> rc 0  (die DREI Zeilen für den Nutzer entfernt)
CASE ac2_record_the_choice_paragraph_deleted_in_all_three -> rc 0 (RECORD THE CHOICE entfernt)
14 passed
```

Die zweite und dritte Mutation löschen je eine ausdrückliche Forderung von AC-1 bzw. AC-2. §6.6 des
Protokolls benennt nur die andere Grenze („ob jemand den Schritt ausgeführt hat"). **Minimalfix:**
Satz in §6 — oder die drei Zeilen und die Aufzeichnungspflicht als eigene Form pinnen.

### R3 — `docs/POST_V2_WISHLIST.md:9291`: ein absichtlich toter pytest-Knoten in Backticks

Die H159-Tabelle führt `` `Held by tools/test_review_procedure.py::test_no_such_test_at_all.` `` als
Beispiel eines faulen Zeigers. `test_repo_hygiene::test_every_test_pointer_this_repo_writes_resolves`
löst genau solche Knoten in `docs/` auf. Heute grün, aber nur durch Backtick-Parität:

```
total citations in the whole file: 43
the deliberately dangling example seen by the whole-file reading: []
backticks before the H159 table row: 10589      (ungerade → die Spanne liegt in der falschen Phase)
… dieselbe Datei ab "### H157" gelesen:
  Heldbytools/test_review_procedure.py::test_no_such_test_at_all -> UNRESOLVED
```

Ein einziger Codeblock (drei Backticks) weiter oben in dieser 9200-Zeilen-Datei dreht die Phase, und
die Suite meldet einen Verstoß, den niemand eingebaut hat — ausgerechnet in einer Datei, die die
Nahttabelle als **geteilt** führt. **Minimalfix:** das Beispiel ohne die `…py::…`-Form schreiben.

### R4 — Protokoll §8: die Token-Zahl fehlt

Pflicht 7 verlangt „wall-clock **und tokens** für die (g)-Zeile". Das Protokoll verweist auf den
Bericht des Umsetzers. Genau das ist der Ort, den CLAUDE.md als verloren beschreibt, sobald die
Sitzung zusammengefasst wird. **Minimalfix:** die Zahl in §8 eintragen.

### R5 — AC-1: der Kanal ist ein anderer als im Kriterium, und das steht nirgends

AC-1 sagt „the session brief carries … three lines to the user", das Item „session brief / round log".
Gebaut ist der Weg über die Evidence-`summary`. Gemessen: `team-kits/kernel/report.py:211-289`
(`generate_session_brief`) schreibt `kit`, `active_roots`, `active_tasks`, `open_approvals`,
`staging_pointers`, `standing_decisions`, `budget_status` — keine Evidence und keine `summary`. Der
gewählte Weg trägt dafür: `team-kits/kernel/schemas/result_envelope.yaml:19` verlangt `summary`
(required, max 2000), `REQUIRED_FIELDS["EVD"]` ebenfalls, und `gate_subagent_output` blockt einen Stop
ohne `summary:`. Die Abweichung ist also vertretbar — sie ist nur nicht erklärt.
**Minimalfix:** eine Zeile im Protokoll §4 (AC-1), die den Kanalwechsel und seinen Grund nennt.

---

## Ausdrücklich GEMESSENE Negativbefunde (kein Befund)

* **Patch.** `git apply --check` und `git apply` auf einen unberührten `75a00d1`-Baum: **rc 0**.
  Anschließend `diff -r --brief head tree`: Unterschiede **nur** in den drei `VERSION`-Dateien.
  Anders als Protokoll §9 vermutet, gibt es **keinen** Zeilenenden-Unterschied — der Hinweis auf ein
  CRLF-Artefakt des Prüf-Rigs kann entfallen. 16 `diff --git`-Köpfe, keine `VERSION`-Hunks, 0 CR-Bytes.
* **Bereich.** Alle 16 Patch-Pfade + die drei `VERSION` liegen im `allowed_scope`; kein Pfad im
  `forbidden_scope`; unter `tools/` nur ein neues Modul und die vom Pin-Skript geschriebene
  `constitution_section_pins.json`.
* **Zeilenenden.** `eolcheck.py` über alle 19 berührten Dateien: `files checked: 19, CR bytes total: 0`.
* **Stempel.** `python -B tools/bump_kit_version.py --check` → `dev-team: unchanged (2026.09.04-2)`,
  `office-team: unchanged (2026.09.04-4)`, `research-team: unchanged (2026.09.04-2)` — der Stempel ist
  aktuell, nichts wurde nach dem Bump geändert.
* **Kein Commit, kein Push, keine Installation.** Arbeitsbaum-`HEAD` = `75a00d1`, Änderungen
  uncommitted; der globale Speicher steht unberührt auf `2026.09.02-10` und kennt den
  Rückschau-Schritt nicht (`grep -c "The RETROSPECTIVE" …/.claude/team-kits/… = 0`).
* **Rot-zuerst je Kriterium, in meiner eigenen Kopie nachgefahren:** AC-1 Schritt aus allen drei
  Auditor-SKILLs entfernt → rc 1 (2 failed); AC-1 Anlassmarken entfernt → rc 1; AC-2 die drei Auflagen
  gelöscht → rc 1; AC-2 Zeigerzeile aus EINER Arbeitsschleife → rc 1 („dev-team: the work loop never
  names …"); AC-3 eine der fünf Formen gelöscht → rc 1 (3 failed); AC-4 eine Regel gelöscht → rc 1.
* **Leser-Böden, nachgefahren:** `_rule_pointer_rx` „jede Erwähnung" → rc 1, „nichts" → rc 1 (2 failed);
  `_item_citations` „nichts" → rc 1 (5 failed); `_question_steps` „jeder Schritt" → rc 1 (2 failed).
* **Scaffolded pilot (von mir gefahren, nicht vom Umsetzer):** `init_project_memory.sh dev-team` +
  `scaffold_team.sh dev-team solo` mit gefälschtem `HOME` in `verify/pilot/` → der Anlass-Punkt steht in
  `.claude/agents/project-auditor.md` (1 Treffer), der Rückschau-Schritt in
  `.claude/skills/project-auditor/SKILL.md` (1), die Auftragslesung in
  `.claude/skills/project-manager/SKILL.md` (2). `project-auditor` ist in **jedem** Preset
  (`presets.yaml`), erreicht also jedes installierte Projekt. Damit ist „measured on a scaffolded
  pilot" erfüllt — durch meine Messung, nicht durch das Paket.
* **Zitate gegen die zitierte Datei geprüft:** „WHAT THIS GATE PARSES: the header, and only the header
  … Free prompt prose is never evidence of anything" steht so in `gate_dispatch.py`; die Aussage über
  Gate 2 in `harness-lead.md` („asks only that the spawn names an item that resolves and is not
  terminal") deckt sich mit `.claude/hooks/gate_spawn_needs_item.py` (Kopf: „an id that RESOLVES …
  and is NOT terminal"); die Behauptung des neuen Moduls, `.claude/agents/` werde von keiner anderen
  Suite gelesen, deckt sich mit `test_gates.py:5128-5131` („A test named in … a role definition under
  `.claude/agents/` … is NOT read here") und mit `test_repo_hygiene._texts_that_answer_for_a_claim`
  (`team-kits/`, `docs/`).
* **Löcher.** Nur H157–H159, alle drei mit Mechanismus, gemessener Kette, Begrenzung und Urteil; die
  Test-Zitate tragen ihr Modulpräfix; `tools/test_routine_feed.py::test_a_run_in_an_earlier_week_leaves_the_routine_due`
  existiert (Zeile 124). Scratch-Pfade als Beleg sind hier etablierte Praxis (H135, H136, H141–H143).
* **Naht.** §3 trägt „empfangen bei Zuschnitt — keine", „erwartet beim Merge: G4-1, G4-2", G4-4 „keine",
  und den wörtlichen Satz an G4-1 samt dem Test, der beim Bau des Auslösers rot wird.
* **Suiten in meiner Kopie:** `test_review_procedure` 14 passed, `test_role_contracts` 30 passed,
  `test_shortening_net` 36 passed, `ruff check tools/test_review_procedure.py` „All checks passed!".

## Ausdrücklich NICHT gemessen

* Die **volle Suite** (gehört zum Merge, `DEC-0050`) und die Suiten `test_parallel_streams`,
  `test_reference_skills`, `test_kit_neutrality`, `test_shared_skill_contract`, `test_routine_feed`,
  `tools/validate.py` — die Zahl „193 passed" des Protokolls bleibt insoweit ungeprüft.
* `test_repo_hygiene`: zwei Tests scheitern in meiner Kopie an `git ls-files` (rc 128, kein `.git`) —
  `test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom` und
  `test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at` konnte ich hier nicht
  beurteilen; der für diese Runde entscheidende
  `test_every_test_pointer_this_repo_writes_resolves` lief einzeln: 1 passed in 46,81 s.
* `.claude/hooks/test_gates.py` (unberührter Bereich, nicht gefahren); Haken-Laufzeiten/`timeout` sind
  hier kein Thema, weil keine Registrierung angefasst wurde.
* Ob in einer echten Sitzung die drei Zeilen wirklich beim Nutzer ankommen (kein Live-Lauf eines
  Auditors); ob `office`/`research` sich ebenso sauber scaffolden lassen (nur dev-team gefahren).
* Die Innereien der Rigs des Umsetzers (gelesen, nicht ausgeführt); sein Journal `redfirst.log` habe
  ich nur stichprobenartig gegen zwei eigene Messungen gehalten (Fall 0: „2 failed, 12 passed" —
  identisch reproduziert).

---

## Verdikt

**FAIL.** Der Kern der Runde steht: der Rückschau-Schritt ist in allen drei Kits ein Schritt mit
Anlässen, Fragen und ehrlicher Grenze, dieselbe Aussage steht in der Datei, die ein Spawn wirklich
lädt, die Auftragslesung sitzt in der Sequenz der drei Lead-SKILLs, die fünf Fehlformen tragen je ihr
Entscheidungs-Item, der Patch ist sauber, gestempelt und im Bereich, und die Rot-Messungen des
Umsetzers reproduzieren sich bei mir. Blockierend sind vier Dinge, alle billig zu beheben: eine
Zeigerzeile, die im office-Kit einen Satz zerreißt (B1); zwei Prüfungen, die zählen statt zu
identifizieren, sodass das Löschen einer der drei DEC-0070-Regeln (B3) und das Löschen des gesamten
Lektionsblocks des Umsetzer-Textes (B2) grün bleiben — beides genau die Klasse, die dieses Item
verbietet; und die zweite Hälfte von FR-0084, der verworfene Weg in jedem TSK-Plan, die in keinem Kit
steht, keinen Test hat und in keiner Restliste geführt wird (B4). Dazu fünf Reste, die aufgeschrieben
gehören, allen voran die gemessene Blindheit der Ehrlichkeitsprüfung gegenüber der Schreibweise
`gate_dispatch`, mit der die neuen Blöcke ihre eigene Mechanik benennen (R1).
