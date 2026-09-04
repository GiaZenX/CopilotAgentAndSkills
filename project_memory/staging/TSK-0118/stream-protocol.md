# TSK-0118 — Strom D „Parallele Spezialisten" (FR-0021), Generation 3

Worktree `C:/Offline Repos/v2-testbed/_worktrees/g3-parallel` (Branch `g3/parallel`, Basis
`e45c0ca`). Scratch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0118/`.
Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0118/stream-parallel.patch`.
Provisorischer Stempel nach Nacharbeit 2: dev `2026.09.03-3`, office `2026.09.03-4`, research `2026.09.03-3`.

---

## 0. Vorgefunden (gemessen, bevor eine Zeile geschrieben wurde)

| Frage | Antwort | Wo gemessen |
|---|---|---|
| Was trägt eine Lease heute? | `task_id`, `nonce`, `root_revision`, `created`, `created_epoch`, `ttl`, `agent_id`, optional `checkpoint`, `hand_back`, `references` | `team-kits/kernel/dispatch.py`, `create_lease` |
| Eine Lease pro Instanz? | Ja — eine Lease-Datei je `task_id`; ein zweiter Anspruch auf **dieselbe** Task wird verweigert, zwei verschiedene Tasks laufen parallel | `dispatch.create_lease`, `dispatch.live_leases` |
| Worktree-Pfad auf der Lease? | **Nein** — kein Feld, kein Leser. Gemessen am geschriebenen Lease-Objekt: `tools/test_parallel_streams.py::test_the_lease_carries_no_tree_of_its_own` |
| Nahttabelle als Item-Feld? | **Nein** — `backlog_types.REQUIRED_FIELDS`/`OPTIONAL_FIELDS` für `TSK` kennen kein solches Feld |
| Wer erzwingt `allowed_scope`? | `gate_write_scope` je **gebundenem Spezialisten** gegen **seine eigene** Task; `_matches` ist die laufende Semantik (Präfix; `**` weitet über `/`, ein einzelnes `*` nicht) | `team-kits/dev-team/hooks/gate_write_scope.py` |
| Vergleicht irgendetwas zwei Scopes? | **Nein.** Zwei Aufträge mit demselben `allowed_scope` erreichen beide `LEASED` über den echten Dispatch | `tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` |
| Ist `gate_write_scope.py` gespiegelt? | Ja, byte-identisch in allen drei Kits (nicht in `KIT_SPECIFIC_HOOKS`) — deshalb ist „die Semantik der Kits" **eine** Datei | `tools/test_hooks.py::test_shared_kit_files_identical` |

### Die Messung, die den Zuschnitt dieser Runde entschieden hat (H136)

Ein Prüfskript **im Skill-Verzeichnis** ist im Kit-Projekt **nicht startbar**. Gemessen am
ausgelieferten `gate_write_scope.py` als echtem Hook-Prozess über einem dev-team-Projekt aus den
Kit-Vorlagen (`_round-scratch/TSK-0118/probe_cmdline.py`, `probe_cmdline2.py`):

| Befehlszeile | rc |
|---|---|
| `python .claude/skills/parallel-streams/check_scope_overlap.py` | **2** — „names the enforcement layer in a pipeline that can write" |
| `python .agents/skills/parallel-streams/check_scope_overlap.py` | **2** |
| `python scripts/kit_checks.py` | 0 |
| `python scripts/harness.py check-scopes` | 0 |
| `git ls-files` | 0 |

Folge: die Vor-Dispatch-Prüfung kann aus dem `allowed_scope` dieses Items **nicht** als laufender
Befehl im Kundenprojekt landen. Sie ist als Werkstatt-Instrument gebaut
(`tools/check_scope_overlap.py`) und als **wörtliche Anforderung an Strom C** formuliert (§3).
Der Kit-Text behauptet entsprechend **keine** Durchsetzung.

---

## 1. Plan, und der verworfene Weg in einer Zeile

**Verworfen:** die Prüfung als Skript im Skill-Verzeichnis auszuliefern
(`.claude/skills/parallel-streams/check_scope_overlap.py`) — gemessen rc 2 am ausgelieferten
`gate_write_scope`, also eine Zeile, die niemand ausführen darf.

*(FR-0084 „Rückschau als Ereignis" ist per Nutzerentscheidung 2026-09-03 nicht in diesem Strom.)*

---

## 2. Nahttabelle

**Nahtsätze, die bei Rundenbeginn empfangen wurden: KEINE.**
**Erwartet in der Merge-Runde: von B, C, E.**

| Naht | Stand am Ende dieser Runde |
|---|---|
| Verfassungs-/Rollen-/Skill-Sätze der Ströme A, B, C, E | empfangen: keine; erwartet im Merge: B, C, E. D besitzt die drei Verfassungen, die PM-Skills und `agents/project-auditor.md` und hat sie in dieser Runde angefasst — jeder fremde Satz kommt im Merge dazu |
| Leases/Dispatch für parallele Spezialisten | **D listet, C besitzt** — vier Anforderungen wörtlich in §3, jede mit dem Test, der sie rot macht |
| `docs/POST_V2_WISHLIST.md` | H135, H136, H137 (Tabellenzeile + Detailabschnitt); Einordnung nach Nummer im Merge |
| `team-kits/*/VERSION` | provisorisch (dev -1, office -2, research -1); **ein** Stempel im Merge |
| `tools/constitution_section_pins.json` + Journal in `docs/reviews/phase0-disposition.md` | zweimal neu aufgenommen (7 Abschnitte); im Merge erneut (DEC-0057 (c)) |
| `tools/lead_package_sizes.json` + Journal | zweimal neu aufgenommen (+951 B je Kit, dann −25 B office); im Merge erneut |
| `tools/test_hooks.py` Spiegel-Verzeichnis-Tests | **nicht berührt** — `_shipped_code_dirs()` liest nur `templates/repo/`, und dieser Strom legt dort nichts an |
| `hooks/_routine.py` Modul-Docstring (H137) | **nicht angefasst** (forbidden_scope); Korrektur gehört der Runde, die die Haken besitzt |

---

## 3. Anforderungen an Kernel/Haken — die Naht zu Strom C (wörtlich)

Vier Anforderungen. Jede nennt Feld/Befehl, den Test, der sie rot macht, und warum Text allein
nicht reicht.

### C-1 — Ein Kernel-Verb `check-scopes` hinter `scripts/harness.py`

**Was:** ein Kommando auf der Oberfläche des Einstiegspunkts, das für jedes Paar offener `TSK`
prüft, ob ihre `allowed_scope` minus `forbidden_scope` **einen gemeinsamen Pfad auflösen**, und
mit rc ≠ 0 antwortet, wenn ja. Die Auflösung benutzt **`gate_write_scope._matches`** (bzw. eine
Ableitung, die der Kernel und der Haken gemeinsam lesen) — keine zweite Schreibweise: ein Kernel,
der `fnmatch` benutzt, beantwortet eine andere Frage als der Haken, der die Spezialisten wirklich
anhält. Fertige Vorlage: `tools/check_scope_overlap.py` (Prädikat, zwei Universen, Zeugenbildung,
Naht-Subtraktion), 21 Tests in `tools/test_parallel_streams.py`.

**Test, der ihn rot macht:** zwei durch den Kernel erfasste `TSK` mit demselben `allowed_scope`,
das Verb als Prozess über `scripts/harness.py` gefahren → rc ≠ 0; dieselben zwei mit disjunkten
Scopes → rc 0; ein Paar, dessen einziger gemeinsamer Pfad in einem noch leeren Verzeichnis liegt →
ebenfalls rc ≠ 0 (die Zeugen-Hälfte).

**Warum Text nicht reicht:** gemessen (H136) — ein Skript unter `.claude/skills/` oder
`.agents/skills/` ist rc 2 an `gate_write_scope`, also gibt es aus dem Skill-Verzeichnis heraus
**keinen** ausführbaren Weg. `scripts/harness.py <verb>` ist rc 0 und damit der einzige Weg, der
alle drei Kits mit **einer** Ableitung erreicht. Ein Repo-Skript unter `templates/repo/scripts/`
wäre die Alternative und kostet eine vierte Kopie des Prädikats je Kit.

### C-2 — Eine Verweigerung bei überlappendem Scope in `create_lease`

**Was:** `kernel.dispatch.create_lease` verweigert eine Lease, wenn eine **lebende** Lease einer
anderen Task existiert, deren Auftrag einen gemeinsamen Pfad auflöst — mit einem Remedy, der das
Paar und mindestens einen gemeinsamen Pfad nennt. Heute prüft `create_lease` nur, ob für
**dieselbe** Task schon eine Lease liegt.

**Test, der ihn rot macht:** `tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`
ist heute grün, **weil** es diese Verweigerung nicht gibt — der Test führt zwei Aufträge mit
demselben `allowed_scope` bis `LEASED`. Sobald C-2 gebaut ist, wird er **rot**, und das ist der
Moment, in dem der Verfassungsabsatz („nothing compares two of them") und die Abschnitte 2 und 7
des `parallel-streams`-Skills korrigiert werden müssen. Gemessen als Mutation M13 (die Verweigerung
in einer Kopie außerhalb des Repos eingebaut → 1 failed).

**Warum Text nicht reicht:** der Verfassungsabsatz sagt heute ausdrücklich, dass die Disjunktheit
die Lesung des Leads ist und nichts sie erzwingt. Das ist ehrlich, aber es ist eben keine
Durchsetzung — und ein Schnitt, der einmal falsch gelesen wird, kostet die Merge-Runde.

### C-3 — Ein Worktree-Feld auf der Lease

**Was:** die Lease trägt den Baum, in dem der Auftrag gearbeitet wird (ein Pfad-Feld, vom Lead
beim Minten gesetzt, im Dispatch-Header sichtbar). Heute nennt eine Lease eine Task und keinen
Checkout, also kann kein Leser sagen, welcher Baum zu welchem Auftrag gehört.

**Test, der ihn rot macht:** `tools/test_parallel_streams.py::test_the_lease_carries_no_tree_of_its_own`
liest das geschriebene Lease-Objekt und ist heute grün; mit dem Feld wird er rot, und dann ist der
Abschnitt 7 des Skills („No knowledge of a second tree anywhere in the kernel") zu korrigieren.
Gemessen als Mutation M14.

**Warum Text nicht reicht:** „ein Baum je Auftrag" ist heute allein die Disziplin des Leads; nichts
im Zustand hält fest, welcher das war, und ein abgebrochener Strom ist danach nicht wiederfindbar.

### C-4 — Die Nahttabelle als Item-Feld (`seam_scope`)

**Was:** ein optionales Feld am `TSK` (Liste von Scope-Einträgen), das die Dateien nennt, die
**absichtlich** geteilt sind und in der Merge-Runde angewendet werden. Die Prüfung aus C-1
subtrahiert es, bevor sie ein Paar beurteilt.

**Test, der ihn rot macht:** `tools/test_parallel_streams.py::test_a_declared_seam_is_shared_on_purpose_and_does_not_fail_the_check`
misst heute genau dieses Verhalten — über ein **Kommandozeilen-Argument** `--seam`, weil das Feld
nicht existiert. Der Test für C-4: dasselbe Paar, die Naht **am Item** statt auf der Kommandozeile
→ rc 0 und die Naht wird gedruckt; ohne das Feld → rc 2.

**Warum Text nicht reicht, und die Messung, die es zeigt:** der echte Generation-3-Schnitt
(TSK-0115..0119 im Hauptrepo) meldet **zehn von zehn Paaren** als überlappend, solange die Naht
nicht deklariert ist — auf `docs/**`, `tools/**` und `team-kits/*/VERSION`. Mit
`--seam "docs/**" "tools/**" "team-kits/*/VERSION"` sind **alle zehn Paare disjunkt** (rc 0). Das
Logbuch der Generation nennt genau diese drei als Naht; `allowed_scope` kann es nicht ausdrücken,
also steht die Naht heute in einer Markdown-Datei, die kein Programm liest.

---

## 4. Was gebaut wurde, je erwartetem Ergebnis

### (1) FR-0021 — das PM-Verfahren für parallele Spezialisten

**(a) Verfahrens-Skill** `team-kits/dev-team/skills/parallel-streams/SKILL.md` (Referenz-Skill nach
Verfassung §1a, `reference_for.roles: [project-manager]`, `task_types` = die ganze Kernel-Sprache).
Sieben Abschnitte: Schnitt nach Dateibesitz und Gruppierung; die Prüfung vor dem Dispatch samt der
Aussage, dass nichts sie erzwingt; ein Baum je Auftrag; nur die Prüfungen, die die geänderten
Dateien lesen; kein Commit aus einem Strom, ein Stempel; die Naht vor dem Start benennen; der Merge
als eigene Prüfung; und ein Abschnitt „was dieses Verfahren NICHT gibt".

**(b) Verfassungsabschnitt** — ein Absatz mit fettem Lead-in, **byte-identisch in allen drei
Verfassungen**, angehängt an den Arbeitsschleifen-Abschnitt (dev §5a, office §4a, research §5a).
Er trägt die kit-unabhängige Regel und **keine** Skill-Route (office liefert den Skill nicht; eine
Route dort wäre ein toter Zeiger, gehalten von
`tools/test_reference_skills.py::test_every_skill_retrieval_route_a_shipped_kit_file_spells_resolves`).

**(c) PM-Skill-Zeilen** — im DELEGATE-Schritt der drei Lead-Skills: dev und research mit der Route
`/parallel-streams` (+ Codex-Pfad), office mit derselben Regel ohne Route und mit dem Satz, dass
dieses Kit kein Verfahrensdokument dafür liefert.

**Zwei Deckel, keine Zahl — und in der ersten Fassung stand nur einer davon da.** Das Item und
`DEC-0063` (2) deckeln die ANZAHL gleichzeitiger Ströme; mein erster Kit-Text deckelte nur die
GRÖSSE eines Auftrags und dieser Absatz behauptete trotzdem, der Anzahl-Deckel stehe als
Eigenschaft da (Befund M2 der ersten Prüfung). Nacharbeit 1 setzt beide in den geteilten
Verfassungsabsatz und in §1 des Skills, beide ohne Zahl: „so viele Ziele GLEICHZEITIG, wie du
durch ihre Nacharbeitsrunden tragen kannst" und „kein Ziel größer als ein Bau-Durchgang und ein
Prüf-Durchgang". Die Zahl „4–5" bleibt in `DEC-0063` und wird nicht ins Kit kopiert: ein
Kundenprojekt hat diese Entscheidung nicht, und eine zweite Zahl daneben wäre die nächste, die rottet.

### (2) DEC-0062 (6) — die Vor-Dispatch-Prüfung, an einer Pilotkopie gemessen

`tools/check_scope_overlap.py`. **Ein Prädikat, zwei Universen:**
`gate_write_scope._matches` (importiert, nicht nachgebaut) entscheidet „gehört dieser Pfad diesem
Auftrag", gefragt über (a) die Dateien, die `git ls-files -c -o --exclude-standard` im Baum findet,
und (b) je einen **Zeugen** pro Scope-Eintrag (jeder Wildcard-Lauf wird EIN Platzhalter-Segment),
damit ein noch leeres Verzeichnis, das zwei Aufträge beanspruchen, nicht unsichtbar ist.
`--seam` subtrahiert erklärte Nähte. rc 0 disjunkt / rc 2 Überlappung.

Gemessen am **echten Generation-3-Schnitt** (Hauptrepo, nur gelesen): 10/10 Paare überlappen ohne
Naht-Erklärung, 0/10 mit den drei erklärten Nähten. Und an einem Piloten aus den Kit-Vorlagen: die
fünf Fälle in §5.

### (3) Der Abschnitt steht in allen drei Verfassungen

Byte-identisch; gehalten von `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`
(die Lead-in-Regel aus Generation 2, Strom E) und von
`tools/test_shortening_net.py::test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`
(der Abschnitts-Digest — ein Löschen des Absatzes ist dort rot). Rot gemessen als M11.

**Naht-Sätze anderer Ströme (A, B, C, E): bei Schnitt keine empfangen; erwartet im Merge von B, C, E.**

### (4) N2 geschlossen

Die `description`-Zeile der drei `agents/project-auditor.md` verliert „weekly / event-triggered" —
denselben Takt, den ihr eigener Rumpf seit E3 im Code verortet. Zusätzlich verliert die
Rollenzeile der Office-Verfassung dieselbe Wendung, weil sie derselbe zweite Ort war.
Der **bestehende** Rollentext-Test sah das nicht (er misst Beschreibung↔Skill-Aufteilung, nicht
„zweimal derselbe Fakt"), also hat diese Runde den Fall **rot zuerst** dazugebaut:
`tools/test_parallel_streams.py::test_no_text_that_describes_the_audited_role_states_the_cadence_the_code_owns`
— Subjekt abgeleitet aus `_routine.AUDIT_ROLE`, Texte = die Rollendatei plus jeder
Verfassungs-Block, der die Rolle nennt; Leser-Boden als eigener parametrisierter Test.

---

## 5. Abnahmezeilen je FR und die roten Tests

**FR-0021 — Abnahme:** der dev-Kit-PM hat ein Verfahren für parallele Spezialisten, das (i) nach
Dateibesitz schneidet, (ii) Anforderungen mit gemeinsamen Dateien in EINEN Auftrag gruppiert,
(iii) nach einem Bau- und einem Prüf-Durchgang deckelt, (iv) `allowed_scope` je Auftrag auf
Dateiebene disjunkt fordert **und vor dem Dispatch prüfbar macht**, (v) einen Baum je Strom,
(vi) nur betroffene Prüfungen im Strom, (vii) den Merge als eigene Prüfung mit Nahttabelle,
(viii) einen Stempel — und der **nichts behauptet, was kein Code baut**.

**N2 — Abnahme:** die `description` der drei `project-auditor.md` und der Rumpfsatz derselben
Datei widersprechen einander nicht mehr; der Takt steht an genau einer Stelle
(`_routine.audit_period_id`), und dass kein Rollen- oder Verfassungstext ihn ein zweites Mal nennt,
ist gemessen.

### Rot-zuerst: 16 Mutationen, jede in einer Kopie AUSSERHALB des Repos gefahren

`_round-scratch/TSK-0118/redfirst.py` + `redfirst2.log`; Kopie ohne `.git` unter
`_round-scratch/TSK-0118/redfirst/`. Jede Zeile: grün vorher → **rot mutiert** → grün nach dem
Zurücksetzen.

| # | Wiederhergestellter Defekt | Roter Test |
|---|---|---|
| M1 | Zeugen-Hälfte entfernt | `test_an_overlap_in_a_directory_that_is_still_empty_is_refused` |
| M2 | `_matches` durch `fnmatch` ersetzt | `test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling` |
| M3 | erklärte Naht nicht subtrahiert | `test_a_declared_seam_is_shared_on_purpose_and_does_not_fail_the_check` |
| M4 | `forbidden_scope` nicht zuerst gefragt | `test_a_forbidden_scope_takes_the_file_back_out_of_the_overlap` |
| M5 | terminale Aufträge nicht übersprungen | `test_the_check_reads_the_orders_that_are_still_open` |
| M6 | N2 in EINER Auditor-`description` zurück | `test_no_text_that_describes_the_audited_role_states_the_cadence_the_code_owns` |
| M7 | N2 in der Office-Rollenzeile zurück | dito |
| M8 | `/humanizer`-Route aus dem Office-Lead-Skill entfernt | `test_a_reference_skill_named_for_a_session_agent_is_named_by_a_text_it_reads` |
| M9 | `/parallel-streams`-Route aus dem dev-PM-Skill entfernt | dito |
| M10 | ein `task_type` aus der Deklaration entfernt | `test_the_parallel_procedure_is_declared_for_every_task_type` |
| M11 | Verfassungsabsatz in EINEM Kit abweichend | `test_role_contracts::test_a_paragraph_the_constitutions_share_is_one_text` **und** `test_shortening_net::test_no_section_of_a_pinned_instruction_file_disappears_unnoticed` |
| M12 | research-Kopie des Skills gelöscht | `test_shared_skill_contract::test_a_reference_skill_ships_in_every_kit_that_ships_a_role_it_names` |
| M13 | eine Scope-Verweigerung IST gebaut | `test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap` (der Test, der die Kit-Behauptung trägt) |
| M14 | die Lease bekommt ein Baum-Feld | `test_the_lease_carries_no_tree_of_its_own` |
| M15 | `sys.dont_write_bytecode` entfernt | `test_hooks_v2::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` **und** `test_the_checker_leaves_no_bytecode_in_the_kit_tree_it_imports` |
| M16 | leerer Wurzelpfad meldet „disjoint" | damals test_a_root_with_nothing_to_compare_never_says_disjoint (kein Zeiger mehr — den Namen gibt es nicht), heute `test_a_route_the_caller_named_has_to_resolve_and_one_nobody_named_does_not` (Nacharbeit 1 hat den Test um die `--only`-Achse erweitert und dabei umbenannt) |

---

## 6. Gemessene Zeilen (vorher → nachher)

| Was | Vorher | Nachher |
|---|---|---|
| `agents/project-auditor.md:3` (x3) | `description: "Project Auditor — weekly / event-triggered READ-ONLY reviewer, …` | `description: "Project Auditor — READ-ONLY reviewer, …` |
| `office-team/constitution/AGENTS.md:287` | `- **project-auditor:** weekly / event-triggered READ-ONLY reviewer — samples …` | `- **project-auditor:** READ-ONLY reviewer — samples …` |
| Verfassungen dev/office/research | kein Absatz zum parallelen Schnitt | ein byte-identischer Absatz am Ende der Arbeitsschleife |
| Lead-Paket | dev 45512 / office 52167 / research 48528 B | dev 46463 / office 53093 / research 49479 B |
| Kit-Stempel | dev/office `2026.09.02-12`, research `-11` | dev `2026.09.03-1`, office `2026.09.03-2`, research `2026.09.03-1` (provisorisch) |
| Generation-3-Schnitt, geprüft | ungeprüft | 10/10 Paare überlappen ohne Naht-Erklärung, 0/10 mit den drei erklärten Nähten |

---

## 7. Was bewusst NICHT geschlossen, aber benannt ist

1. **H136 — die Prüfung hat im Kundenprojekt keinen ausführbaren Weg.** Gemessen (§0). Beide
   Orte, die rc 0 bleiben, liegen im `forbidden_scope` dieses Items. Anforderung C-1.
2. **H135 — die Zeugen-Hälfte ist eine Stichprobe, keine Sprache.** `a/*x` gegen `a/y*`: rc 0 bei
   leerem `a/`, rc 2 sobald `a/yx` existiert (`probe_h135.py`). Der Docstring von `witnesses` nennt
   genau diese Grenze.
3. **H137 — `hooks/_routine.py` behauptet einen Takt in „jeder Verfassung".** Nach dieser Runde
   nennt ihn keine. Datei ist forbidden_scope und dreifach gespiegelt.
4. **Keine Naht-Anwendung, kein Merge-Werkzeug.** Das Verfahren beschreibt die Merge-Runde; nichts
   in dieser Lieferung führt sie aus. Bewusst: der Merge ist nach DEC-0057 (e) eine eigene Runde.
5. **FR-0022 (menschliche Namen für Instanzen)** ist referenziert, nicht gebaut — Nutzerentscheidung
   2026-09-02: zusammen mit der Oberfläche (FR-0024).
6. **FR-0084 (Rückschau als Ereignis)** ist nicht in diesem Strom (Nutzerentscheidung 2026-09-03,
   Generation 4).
7. **Das Office-Kit liefert kein `parallel-streams`-Verzeichnis.** Der Verfassungsabsatz gilt dort,
   das Verfahrensdokument fehlt; der `office-manager`-Skill sagt das ausdrücklich. Grund: die
   Deklaration nennt `project-manager`, und die Präsenzregel
   (`test_a_reference_skill_ships_in_every_kit_that_ships_a_role_it_names`) verpflichtet damit dev
   und research, nicht office.

### Abweichung vom Item, benannt

Das Item nennt `team-kits/dev-team/skills/parallel-streams/**` im `allowed_scope`. Geliefert wird
zusätzlich **`team-kits/research-team/skills/parallel-streams/SKILL.md`, byte-identisch** — nicht
aus Geschmack, sondern weil der ausgelieferte Kit-Vertrag es verlangt: die Deklaration nennt
`project-manager`, dev **und** research liefern eine Rolle dieses Namens, und
`tools/test_shared_skill_contract.py::test_a_reference_skill_ships_in_every_kit_that_ships_a_role_it_names`
wird ohne die Kopie rot (Mutation M12, gemessen). Die Alternativen waren: eine Deklaration, die
`project-manager` verschweigt und stattdessen Ausführer-Rollen aufzählt, um die Spiegelpflicht zu
umgehen — eine Aufzählung, deren Auswahlkriterium der Scope dieses Items gewesen wäre —, oder den
Skill entgegen dem Item in das PM-Skill-Verzeichnis zu legen. Beide sind schlechter; die Kopie ist
gemeldet statt versteckt.

### Nebenkorrekturen im `allowed_scope`, benannt

* Die drei Lead-Skills nennen jetzt die Route zu `/humanizer`. Vorher nannte sie **kein** Text, den
  ein Lead liest, während `humanizer` beide Kit-Leads deklariert und deren Kommentar behauptet,
  „nur der eigene Text schickt es dorthin". Gemessen und mit
  `test_a_reference_skill_named_for_a_session_agent_is_named_by_a_text_it_reads` beidseitig gehalten
  (M8).
* `tools/test_routine_feed.py`s Modul-Docstring behauptete „all three constitutions ride it on a
  weekly rhythm" — falsch für dev und research (gemessen). Korrigiert auf die Stelle, die den Takt
  wirklich trägt.

---

## 8. Läufe (nur betroffene Suiten — die volle Suite gehört in die Merge-Runde, DEC-0050/DEC-0063)

| Lauf | Ergebnis | Dauer |
|---|---|---|
| `tools/test_parallel_streams.py` (neu) | **21 passed** | 29 s |
| `tools/test_role_contracts.py`, `test_shared_skill_contract.py`, `test_kit_neutrality.py`, `test_routine_feed.py`, `test_model_pins.py`, `test_presets.py`, `test_parallel_streams.py` | **129 passed** | 2:18 |
| `tools/test_reference_skills.py` (nach dem Stempel) | **18 passed** | 1:02 |
| `tools/test_shortening_net.py`, `test_context_budget.py`, `test_disposition.py` (nach den Ratschen) | **86 passed** | 55 s |
| `tools/test_repo_hygiene.py`, `test_disposition.py`, `test_kitupdate.py` | **115 passed, 1 skipped** | 6:16 |
| `tools/test_hooks.py` | **902 passed, 13 skipped** | 20:18 |
| `tools/test_hooks_v2.py` (1. Lauf) | 2136 passed, **1 failed** — `test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it`: der neue Prüfer schrieb Bytecode in den Kit-Baum und beendete sich in einem Verzeichnis ohne Zustand mit rc 1 | 16:31 |
| `tools/test_hooks_v2.py` (2. Lauf, nach dem Fix, VOLL) | **2137 passed** | 15:53 |
| `.claude/hooks/test_gates.py` (voll — die Löcherliste hat sich geändert) | **489 passed** | 15:24 |
| `python -m ruff check .` | all checks passed | — |
| `python tools/validate.py` | all structural checks passed | — |
| `tools/bump_kit_version.py` | dev `2026.09.03-1`, office `2026.09.03-2`, research `2026.09.03-1` | — |

Der Befund des ersten `test_hooks_v2`-Laufs war ein **echter Defekt dieser Runde** und ist nach
DEC-0063 (4) mit vollen Läufen der lesenden Suite nachgefahren: `sys.dont_write_bytecode = True`
im Prüfer, und „nichts zu vergleichen" ist jetzt rc 0 mit einer Meldung, die das Wort „disjoint"
nicht enthält (M15, M16 rot gemessen).

---

## 8a. Der Patch

`_round-scratch/TSK-0118/stream-parallel.patch`, nach Nacharbeit 2 **129 622 Bytes, 18 Dateien, +1537/−17**
(erzeugt von `make_patch.py`, BYTES statt `text=True` — der erste Versuch dekodierte git's UTF-8
mit der Windows-Codepage und doppelt-kodierte jedes `ü`, was `git apply --check` scheitern ließ).

**Nicht im Patch, mit Grund:**
* `project_memory/.audit/hook_events.jsonl` — der Worktree hat eigene Haken laufen lassen; nie Teil
  eines Strom-Patches.
* `team-kits/*/VERSION` — provisorisch je Strom, EIN Stempel in der Merge-Runde (Nahttabelle der
  Generation 3). Die Stempel stehen oben, damit die Merge-Runde sie kennt.

**Gemessen (Stand nach Nacharbeit 1):** auf einem sauberen `e45c0ca`-Baum (aus dem Objektspeicher
per `git archive HEAD` ausgepackt) `git apply --check` **rc 0**, danach `git apply` rc 0; die
beiden Skill-Kopien sind nach dem Anwenden byte-identisch (9345 B); `tools/test_parallel_streams.py`
auf dem frisch gepatchten Baum **28 passed**. Der Patch ist also in sich geschlossen.

**Prüfer-Hinweis:** `_round-scratch/TSK-0118/redfirst.py` legt seine Kopie außerhalb des Repos
selbst an (ohne die `.git`-Datei des Worktrees) und fährt alle 16 Mutationen; `redfirst3.log` ist
der Lauf mit dieser Fassung. `apply_check.py` baut den sauberen `e45c0ca`-Baum aus dem
Objektspeicher und wendet den Patch an.

**Selbstprüfung am Ende der Runde, mit einem eigenen Befund.**
`_round-scratch/TSK-0118/check_refs.py` löst jeden Testnamen auf, den die in dieser Runde
geschriebenen oder geänderten Texte in Backticks nennen (138 Spannen, gegen die Parse-Bäume von
`tools/*.py` und `.claude/hooks/*.py`). Erster Lauf: **ein** Name löste nicht auf — der Kopf von
`tools/check_scope_overlap.py` nannte
tools/test_parallel_streams.py::test_the_matcher_is_the_shipped_gates_own (absichtlich ohne Backticks zitiert — der Name löst nicht auf, das war der Befund), während der Test
`…_and_not_a_second_spelling` heißt. Korrigiert; zweiter Lauf sauber (die einzige verbleibende
Meldung ist `test_strategy` in der dev-Verfassung — ein YAML-Feldname, älter als diese Runde,
`git diff` zeigt ihn nicht). **`check_refs.py` ist ein Rundeninstrument und kein ausgelieferter
Wächter:** unter `tools/` prüft heute nichts, ob ein Testname in einem Docstring auflöst.
Die Gate-Suite hat dafür ZWEI Prüfer, und beide lesen woanders (Korrektur des Befunds N1 der
ersten Prüfung — hier stand „ausschließlich die Löcherliste"): `test_gates.py::test_every_test_the_hole_list_names_is_one_that_exists`
über `docs/POST_V2_WISHLIST.md` und `test_gates.py::test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`
über die Quellen unter `.claude/hooks/`. Ein `tools/`-Docstring liegt in keinem der beiden Subjekte.

## 10. Nacharbeit 1 (2026-09-03) — die neun Befunde der ersten Prüfung

### B1 — der Prüfer las `_matches`, aber nicht die Normalisierung, mit der das Gate ihn füttert

**Mechanismus.** `gate_write_scope` ruft `_matches` nie auf rohen Wörtern: der Eintrag kommt
aus `_scope_entries` (`_norm(entry)`), der Pfad aus `_repo_relative(..., fold=True)` (`_norm(rel)`),
und `_norm` ist normcase + Schrägstriche + `.lower()`. Ich hatte die Hälfte importiert und
die andere weggelassen — also beantwortete mein Prüfer eine andere Frage als die Tür.

**Gemessen** (`_round-scratch/TSK-0118/probe_b1.py`, beide Aufträge durch den Kernel erfasst,
`tools/foo.py` im Baum): `allowed_scope ["Tools/**"]` gegen `["tools/**"]`
— **vorher rc 0** („disjoint“), **nachher rc 2** mit `file tools/foo.py`. Die
Gegenrichtung liegt schon im Baum:
`tools/test_hooks_v2.py::test_a_case_mismatched_scope_entry_still_matches`.

**Fix.** `matcher()` gibt jetzt einen Wrapper zurück, der BEIDE Argumente durch
`gate_write_scope._norm` schickt; der Kopf der Datei sagt, dass das Prädikat aus zwei Hälften
besteht. Rot ohne den Fix: `R1` der Mutationsreihe. **N3** ist mitgeschrieben: §2 des Skills
sagt jetzt, dass beide Seiten fallgefaltet werden und `Tools/**` und `tools/**` an der Tür EIN
Scope sind.

### M1 — die Bündelung gehört auf die Ebene des PRODUKTZIELS (`DEC-0067`)

Meine erste Fassung schrieb `DEC-0062` (2) fort: mehrere Anforderungen in EINEM Arbeitsauftrag. Der
Nutzer hat das eine Stunde nach meinem Schnitt anders entschieden. Umgeschrieben an den acht
Stellen, die die Prüfung nennt — Skill §1 (beide Kopien), die drei Verfassungsabsätze,
die drei Lead-Skills:

* Wünsche, deren Dateilisten sich überschneiden, werden **bei der Sichtung in EIN Ziel**
  eingearbeitet; der Wunsch endet terminal mit seinem Zeiger auf das Ziel, und was er verlangt hat,
  wird Teil dessen, woran das Ziel gemessen wird. Das Ziel bekommt **einen** Arbeitsauftrag.
* Die Gegenrichtung steht ausdrücklich da: mehrere Anforderungen in einem Auftrag sind der Zug,
  den dieses Verfahren verbietet — der Kernel gibt einem Auftrag genau ein Ziel
  (`product_requirement`), also lebt jede weitere Anforderung in Prosafeldern und ist für Index,
  Board und jede Auswertung unsichtbar.
* Der geteilte Verfassungsabsatz bleibt kit-neutral („Ziel“ statt `PR`), weil er
  byte-identisch in drei Kits steht und die drei Kits verschiedene Wurzeltypen haben; die
  **Lead-Skills nennen den eigenen Typ**: dev `PR`, research `RQ`, office `PROC`.
* §2 des Skills sagt jetzt, dass die Vor-Dispatch-Prüfung über die Aufträge dieser
  Ziele läuft — einer je Ziel.

**Was diese Aussage hält, ehrlich gesagt:** kein Test. Sie ist Prosa in einem Kit-Text. Gehalten
sind nur ihre Träger — die Spiegelregel (beide Skill-Kopien byte-identisch, `R8` rot), die
Lead-in-Regel (der Absatz identisch in allen drei Verfassungen, `R9` rot) und der Abschnitts-Pin.

### M2 — der zweite Deckel fehlte

Siehe die korrigierte Stelle in §4. Beide Deckel stehen jetzt als Eigenschaft ohne Zahl.

### M3 / M4 / M5 — zwei gebaut, drei benannt

| Befund | Entscheidung | Warum |
|---|---|---|
| **M3** Takt-Leser ist eine Adverb-Aufzählung | **Loch `H141`** + Docstring auf die richtige Klasse + fünf blinde Formen als eigene Testzeilen | „ist dieser Satz eine Taktangabe“ ist Weltwissen; eine größere Liste wäre derselbe Defekt eine Runde später |
| **M4** jede Route unter zwei Aufträgen endete rc 0 | **gebaut**: was der Aufrufer GENANNT hat, muss auflösen (rc 1); was niemand genannt hat, bleibt rc 0. Rest als `H142` | ein Tippfehler in `--root`/`--only` ist genau der Bedienfehler, den die Prüfung verhindern soll; rc 1 für ALLES hätte den argumentlosen Lauf gebrochen, den `tools/test_hooks_v2.py::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` fährt |
| **M5** eine zu weite Naht macht jede Kollision zu „seam only“ | **gebaut**: eine Naht, die die GESAMTE Ownership eines der beiden Aufträge deckt, wird verweigert (rc 1). Rest als `H143` | die vom Prüfer vorgeschlagene Fassung („deckt einen ganzen `allowed_scope`-Eintrag“) hätte die legitime Naht `team-kits/*/VERSION` verweigert — sie IST in den Generation-3-Items ein ganzer Eintrag. „Lässt einen Auftrag ohne Ownership zurück“ trennt beide Fälle sauber und ist beidseitig gemessen |

Messungen dazu (`_round-scratch/TSK-0118/probe_m4_m5.py`, `probe_h141.py`):
`--root <pfad>-typo` 0→1, `--only TSK-0001 TSK-0404` 0→1, `--only TSK-0001` bleibt 0,
argumentloser Lauf außerhalb eines Projekts bleibt 0; `--seam "**"` und `--seam "src/**"` über
zwei Aufträgen auf `src/**` 0→1, die Scheiben-Naht `notes/holes.md` bleibt 0.
`weekly` feuert, `runs once a week` / `on Mondays` / `every seven days` / `runs each Monday morning`
/ `cadence: 7d` / `wöchentliche` bleiben still.

**Die Generation-3-Messung hält auch nach M5:** mit den drei erklärten Nähten
(`docs/**`, `tools/**`, `team-kits/*/VERSION`) bleibt der Schnitt rc 0 — keiner der fünf
Aufträge verliert seine ganze Ownership an die Naht, weil jeder auch Kit-Dateien besitzt.

### N1 / N2 / N3

N1 in §8a korrigiert (zwei Namensprüfer, zwei Subjekte). N2: der Patch lässt
`team-kits/*/VERSION` weiterhin weg — nach `DEC-0057` (d) und der Nahttabelle der Generation 3
richtig; die Stempel stehen im Kopf dieses Protokolls, damit die Merge-Runde sie liest. N3 ist in
B1 mitgeschrieben.

### Rot zuerst: 10 weitere Mutationen (`_round-scratch/TSK-0118/redfirst_rw1.py`, `redfirst_rw1.log`)

| # | Wiederhergestellter Defekt | Roter Test |
|---|---|---|
| R1 | der Matcher faltet nicht mehr | `test_two_orders_whose_scope_entries_differ_only_in_case_are_refused` |
| R2 | Matcher durch `fnmatch` ersetzt | `test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling` |
| R3 | genanntes `--root` ohne Verzeichnis wieder rc 0 | `test_a_route_the_caller_named_has_to_resolve_and_one_nobody_named_does_not` |
| R4 | unbekannte `--only`-Id wieder rc 0 | dito |
| R5 | auch die Standardwurzel wird rc 1 (Über-Verweigerung) | dito **und** `test_hooks_v2::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` |
| R6 | die schluckende Naht wieder akzeptiert | `test_a_seam_that_swallows_an_orders_whole_ownership_is_refused` |
| R7 | auch die Scheiben-Naht verweigert (Über-Verweigerung) | dito |
| R8 | der Skill bündelt wieder im Auftrag (nur eine Kopie) | `test_shared_skill_contract::test_a_skill_shipped_by_several_kits_is_one_directory_in_all_of_them` |
| R9 | der Verfassungsabsatz driftet in EINEM Kit | `test_role_contracts::test_a_paragraph_the_constitutions_share_is_one_text` **und** `test_shortening_net::test_no_section_of_a_pinned_instruction_file_disappears_unnoticed` |
| R10 | der Takt-Leser behauptet eine Grenze, die er nicht hat | `test_the_cadence_reader_reads_what_it_claims` |

Die 16 Mutationen der ersten Runde sind gegen den nachgearbeiteten Baum **erneut** gefahren
(`redfirst4.log`, zwei Selektoren nachgezogen: `M2` auf den neuen Wrapper, `M16` auf den
umbenannten Test) — alle 16 wieder rot und zurückgesetzt.

### Läufe der Nacharbeit 1

| Lauf | Ergebnis | Dauer |
|---|---|---|
| `tools/test_parallel_streams.py` (jetzt 27 Tests) | **27 passed** | 12 s |
| Text/Vertrag-Batch: `test_role_contracts`, `test_shared_skill_contract`, `test_reference_skills`, `test_shortening_net`, `test_context_budget`, `test_disposition`, `test_routine_feed`, `test_kit_neutrality`, `test_parallel_streams` | **202 passed** | 3:26 |
| Löcherlisten-Prüfer der Gate-Suite (beide, namentlich) | **2 passed** | 3 s |
| `tools/test_hooks_v2.py` (voll) | **2137 passed** | 15:14 |
| `tools/test_hooks.py` (voll) | **902 passed, 13 skipped** | 15:50 |
| `ruff`, `validate.py` | sauber | — |
| Stempel (provisorisch) | dev `2026.09.03-2`, office `2026.09.03-3`, research `2026.09.03-2` | — |
| Ratschen | Lead-Paket +482 B je Kit; 6 Abschnitts-Pins neu | — |
| `check_refs.py` (Rundeninstrument) | 151 Spannen, **ein** toter Zeiger gefunden und korrigiert (der Kommentar in `check_scope_overlap.py` nannte noch den Test, den diese Nacharbeit umbenannt hat) | — |
| Patch neu | **124 745 B, 18 Dateien, +1482/−17**; `git apply --check` auf sauberem `e45c0ca` rc 0, Spiegel danach byte-identisch (9244 B), `test_parallel_streams` auf dem gepatchten Baum **27 passed** | — |

## 11. Nacharbeit 2 (2026-09-03) — die vier Abschlusszeilen der Wiederholungsprüfung

Urteil der Wiederholungsprüfung: **PASS** (0 B / 0 M / 4 N). Der Prüfer nimmt seinen
M5-Vorschlag ausdrücklich zurück — „deckt einen ganzen `allowed_scope`-Eintrag“
hätte die legitime Naht `team-kits/*/VERSION` verweigert; die gebaute Form („lässt
einen Auftrag ohne Ownership zurück“) bleibt.

**N4 — ein Zeiger in der Mutationstabelle der ersten Runde.** Die M16-Zeile nannte noch den
Testnamen von damals. Sie führt ihn jetzt als historisches Zitat **ohne Backticks** (er
löst nicht mehr auf) und daneben den heutigen Namen. Der Mechanismus hinter dem Treffer ist
mitgeschlossen: `check_refs.py` liest jetzt **das ganze Protokoll**, nicht nur die Abschnitte der
laufenden Runde — genau dort saß der tote Zeiger. Der Leser überspringt seitdem
MODUL-Namen (`test_role_contracts` zeigt auf eine Datei) und nennt in seinem eigenen Kopf, was er
nicht unterscheiden kann: ein Bezeichner, der aussieht wie ein Testname. Lauf danach: **203
Spannen, ein einziger Dauer-Treffer** — `test_strategy`, ein YAML-Feld des
Architektur-Vertrags, älter als diese Runde.

**N5 — zwei fehlende Zeiger.** `overlaps` nennt jetzt `H143` (was eine Naht schmäler als
die Überlappung weiter zudeckt), `ownership_left` nennt `H143` und `H142` (die Wege, die ohne
Vergleich enden). Damit steht in jedem der drei Docstrings, die eine Grenze haben, der Eintrag mit
der Kette — derselbe Standard wie bei `witnesses` und `H135`.

**N6 — eine Zahl an zwei Orten.** „All six were measured quiet“ bei fünf
Testzeilen ist raus; der Docstring sagt jetzt „every form named here“, die
Löcherliste „die blinden Formen“ ohne Zählung. Die Formen selbst stehen einmal:
in der Tabelle von `H141`.

**N7 — die Kernel-Behauptung des Verfassungsabsatzes ist jetzt gemessen.** Der Absatz sagt,
der Kernel gebe einem Arbeitsauftrag genau ein Ziel. Neuer Test
`tools/test_parallel_streams.py::test_a_work_order_carries_exactly_one_product_requirement`:
`product_requirement` steht in `REQUIRED_FIELDS["TSK"]` **und** in `PARENT_FIELDS["TSK"]`, und der
laufende Produzent `dispatch.create_task` nimmt eine Id und **verweigert eine Liste**. Gemessen
(`_round-scratch/TSK-0118/probe_n7.py`): eine Liste endet im Id-Parser (`TypeError`), eine Id
ergibt `TSK-0001` — die Verweigerung ist unschön, und genau so sieht „kann es nicht
darstellen“ aus. Der Absatz in allen drei Verfassungen und der Skill-Absatz nennen den Test,
also wird die Behauptung sichtbar falsch, sobald der Kernel mehrere Ziele lernt.
**Rot zuerst (R11, `redfirst_rw2.py`):** in einer Kopie außerhalb des Repos nimmt
`create_task` eine Liste an, indem es das erste Element zieht → **1 failed**; zurückgesetzt
→ 1 passed.

### Läufe der Nacharbeit 2 (nur die lesenden Tests, wie beauftragt)

| Lauf | Ergebnis | Dauer |
|---|---|---|
| `tools/test_parallel_streams.py` (jetzt 28 Tests) | **28 passed** | 15 s |
| die beiden Löcherlisten-Prüfer aus `test_gates.py`, namentlich | **2 passed** | 2 s |
| `ruff`, `validate.py` | sauber | — |
| Stempel (provisorisch) | dev `2026.09.03-3`, office `2026.09.03-4`, research `2026.09.03-3` | — |
| Ratschen | Lead-Paket +101 B je Kit; 3 Abschnitts-Pins | — |
| `check_refs.py` | 203 Spannen, 1 bekannter Dauer-Treffer (`test_strategy`) | — |

**Keine volle `test_hooks`/`test_hooks_v2`-Runde**, wie beauftragt: die Änderungen dieser
Nacharbeit sind ein neuer Test in `tools/`, zwei Docstring-Zeiger, eine Zahl weniger und ein
Halbsatz in den drei Verfassungen plus dem Skill. Die Suiten, die diese Dateien lesen und in
Nacharbeit 1 voll grün waren, lesen sie unverändert weiter — die Merge-Runde fährt
den vollen Lauf.

## 9. Für die (g)-Tabelle

* Stufe: Opus (Implementer).
* Wanddauer Spawn → dieser Bericht: siehe Rundenprotokoll des Leads; die Suiten-Läufe allein
  summieren ~62 min (test_hooks 20:18, test_hooks_v2 16:31 + Wiederholung, test_gates 15:24,
  Hygiene 6:16, Rest ~5 min).
* Erst-Prüf-Befunde: vom Prüfer einzutragen.
