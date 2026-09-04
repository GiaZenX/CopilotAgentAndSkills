# TSK-0120 — Merge-Runde der Generation 3 (DEC-0062, DEC-0063, DEC-0064..DEC-0069)

Umsetzer: `harness-implementer` (Opus). Arbeitsbaum: `C:\Offline Repos\AgentAndSkills`, Branch
`feat/harness-v2`, Basis `e45c0ca`. Rundenverzeichnis außerhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0120\`.

Kein Commit, kein Push, keine Installation. Der Lead trägt das `EVD` ein und committet nach dem
PASS des Merge-Prüfers.

**Der verworfene Weg dieses Merge-Plans, in einer Zeile (FR-0084-Form):** die fünf Patches mit
`git merge` über fünf Branches zusammenführen statt sie in Naht-Reihenfolge anzuwenden — verworfen,
weil ein Merge-Commit die Nähte automatisch „löst" und damit genau die Prüfung überspringt, die
DEC-0063 (1) zur eigenen Prüfrunde erklärt.

---

## 0. Ausgangsmessung

```
git rev-parse --abbrev-ref HEAD -> feat/harness-v2
git rev-parse HEAD              -> e45c0ca6099b6ff7f45d3e57497a6dd183ead890
git status --short               -> außerhalb project_memory/ LEER
```

**Zeilenenden, vor dem ersten `apply` gemessen** (`git ls-files --eol`, die Autorität, nicht ein
Grep über die Bytes):

| Menge | Zahl |
|---|---|
| verfolgte Dateien mit `w/crlf` oder `w/mixed` | 39 |
| davon außerhalb des Zustandsverzeichnisses `project_memory/` | **35** |
| davon von einem der fünf Patches berührt | **2** |

Die 35 sind die Zahl, die der C-Umsetzer gemeldet und das Item übernommen hat; meine erste eigene
Lesung sagte 27, und das war mein Filter und nicht der Baum — `grep -v project_memory/` warf auch
`team-kits/*/templates/project_memory/**` weg. Nachgezählt und korrigiert, bevor irgendetwas
angewandt wurde. Ursache der CRLF-Dateien, gemessen: dieses Repo trägt `core.autocrlf=true` in
seiner LOKALEN Konfiguration und der Host zusätzlich in der SYSTEM-Konfiguration, während
`.gitattributes:10` seit BUG-0025 `* text=auto eol=lf` sagt. BUG-0025 selbst bleibt Generation 4.

**Die zwei berührten Dateien, einzeln normalisiert und hier benannt** (Skript
`_round-scratch/TSK-0120/normalise_one.py`, das die Umwandlung verweigert, wenn der normalisierte
Inhalt nicht Byte für Byte dem HEAD-Blob entspricht):

| Datei | vorher | nachher | HEAD-Blob |
|---|---|---|---|
| `team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html` | 13 829 B, 351 CR | 13 478 B, 0 CR | 13 478 B, sha `9d2035dbe09d…` |
| `team-kits/research-team/skills/project-manager/SKILL.md` | 23 824 B, 264 CR | 23 560 B, 0 CR | 23 560 B, sha `c121eac2b035…` |

Keine weitere Datei wurde angefasst; nach dem Merge tragen **33** Dateien außerhalb
`project_memory/` weiterhin CRLF, unverändert gegenüber HEAD.

**Alle fünf Patches sind reines LF** (0 CR-Bytes), und keiner trägt `project_memory/.audit` oder
irgendeine andere Datei unter `project_memory/` — über die `diff --git`-Köpfe geprüft, nicht über
eine Zeichenkettensuche.

---

## 0a. Vorgefunden bei der Fortsetzung (der Lauf wurde durch ein Wochenlimit unterbrochen)

Gemessen, nicht erinnert, bevor weitergearbeitet wurde:

```
git rev-parse HEAD              -> e45c0ca (unverändert, kein Commit)
git diff HEAD --stat            -> 90 Dateien, +12593/-1602 außerhalb project_memory/
git status --short              -> 14 neue Dateien vorgemerkt (A), 68 geändert, 7 unvorgemerkt
team-kits/*/VERSION             -> alle drei 2026.09.03-1 (der eine Stempel steht)
_round-scratch/TSK-0120/        -> fullrun-tools-2.txt (4 failed / 4554 passed / 14 skipped),
                                   gatesuite.txt (489 passed), rework-suites.txt (201 passed),
                                   die Rot-zuerst-Rigs r1..r8, das Messrig, die Wunschlisten-Diffs
project_memory/staging/TSK-0120 -> existierte NICHT; das Protokoll lag als Entwurf im Scratch
```

Alle fünf Patches waren angewandt, der Stempel gesetzt, der Volllauf und die Gate-Suite gefahren
und die vier Roten des Volllaufs behoben. Offen war genau das Protokoll.

---

## 1. Reihenfolge, Anwendung, Pin-Tests

Die Pin-Menge ist `tools/test_repo_hygiene.py`, `tools/test_shortening_net.py`,
`tools/test_ci_lint_pinned.py` (zusammen 67) und `tools/test_context_budget.py -k "pin or size"` (3).

| # | Strom | Patch (sha256) | Dateien | angewandt | ausgeschlossen | Pin |
|---|---|---|---|---|---|---|
| 0 | — | Basislinie auf `e45c0ca` | — | — | — | **67 + 3 passed** |
| 1 | C Freigaben | `TSK-0117/stream-approvals.patch` `e3ab4ceac6b0…` | 24 | 21 | 3 × `VERSION` | **67 + 3 passed** |
| 2 | B Büro | `TSK-0116/stream-office.patch` `7c6f388ff841…` | 19 | 15 | 3 × `VERSION`, Löcherliste | **67 + 3 passed** |
| 3 | A Board | `TSK-0115/stream-board.patch` `884af7252ffc…` | 16 | 12 | 3 × `VERSION`, Löcherliste | **67 + 3 passed** |
| 4 | E Design | `TSK-0119/stream-design.patch` `6be9bd2cc313…` | 8 | 6 | 1 × `VERSION`, Löcherliste | **67 + 3 passed** |
| 5 | D Texte | `TSK-0118/stream-parallel.patch` `31d5e9dbd07e…` | 18 | 16 | Löcherliste, Dispositionsjournal | **67 + 3 passed** |

C's Patch wurde erst nach der Meldung „C final" des Leads genommen und vorher gemessen:
231 318 B, 0 CR, sha256 `e3ab4ceac6b0ded8e7fdb7088e20db92f5f11657896ad343c8f063a8f3849f17`,
`24 files changed, 2879 insertions(+), 131 deletions(-)` — Byte für Byte die Werte, die der Lead
gemeldet hat.

**BEFUND GEGEN DAS ITEM (M):** das Item sagt „every patch drops the VERSION hunks". Gemessen ist
das falsch — **vier von fünf** Patches tragen `team-kits/*/VERSION`-Hunks (A, B, C je drei, E einer;
nur D nicht). Sie sind beim Anwenden per `--exclude` verworfen worden statt die Patch-Dateien zu
ändern, damit die angewandten Bytes die vom jeweiligen Prüfer geprüften bleiben.

**Nicht per `git apply` anwendbar, weil alle fünf dieselbe Stelle schreiben:**
`docs/POST_V2_WISHLIST.md` (alle fünf) und `docs/reviews/phase0-disposition.md` (A, D, E). Beide
sind unten von Hand aufgelöst.

---

## 2. Nahttabelle — Auflösung und Schiedsrichter je Naht

| Naht | Auflösung | Schiedsrichter (Test) |
|---|---|---|
| `team-kits/*/VERSION` (alle fünf) | alle Hunks verworfen, EIN Stempel am Ende | `tools/validate.py` („VERSION not bumped") |
| MST-Zeilen `guard_no_adhoc.ITEM_TYPES` ×3 | `"mst"` in die Tupel, drei Kits byte-identisch | `tools/test_hooks.py::test_no_adhoc_covers_every_item_type` |
| MST-Zeilen `guard_memory_budget._ID` ×3 | `MST` in die Id-Alternative, drei Kits byte-identisch | `tools/test_hooks_v2.py::test_the_id_prefixes_match_the_kernels_item_types` |
| `templates/project_memory/milestones/active` ×3 | Verzeichnis mit `.gitkeep` je Kit angelegt | **neu gebaut**, siehe Befund M-2 unten: `tools/test_board.py::test_every_kit_ships_a_directory_for_every_type_the_product_view_places` |
| `generate_dashboard.py` `VIEWS` | **gegenstandslos** — der Test existiert nicht mehr (A's Patch entfernt ihn; DEC-0065 (1): das Dashboard rendert keine Items) | am Sammler gemessen statt an einer Zeichenkettensuche: `pytest tools/ -k dashboard_views --collect-only` sammelt **no tests** |
| A §7.2 `backlog_tree` MST-Zeilen | `_LABELS["MST"]` und `children=("FR","CR","MST")` | `tools/test_board.py::test_the_milestone_type_is_wired_completely_or_not_at_all`, `…::test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view`, `…::test_every_type_the_kernel_has_carries_a_plain_language_name` |
| A §7.3 `state._write_board` → `plan_diagram.render_all` | gebaut, aber in einem EIGENEN `try` (Abweichung, unten begründet) | `tools/test_plan_diagram.py::test_a_state_write_leaves_both_diagrams_beside_the_board` |
| A §7.4 `cli.py` druckt die zwei Diagrammpfade | gebaut, aus `plan_diagram.FILENAMES` abgeleitet | `tools/test_board.py::test_the_documented_command_names_every_artefact_it_writes` |
| A §7.5 optionales `now=None` auf `approvals.open_requests` | gebaut, plus die eine Definition `has_expired(request, now=None)` und ihre drei Leser | `tools/test_approvals_dispatch.py::test_every_reader_of_the_expiry_rule_asks_this_one`, `tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`, `tools/test_board.py::test_the_board_and_the_session_brief_agree_on_the_open_requests` |
| B S1/S2 Onboarding-Antworten | in `skills/office-manager/SKILL.md`, Schritt ONBOARD | `tools/test_shortening_net.py` (Abschnitts-Pin), `tools/test_disposition.py` |
| B S3 Reichweiten-Satz | in `agents/records-clerk.md` und Office-Verfassung §2 | Abschnitts-Pin; die Eigenschaft selbst: `tools/test_hooks.py::test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` |
| B S4 (`retention: null` über `add-filing-rule`) | **nicht gebaut**, `H130` bleibt offen — es ist im Stromprotokoll ein Vorschlag, keine Zeile |
| B S5 (Rollup über unlesbare `retention` in `report.py`) | **nicht gebaut**, im Stromprotokoll ausdrücklich „optional" |
| B S6 (`_duties._retention_years` auf `kernel.filing.retention_span`) | **nicht gebaut, mit gemessener Begründung** (unten) | `tools/test_office_duties.py::test_the_kernel_and_the_duty_register_read_a_retention_the_same_way` (Docstring korrigiert) |
| B S7 `tools/test_hooks.py` (A × B) | keine Kollision — beide Patches sauber angewandt | — |
| B S8 `user/CLAUDE.md` | **verbotener Scope**, nicht angefasst, hier benannt | — |
| B S9 Trenner aus `_filing._walk` | **GEBAUT**, siehe Abschnitt 4 | `tools/test_hooks.py::test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` |
| C §6 Plan-Freigabe-Sätze | in dev- und research-Verfassung §5 und in beide PM-Skills, Schritt 4; **nicht** ins Office-Kit (gemessen: `approvals.plan_goals` läuft über `set(ROOT_TYPE_BY_KIT.values())` = `{PR, RQ}`, ein `PROC` ist nie ein Planziel) | `tools/test_approvals_dispatch.py::test_a_plan_stops_covering_a_goal_the_moment_its_scope_moves` (im Text zitiert) |
| C §6 QA-Satz `--result blocked` | in fünf `SKILL.md` (zwei QA-, drei Auditor-Skills) | `tools/test_hooks.py::test_no_instruction_text_names_an_evidence_kind_or_verdict_the_kernel_refuses` |
| C-1 `check-scopes` in der Befehlsoberfläche | eine Zeile in drei Verfassungen + `README.md`, an der Stelle der Parser-Reihenfolge (nach `archive`) | `tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it` |
| C's Rest „`docs/` vs `docs/**`" an `H148` | **war schon im finalen C-Patch** (letzte Änderung vor „C final"); nichts anzuhängen | `.claude/hooks/test_gates.py::test_the_hole_list_judges_every_entry_it_carries` |
| E §9 (a) `agents/product-designer.md` | Absatz „You LOOK at your own draft" um die drei Exit-Codes ergänzt | Abschnitts-Pin; `tools/test_design_conformance.py` |
| E §9 (b) PM-Skill Design-Schritt (b) | Satz über den `3` angehängt | Abschnitts-Pin |
| E §9 (c) Verfassung | **kein Satz**, wie E es verlangt (kein Gate ⇒ keine Schutzbehauptung) | — |
| DEC-0064 (5) Verfassungszeile ×3 | MST-Absatz + Eigentümerzeile in allen drei Verfassungen | `tools/test_shortening_net.py::test_every_hand_built_item_type_is_ruled_on_and_not_merely_assigned` |
| `docs/POST_V2_WISHLIST.md` (alle fünf) | abschnittsweiser Drei-Wege-Merge, danach Zeilen und Abschnitte aufsteigend nach Nummer | `.claude/hooks/test_gates.py::test_the_hole_list_judges_every_entry_it_carries`, `…::test_every_test_the_hole_list_names_is_one_that_exists` |
| `docs/reviews/phase0-disposition.md` (A, D, E) | A und E per `git apply`; D's zwei Anhänge an die beiden append-only-Journale von Hand ans Ende | `tools/test_disposition.py` |
| `tools/constitution_section_pins.json`, `tools/lead_package_sizes.json` | Ratschen nach der letzten Textänderung neu aufgenommen, mit Notiz | `tools/test_shortening_net.py`, `tools/test_context_budget.py` |
| die zwei Scope-Leser | **entschieden**: `kernel/scopes.py` ist der ausgelieferte; `tools/check_scope_overlap.py` behält nur die Kommandozeile | `tools/test_parallel_streams.py::test_the_workshop_tool_carries_no_predicate_of_its_own` |

---

## 3. Die Nähte, die einen BAU verlangten — mit ihrer Rot-Messung

Jede Messung lief in einer Kopie **außerhalb** des Repos
(`_round-scratch/TSK-0120/redfirst-tree`, Rig `redfirst.py`, das sich weigert zu laufen, wenn seine
Kopie im Repo läge — die Lehre aus dem Vorfall von Strom C).

| # | Wiederhergestellter Defekt | Test | Ergebnis |
|---|---|---|---|
| R1 | `approvals.mint` vergleicht die Uhr wieder selbst | `test_every_reader_of_the_expiry_rule_asks_this_one` | **1 failed** |
| R2 | der Sitzungsbrief vergleicht wieder selbst | dito | **1 failed** |
| R3 | die Tafel vergleicht wieder selbst | dito | **1 failed** |
| R4 | die Auslöserzeile in `state._write_board` fällt weg | `test_a_state_write_leaves_both_diagrams_beside_the_board` | **1 failed** |
| R5 | die Diagramme teilen sich den `try` der Tafel | dito | **1 failed** |
| R6 | `cli.py` nennt die zwei Diagrammpfade nicht mehr | `test_the_documented_command_names_every_artefact_it_writes` | **1 failed** |
| R7 | derselbe Zustand, aber mit der ALTEN Zählfassung des Tests | dito | **1 passed** — die Zählfassung ist blind, die Ableitung nicht |
| R8 | `guard_no_adhoc.ITEM_TYPES` verliert `mst` | `test_no_adhoc_covers_every_item_type` | **1 failed** |
| R9 | `guard_memory_budget._ID` verliert `MST` | `test_the_id_prefixes_match_the_kernels_item_types` | **1 failed** |
| R10 | die drei `milestones/active` verschwinden | DEC-0064s benannter Stolperdraht `test_each_kit_renders_the_types_its_own_template_ships` | **3 passed** — der Draht sieht es NICHT (Befund M-2) |
| R10b | dieselbe Mutation | der neu gebaute `test_every_kit_ships_a_directory_for_every_type_the_product_view_places` | **3 failed**; nur ein Kit entfernt → **1 failed, 2 passed** |
| R11 | `backlog_tree._LABELS` verliert `MST` | `test_…plain_language…` + `test_the_milestone_type_is_wired_completely_or_not_at_all` | **2 failed** |
| R12 | `backlog_tree.VIEWS` verliert `MST` | `test_…placed_by_a_backlog_view` + `…wired_completely…` | **2 failed** |
| R13 | der Wächter fragt den Trenner nicht mehr | `test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` | **1 failed** |
| R14 | nur die VOR-Hälfte des Trenner-Prädikats fällt weg | dito | **1 failed** |
| R15 | nur die NACH-Hälfte fällt weg | dito | **1 failed** |
| R16 | eine zweite Schreibweise kehrt in das Werkstattwerkzeug zurück | `test_the_workshop_tool_carries_no_predicate_of_its_own` | **1 failed** |

Kontrolle ohne Mutation: in jedem Fall grün.

---

## 4. Merge-Befunde — was die Nähte zeigen und kein Strom sehen konnte

### M-1 (blockierend, behoben) — `approvals.mint` war ein VIERTER Leser der Ablaufregel und stürzte ab

`approvals.has_expired` nennt sich im eigenen Docstring „die EINE Definition" von „kann nie mehr
prägen" und zählte „zwei Leser" auf. Beim Bau der Naht §7.5 gemessen: es sind vier —
`pending_request`, `sweep_expired_requests`, `report.generate_session_brief` (eigene Zeile) und
`approvals.mint` (`time.time() > float(request["expires_at_epoch"])`, ohne Fangnetz). Auf einem
Stempel, den niemand lesen kann, gehen die Leser auseinander
(`_round-scratch/TSK-0120/probe_expiry_readers.py`, Anfragedatei je Form von Hand geschrieben):

| `expires_at_epoch` | `pending_request` | `mint` VORHER | `mint` NACHHER |
|---|---|---|---|
| `'soon'` | `ApprovalError` (abgelaufen) | **`ValueError: could not convert string to float`** | `ApprovalError` |
| `null` | `ApprovalError` (abgelaufen) | **`TypeError`** | `ApprovalError` |
| lebend | gibt zurück | `ApprovalError` (falsche Antwort) | unverändert |
| abgelaufen | `ApprovalError` | `ApprovalError` | unverändert |

Warum es kein Strom sehen konnte: A besaß die Tafel und meldete die Naht; C besaß `approvals.py`,
hatte aber keinen Anlass, `mint` gegen `has_expired` zu halten — die Frage entsteht erst, wenn
jemand zählt, wie viele Leser die Regel hat, und das tut erst die Naht. **Behoben:** `mint` fragt
`has_expired`. **Test:** `tools/test_approvals_dispatch.py::test_every_reader_of_the_expiry_rule_asks_this_one`,
zwei Hälften — die geparste Paketstruktur (welche Funktion vergleicht überhaupt gegen eine Uhr) und
der ausgeführte Lauf über vier unlesbare Stempelformen. Rot: R1–R3.

**Eigener Fehler dieser Runde, gemessen und behoben:** die erste Fassung des Strukturtests las nur
`ast.Compare`-Knoten, deren Quelltext den Feldnamen enthält. Die Rückkehr der Tafel-Kopie
(`expires = float(...)`, danach `now > expires`) blieb damit **grün** — ein Test, der den Defekt
nicht sehen kann, den er benennt (R3 war beim ersten Lauf `1 passed`). Der Leser hat jetzt einen
Taint-Schritt und nennt diese Messung in seinem eigenen Docstring.

### M-2 (blockierend, behoben) — DEC-0064s benannter Stolperdraht kann ein fehlendes Vorlagen-Verzeichnis nicht sehen

`DEC-0064` `consequences` verspricht: „jede Zeile hat einen Test, der ohne sie rot wird, so ist eine
halb angewandte Naht sichtbar und nicht still". Für die Naht `templates/project_memory/
milestones/active` ×3 nennt der DEC `test_board.test_each_kit_renders_the_types_its_own_template_ships`.
Gemessen (R10): mit allen drei Verzeichnissen gelöscht bleibt dieser Test **grün, 3 passed** — er
leitet seine Erwartung aus DEMSELBEN Vorlagenbaum ab und kann den Baum darum nicht eine Schublade
verlieren sehen. Kein Strom konnte das sehen: A hat den DEC vorgeschlagen und dessen Kostenliste
geschrieben, C hat die Kernel-Zeilen gebaut, die Vorlagen gehörten keinem.

**Gebaut** statt nur benannt, als Eigenschaft und nicht als MST-Sonderfall:
`tools/test_board.py::test_every_kit_ships_a_directory_for_every_type_the_product_view_places` —
jedes Kit muss für jeden Typ, den die PRODUKT-Sicht platziert, eine Schublade ausliefern, und der
Typ muss auf einer frischen Tafel entweder gezeichnet oder als still benannt sein. Die System-Sicht
ist absichtlich ausgenommen (dev liefert legitim keine `HYP`/`EXP`). Rot: R10b, beidseitig
(drei Verzeichnisse weg → 3 failed; eines weg → 1 failed / 2 passed).

### M-3 (behoben) — MST ist ein handgebauter Typ, und dafür gibt es einen Stolperdraht, den DEC-0064 nicht kennt

`tools/test_shortening_net.py::test_every_hand_built_item_type_is_ruled_on_and_not_merely_assigned`
verlangt, dass ein Typ, dessen Felder der Kernel erzwingt, im Lead-Paket in mindestens DREI
Abschnitten außerhalb einer Tabelle erklärt ist. Nach den Kernel-Zeilen von C war `MST` in allen
drei Kits **nirgends außerhalb einer Tabelle**. Das steht in DEC-0064s Kostenliste nicht, und kein
Strom hätte es sehen können: der Test liest das LEAD-PAKET, das erst im Merge alle Sätze trägt.
Gebaut: der MST-Absatz in allen drei Verfassungen, ein Satz in der Anforderungshierarchie (dev,
research) bzw. in §1a (office), und die Eigentumsklausel in den drei Lead-Skills.

### M-4 (behoben) — die Naht §7.3 hätte die Fehlermeldung der Tafel lügen lassen

A's Naht-Zeile sagt wörtlich „innerhalb desselben `try`". Angewandt so, meldet der bestehende
`except`-Zweig `[board] … was NOT rebuilt`, wenn eine GRAFIK scheitert — obwohl die Tafel längst
geschrieben ist. Das ist die über-alarmierende Hälfte der Hausregel „kein Kommentar behauptet
etwas, das der Code nicht baut". Gebaut mit einem eigenen `try` und einer eigenen Meldung
(`[plan] …`); der Test prüft beides, und die Rückkehr zum gemeinsamen `try` ist rot (R5).

### M-5 (behoben) — der Schiedsrichter von §7.4 war eine Zahl, keine Ableitung

test_the_documented_command_writes_and_names_both_artefacts (historischer Name, ohne Backticks,
weil er nicht mehr auflöst) verlangte **genau zwei** gedruckte
Zeilen. Mit der Naht schreibt `generate-index` vier Artefakte. Gemessen (R7): mit der alten,
zählenden Fassung UND ohne die neuen Druckzeilen bleibt der Test **grün** — er kann nicht sehen,
dass ein Artefakt unangekündigt entsteht; mit der abgeleiteten Fassung ist derselbe Zustand rot.
Der Test heißt jetzt `test_the_documented_command_names_every_artefact_it_writes` und vergleicht,
was der Lauf gedruckt hat, mit dem, was unter `generated/` liegt. Der historische Name steht ohne
Backticks in seinem Docstring und in `docs/reviews/2026-08-16-tsk0071-measurements.md`, weil er
nicht mehr auflöst.

### M-6 (behoben) — die zwei Scope-Leser: eine Entscheidung, ein Prädikat

C's Prüfer (N3) hat gemeldet, dass `kernel/scopes.py` und `tools/check_scope_overlap.py` in
Prädikat und Regel übereinstimmen und sich in der EINGABE unterscheiden. Entschieden wie im Item
verlangt: **`kernel/scopes.py` ist der ausgelieferte** — ein Kundenprojekt erreicht ihn über
`scripts/harness.py check-scopes`, ein Repo-Skript nicht. `tools/check_scope_overlap.py` trägt
seitdem KEIN Prädikat mehr; es liest eine Kommandozeile und ruft `kernel.scopes`. Sein Modulkopf
zeigt auf `team-kits/kernel/scopes.py` statt die Regel zu wiederholen.

Dabei kam ein Unterschied heraus, den beide Prüfer je für sich abgenommen hatten: eine Naht, die
einem Auftrag die ganze Ownership nimmt, war im Werkzeug **rc 1** („der Aufrufer hat etwas
verlangt, das nicht geht") und ist im Kernel **rc 2** (die Naht wird nicht abgezogen, die Kollision
steht). `2` ist die wahre Antwort — die Prüfung KONNTE laufen und hat eine geteilte Datei gefunden.
D's Test ist auf diese Semantik gezogen, mit der Begründung im Docstring.
Rot: R16. Suiten danach: `test_parallel_streams` 29, `test_parallel_scopes` 14, beide grün.

### M-7 (benannt, nicht behoben) — das Item nennt eine „F6 call line in report.py", die es nicht gibt

Das Item verlangt „B F6 call line in report.py (S4-S6)". In B's Protokoll ist S5 ausdrücklich
„optional", S4 ein Vorschlag an C (`H130` bleibt offen) und S6 eine Änderung in
`office-team/hooks/_*.py`. Eine konkrete Aufrufzeile für `report.py` gibt es in keinem der drei.
Gebaut wurde keiner der drei; S6 mit einer Messung dahinter (unten), S4/S5 als das benannt, was sie
sind.

### M-8 (benannt) — der Auftragstext zu H126 sagt „two clocks → one", die Messung sagt das Gegenteil

Das Item schreibt zur Naht §7.5 „H126 two clocks -> one". A's eigener H126-Eintrag sagt wörtlich:
„die zwei Uhren bleiben zwei, aber die Regel wird eine" — und das ist auch das, was gebaut ist und
was gebaut werden DARF: die Tafel liest bewusst keine Wanduhr, damit die Seite eine reine Funktion
des Zustands bleibt. Ich bin der gemessenen Fassung gefolgt und nenne die Abweichung hier.

### M-9 (benannt) — unbenannte Kollisionen im Schnitt, die die Nahttabelle nicht führte

Die Nahttabelle vom Schnitt nennt `tools/test_hooks.py` als Naht „A × B". Tatsächlich schreiben
**drei** Ströme diese Datei (A, B, C), und dazu kommen drei weitere geteilte Dateien, die die
Tabelle nicht führt: `tools/test_kernel.py` (A × B), `tools/constitution_section_pins.json`
(D × E) und `docs/reviews/phase0-disposition.md` (A × D × E). Keine davon hat beim Anwenden
kollidiert — außer `phase0-disposition.md`, das von Hand aufgelöst werden musste. Ein
unbenannter Zusammenstoß im Merge ist nach DEC-0062 (5) ein Befund gegen den Schnitt; er steht
darum auch in Abschnitt 6.

### M-10 (aus dem Volllauf, behoben) — die Plan-Freigabe kam ohne die Messung, auf der ihre eigene Begrenzung steht

`tools/test_presets.py::test_every_target_form_names_a_live_apr_kind` verweigert ausdrücklich eine
Freigabeform, die „ohne eine Messung dessen ankommt, was sie rendert" — jede der vier vorhandenen
Formen nennt in einem Kommentar den Test, der ihren Satz misst. `plan` ist mit Strom C dazugekommen
und hatte keinen. Das ist genau die Zusage, auf der `H132` steht („begrenzt: die Frage nennt jedes
Ziel") und auf der DEC-0068 (1) den Nutzer hat entscheiden lassen. Kein Strom konnte es sehen: C
besaß `approvals.py` und `tools/test_presets.py` liegt nicht in seinem Scope-Schnitt, und der Test
wird nur beim Volllauf gefahren. **Gebaut:**
`tools/test_kernel.py::test_the_question_a_plan_asks_shows_every_goal_the_hash_covers` — in
derselben Form wie seine vier Geschwister: er fragt das MANIFEST, welche Ziele es hasht, und
verlangt Id, Titel und Revision jedes einzelnen im gerenderten Satz, prüft die Determiniertheit und
verweigert eine Zählung anstelle der Liste.

### M-11 (aus dem Volllauf, behoben) — das ausgelieferte EÜR-Vokabular gegen die Kit-Neutralität

`tools/test_kit_neutrality.py::test_every_office_state_template_ships_its_lists_empty` (FR-0028)
verlangt, dass eine Office-Vorlage STRUKTUR ausliefert und keinen INHALT. FR-0076 (1) liefert seit
Strom B `master_data.yaml` mit 15 Kategorien gefüllt aus. Kein Strom konnte den Zusammenstoß sehen:
B's Suitenliste enthält `test_kit_neutrality` nicht, und die Neutralitätsregel ist älter als FR-0076.

**Entschieden statt weggeräumt, und die Entscheidung ist gemessen:** die 15 Zeilen sind die
Ausgaben- und Einnahmeklassen der Anlage EÜR — **jede** trägt eine Formularzeile (`euer_line`) —,
und die Liste, die ein fremdes Geschäft trüge, liefert leer aus (`counterparties: []`). Ein
Steuerformular ist kein Geschäft. Der Eintrag steht darum in `FILLED_TEMPLATE_LISTS` mit diesem
Grund, und **die Ausnahme ist kein Freibrief**: derselbe Test verlangt jetzt von jeder
ausgelieferten Kategorie eine Formularzeile, liest sie am Dokument statt am Sammler (der `income`
und `expense` auf einen Schlüssel zusammenfallen lässt) und hat eine eigene Untergrenze. Rot
gemessen in beide Richtungen: eine erfundene Kategorie ohne Zeile → **1 failed**; die Ausnahme
zurückgenommen → **1 failed**; ohne Mutation grün.

### M-12 (aus dem Volllauf, behoben) — dieselbe Änderung bewegte eine Untergrenze in einem zweiten Test

`tools/test_kernel.py::test_no_shipped_kit_document_refuses_the_fill_its_own_template_asks_for`
zählt, wie viele leere Listen der Kits ihre eigene natürliche Füllung annehmen, und hatte die
Untergrenze `>= 8` mit dem Kommentar „acht der neun ausgelieferten sind schreibbar". Mit dem
gefüllten `categories` sind es acht ausgelieferte und **sieben** schreibbare (`filing_plan.rules`
gehört `add-filing-rule`). Die Grenze steht jetzt auf 7 — **mit dem Grund daneben**, nicht
angepasst, damit die Zahl passt: der Kommentar nennt, welche Liste weggefallen ist und warum, und
zeigt auf die Ausnahme in M-11.

### M-13 (aus dem Volllauf, behoben) — ein Verfassungsabsatz in zwei von drei Kits braucht eine benannte Ausnahme

`tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text` liest einen
fetten Absatz-Anfang, den mindestens ZWEI Verfassungen tragen, als geteilten Text und verlangt ihn
dann in allen dreien — oder einen Eintrag in `KIT_SPECIFIC_PARAGRAPHS` mit dem Grund. Mein
Plan-Freigabe-Absatz steht in dev und research und bewusst nicht in office. Das ist mein eigener
Befund aus dem Volllauf, und die Ausnahme trägt die Messung, die ihn rechtfertigt:
`approvals.plan_goals` läuft über `set(ROOT_TYPE_BY_KIT.values())` = `{PR, RQ}` — ein `PROC` kann
nie von einer Planfreigabe gedeckt sein, also wäre der Absatz im Office-Kit eine Beschreibung eines
Mechanismus, den dieses Kit nicht hat.

### S6 — nicht gebaut, und WARUM, gemessen

B's Naht S6 will `_duties._retention_years` auf `kernel.filing.retention_span` umstellen, damit die
Aufbewahrungs-Definition einmal statt zweimal steht. Der Weg existiert
(`_kernel.kernel_module("filing")`, dieselbe Brücke, die `gate_approval` und `gate_dispatch` schon
benutzen). Gemessen, warum er trotzdem nicht genommen wird: mit `$HARNESS_KERNEL_PATH` auf ein
Verzeichnis ohne Kernel beantwortet `_duties.retention_duties` seine Frage weiter, während
`_kernel.kernel_module("filing")` `KernelUnavailable` wirft. Das Fristenregister läuft beim
SITZUNGSSTART; es an einen importierbaren Kernel zu binden, hieße, es genau dann verstummen zu
lassen, wenn ein Projekt seine Fristen am nötigsten hört. Die zwei Kopien bleiben und werden
gemessen statt versprochen — der Test vergleicht die kompilierten Muster selbst und leitet seinen
Korpus aus den Einheitenwörtern BEIDER Leser ab. **Was daran korrigiert wurde:** sein Docstring
nannte nur die eine Richtung („der Kernel darf keinen Kit-Haken importieren") und verschwieg die
tragende — jetzt stehen beide, mit der Messung.

---

## 5. Zeigertabelle — jeder `DEC`/`H`/Test-Zeiger, den der gemergte Baum schreibt

| Zeiger | Wo | löst auf? |
|---|---|---|
| `DEC-0064` | Verfassungen ×3, `state.py`, `board.py` | ja (`project_memory/decisions/active/DEC-0064.yaml`) |
| `DEC-0065`, `DEC-0066`, `DEC-0067` | Board-/Text-Code | ja |
| `DEC-0068` | Verfassungen dev/research, PM-Skills ×2, `approvals.py` | ja |
| `DEC-0069` | `H138`-Eintrag | ja |
| `H126`, `H127`, `H136`, `H144`, `H147`, `H148` | Kernel- und Haken-Köpfe | ja — alle in `docs/POST_V2_WISHLIST.md` |
| jeder Testname in Backticks unter `.claude/hooks/` | — | `.claude/hooks/test_gates.py` misst es |
| jeder Testname, den die Löcherliste nennt | — | `test_gates.py::test_every_test_the_hole_list_names_is_one_that_exists`, grün |
| jeder `DEC`-Zeiger in einer ausgelieferten Kit-Datei | — | `tools/test_repo_hygiene.py::test_every_decision_pointer_in_a_shipped_kit_file_resolves`, grün |

---

## 6. Befunde GEGEN DEN SCHNITT (für die Retrospektiv-DEC der Generation 3, hier NICHT behoben)

| # | Befund | Gemeldet von |
|---|---|---|
| 1 | Der ausgelieferte Referenz-Skill-Vertrag ERZWINGT eine byte-identische Kopie des `parallel-streams`-Skills nach `research-team`, obwohl TSK-0118s `allowed_scope` nur dev nennt — der Auftrag war so nicht erfüllbar | D + D's Prüfer |
| 2 | `TSK-0088` (DRAFT seit August, Scope `team-kits/**`) überlappte JEDEN der fünf Ströme; der Lead hat es während der Runde abgebrochen | D's Prüfer |
| 3 | Die Löchernummern H141–H149 wurden per Nachricht vergeben, während die Items schon READY (= eingefroren) waren; die Reservierung lebt nur im Rundenlogbuch | E's Prüfer (N-4) |
| 4 | Jedes der fünf Items führt `project_memory/**` im `forbidden_scope` UND schreibt sein Protokoll nach `project_memory/staging/<id>/` — derselbe Widerspruch wie in Generation 2 | E's Prüfer (N-10), C's Prüfer |
| 5 | TSK-0119 erlaubt `templates/repo/scripts/kit_*.py`, verbietet aber `research-team/**`, während `kit_browser_checks.py` byte-gespiegelt sein MUSS — die BUILD-Hälfte von FR-0077 war damit unbaubar (`H139`) | E |
| 6 | Die Nahttabelle des Schnitts nennt `tools/test_hooks.py` als „A × B"; tatsächlich schreiben A, B und C sie, und `tools/test_kernel.py`, `tools/constitution_section_pins.json`, `docs/reviews/phase0-disposition.md` sind drei weitere ungenannte geteilte Dateien | **diese Merge-Runde** |
| 7 | Das Item behauptet „every patch drops the VERSION hunks"; gemessen tragen vier von fünf Patches sie | **diese Merge-Runde** |
| 8 | DEC-0064s Kostenliste nennt für zwei ihrer Zeilen (Vorlagenverzeichnis ×3, Lead-Text) Stolperdrähte, die den Defekt nicht sehen bzw. gar nicht genannt sind (M-2, M-3) | **diese Merge-Runde** |
| 9 | **Der Auftrag an diese Runde sagt „every patch drops the VERSION hunks“** — gemessen tragen vier von fünf Patches sie (identisch mit Zeile 7, hier als AUFTRAGS-Befund geführt und nicht als Schnitt-Befund) | **diese Merge-Runde** |
| 10 | Der Auftrag verlangt eine „F6 call line in report.py“; in keinem der fünf Stromprotokolle gibt es eine solche Zeile — S4 ist ein Vorschlag, S5 ausdrücklich optional, S6 eine Hakenänderung | **diese Merge-Runde** |
| 11 | Der Auftrag fasst H126 als „two clocks → one“; A's gemessener Eintrag sagt „die zwei Uhren bleiben zwei, die Regel wird eine“, und nur das ist baubar (die Tafel liest bewusst keine Wanduhr) | **diese Merge-Runde** |
| 12 | Der Auftrag sagt „H144 stays open either way“ und verlangt im selben Satz „S9 BUILT or named“; gebaut und in beiden Richtungen gemessen ist der Eintrag GESCHLOSSEN, mit benanntem Preis — ein Auftrag kann ein Urteil nicht vorwegnehmen, das die Messung erst ergibt | **diese Merge-Runde** |

---

## 7. Die Löcherliste in einer Ordnung

Zusammengeführt wurde **abschnittsweise**, nicht zeilenweise: ein zeilenbasierter Drei-Wege-Merge
war der erste Versuch und hat die Messtabelle eines Stroms in den Eintrag eines anderen gelegt,
weil die Konfliktbereiche nicht auf den Abschnittsgrenzen liegen. Das Rig
(`_round-scratch/TSK-0120/wl/merge3.py`) liest je Strom `base + Patch`, ordnet jede geänderte Zeile
und jeden geänderten Abschnitt seinem Strom zu und VERWEIGERT, wenn zwei Ströme denselben Eintrag
anfassen. Ergebnis:

| Strom | geänderte/neue Einträge |
|---|---|
| A | H126, H127 |
| B | H123, H125, H129, H130, H131, H144 |
| C | H132, H133, H134, H147, H148 |
| D | H135, H136, H137, H141, H142, H143 |
| E | H138, H139, H140, H145, H146 |

Kontrolle. **Die Zählregel steht neben der Zahl**, weil sie das Ergebnis bestimmt und zwei
vertretbare Regeln zwei Zahlen ergeben (Prüferbefund M7): gezählt wird eine nicht-leere
hinzugefügte Zeile eines Patches, die im Ergebnis **nicht als GANZE ZEILE** vorkommt. Nach dieser
Regel sind es von den 1 182 hinzugefügten Zeilen (A 96, B 364, C 222, D 192, E 308) am Ende dieser
Runde **A 9, B 10, D 11, C 0, E 0**. Die schwächere Regel — die Zeile kommt irgendwo als
TEILZEICHENKETTE vor — zählt zwei weniger; das ist der ganze Unterschied zwischen den beiden
Messungen, und die Zeilenregel ist die richtige, weil eine Zeile, die nur als Teil einer anderen
auftaucht, nicht diese Zeile ist. Die erste Fassung dieses Absatzes sagte "0 fehlend" und maß
gegen den Stand VOR dem Neubeurteilen. Wo sie liegen: ausschließlich in den Einträgen, die diese
Runde neu beurteilt hat (`H125`, `H126`, `H127`, `H135`, `H136`, `H142`, `H144`) und in deren
Zusammenfassungszeilen — in keinem, den sie nur übernommen hat. Zusammenfassungszeilen und
Abschnitte sind aufsteigend und eindeutig; jede Zeile hat einen Abschnitt.

**H128 und H149 sind reserviert und unbenutzt** — als eigener Absatz unter der Tabelle festgehalten,
damit die Lücke als Buchführung lesbar ist und nicht als verlorener Eintrag.

**Von dieser Runde neu beurteilt:**

* **H126** — Rest, verkleinert: die Regel ist eine (`has_expired`), die zwei Uhren bleiben zwei.
* **H127** — halb geschlossen: die Diagramme haben ihren Auslöser; die MELDUNG über eine
  Handänderung fehlt weiterhin.
* **H136** — GESCHLOSSEN: das Kernel-Verb, das der Eintrag als die richtige Antwort benannt hat,
  ist gebaut und in der Werkstatt gemessen (15 überlappende Paare, rc 2). Was offen bleibt, ist ein
  anderer Satz (nichts VERWEIGERT einen überlappenden Schnitt) und gehört Generation 4.
* **H144** — GESCHLOSSEN für die vier gemessenen Formen, mit einer benannten Über-Verweigerung.
* **H125, H135, H142** — Zeiger auf den zurückgezogenen zweiten Scope-Leser umgehängt.

---

## 8. Läufe

**Der Stempel.** `python tools/bump_kit_version.py` **einmal**, nach der letzten Änderung an
Kit-Code, vor dem Volllauf: dev / office / research alle drei auf `2026.09.03-1`
(`fef14a9edc6b…`, `c24c5cd542b4…`, `914d9e46a01e…`). Kein Zwischenstempel steht im Baum — die
vorläufigen Stempel aller vier Ströme, die sie trugen, sind beim Anwenden verworfen worden.

**Der Volllauf, EINMAL, nach der letzten Nacharbeit an Kit-Code und nach dem Stempel:**

| Lauf | Ergebnis | Dauer |
|---|---|---|
| `python -B -m pytest tools/ -q` | **4 failed, 4554 passed, 14 skipped** — collect = 4 572 | 57:45 |
| `python -B -m ruff check .` | sauber | — |
| `python -B tools/validate.py` | alle strukturellen Prüfungen bestanden | — |

**Die Sammelzahl, an genau einem Ort.** Der Volllauf sammelte 4 572. Der Baum sammelt heute
**4 575** (`pytest tools/ --collect-only`), weil danach drei Tests entstanden sind: der aus M-10
(die Plan-Frage) und je einer aus Nacharbeit 1 und Nacharbeit 2. Die Differenz ist genau diese drei
Knoten; jede andere Stelle dieses Protokolls zeigt hierher.

Die vier Roten sind **Befunde und keine Übersprünge**; alle vier stehen als M-10 bis M-13 in
Abschnitt 4 und sind behoben. `BUG-0033` (Zeitverhalten von Gate 3 unter Last) ist in
diesem Lauf **nicht** aufgetreten.

**Nach den vier Nacharbeiten** — sie berührten ausschließlich Testdateien
(`tools/test_kernel.py`, `tools/test_presets.py`, `tools/test_kit_neutrality.py`,
`tools/test_role_contracts.py`), also blieb der Kit-Hash unverändert und es gab keinen zweiten
Stempel (`validate.py` bestätigt das). Volle Läufe **jeder** Suite, die eine dieser Dateien liest
(DEC-0063 (4)), mit der Dateiliste:

| Lauf | liest | Ergebnis | Dauer |
|---|---|---|---|
| `test_kernel` + `test_presets` + `test_kit_neutrality` + `test_role_contracts` | sich selbst | **201 passed** | 1:33 |
| `test_repo_hygiene` + `test_shortening_net` + `test_ci_lint_pinned` + `test_context_budget` + `test_disposition` | alle Dateien unter `tools/` als Text | **117 passed** | 2:30 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` (voll) | `.claude/hooks/**`, `docs/POST_V2_WISHLIST.md`, `CLAUDE.md` | **489 passed** | 26:10 |
| `ruff`, `validate.py` (erneut) | — | sauber | — |

**Ratschen**, nach der letzten Textänderung neu aufgenommen, jede mit Notiz:
`pin_constitution_sections.py --write` (14 Abschnitte, dann 9 weitere nach dem MST-Text) und
`record_lead_package_sizes.py --write` (dev 47 046 → 49 208 B, office 53 676 → 54 779 B,
research 50 062 → 52 213 B).

**Zeilenenden nach dem Merge:** 33 verfolgte Dateien außerhalb `project_memory/` tragen weiterhin
CRLF — die 35 vom Anfang minus die zwei, die ein Hunk traf. Keine davon wurde inhaltlich verändert.

---

## 9. Die (g)-Tabelle der Generation 3

| Strom | Stufe | Erst-Bericht | Erst-Prüfung B/M/N | Nacharbeits­runden | Prüfrunden | Tokens Umsetzer / Prüfer | Spawn → PASS | DEC-0050-Notiz |
|---|---|---|---|---|---|---|---|---|
| A Board | Fable (Entwurf, 4 Phasen) + Opus (Bau) | Entwurf 07:22–09:56; Bau ~4 h 30 | B 2 / M 2 / N 7 | 4 (1 h 30, 35 min, 50 min, 30 min) | 4 (52 + 20 + 23 + 40 min) | ~810 k (Bau) + ~690 k (Entwurf) / ~495 k | ~9 h 15 (Bau) | erster Strom, der DEC-0050 in einer Nacharbeit hielt (nur lesende Suiten) |
| B Büro | Opus | ~2 h 20 | B 2 / M 2 / N 6 | 4 (1 h 50, 50 min, 40 min, 20 min) | 4 (1 h 05 + 55 + 35 + 30 min) | ~745 k / ~525 k | ~7 h 30 | ~50 min Erst-Bericht und ~65 min Nacharbeit 1 in vollen Haken-/Gate-Läufen, die DEC-0050 nicht verlangt |
| C Freigaben | Opus | ~3 h 20 (zwei Nähte mitten in der Runde) | B 2 / M 2 / N 7 | 2 (1 h 10, 40 min) | 3 (2 h 20 + 2 h 05 + 1 h 15) | ~650 k / ~690 k | **~13 h** (kritischer Pfad) | Prüfer fuhr zwei volle Haken-Suiten (47:43), die DEC-0050 von ihm nicht verlangt; dazu ~5 h Leerlauf durch eine verlorene Fertigmeldung und ein API-529 |
| D Texte | Opus | ~2 h 17 | B 1 / M 5 / N 3 | 2 (1 h 55, 35 min) | 2 (27 min + 1 h 31) | ~495 k / ~355 k | ~5 h 30 | Nacharbeit 1 fuhr `test_hooks_v2` **und** `test_hooks` voll (~31 min) für zwei lesende Tests |
| E Design | Opus | ~3 h 30 | B 1 / M 5 / N 4 | 3 (2 h 25, 40 min, 20 min) | 3 (75 + 50 + 35 min) | ~475 k / ~360 k | ~9 h 45 | ~2 h 20 volle Suitenläufe, die der Auftrag nicht verlangte (14 Suiten + zweite volle Gate-Suite) |
| **Merge** | Opus | — | — | 1 (die vier Roten des Volllaufs) | (steht aus: Merge-Prüfer) | siehe Bericht | **~4 h** (19:01 → 23:0x), davon ~1 h 40 reine Suitenlaufzeit | die volle Suite **einmal**, nach der letzten Nacharbeit an Kit-Code; nach den Testdatei-Fixes nur die lesenden Suiten |

**Was die Zeile „Merge" trägt und die fünf Stromzeilen nicht:** die vier Roten des Volllaufs waren
in KEINEM Strom sichtbar — `test_kit_neutrality` lief in keinem Stromauftrag, `test_presets` und
`test_role_contracts` liest kein Strom, der sie nicht selbst ändert, und `test_kernel`s
Listen-Untergrenze bewegt sich erst, wenn eine Vorlage gefüllt ausgeliefert wird. Das ist die
Messung hinter DEC-0063 (1): die Merge-Runde ist eine eigene Prüfung.

**Der Deckel (DEC-0060/DEC-0062 (3)): hält er?** Fünf Ströme gleichzeitig, gemessen: 16
Prüfrunden, 15 Nacharbeitsrunden, ~3,2 Mio Tokens auf der Umsetzerseite und ~2,4 Mio auf der
Prüferseite, kritischer Pfad 13 h. Der Engpass war weder der Deckel noch die Arbeit, sondern
**zwei Zustellungsfehler des Orchestrators** (eine verlorene Fertigmeldung, ~5 h Leerlauf auf dem
kritischen Pfad) und **~5 h Suitenlaufzeit, die DEC-0050 nicht verlangt hat**, verteilt über vier
Ströme und zwei Prüfer. Beides ist eine Aussage über das Verfahren, nicht über die Zahl fünf.

---

## 10. Was bewusst NICHT geschlossen, aber benannt ist

1. **`H130`** — `retention: null` bleibt über `add-filing-rule` unerreichbar (B's S4 war ein
   Vorschlag, keine Zeile).
2. **`H135`, `H141`, `H142`, `H143`, `H147`, `H148`, `H129`, `H131`, `H132`, `H133`, `H134`,
   `H137`, `H139`, `H140`** — die Reste der fünf Ströme, unverändert übernommen und in einer
   Ordnung einsortiert.
3. **`H127`** — die MELDUNG über eine Handänderung an einem Diagramm fehlt weiterhin; nur der
   Auslöser ist gebaut.
4. **`H126`** — zwei Uhren, mit Absicht.
5. **B's S5** (Rollup über unlesbare Aufbewahrung im Kernel-Bericht) und **B's S6** (die zweite
   Aufbewahrungs-Definition) — S6 mit der Messung, die dagegen spricht.
6. **B's S8** (`user/CLAUDE.md`) — verbotener Scope, nicht angefasst.
7. **`BUG-0025`** (Zeilenenden nicht festgenagelt) — Generation 4, wie das Item verlangt; 33
   Dateien tragen weiter CRLF, und die Ursache ist gemessen (`core.autocrlf=true` lokal UND im
   System, gegen `.gitattributes`).
8. **Die acht Befunde gegen den Schnitt** aus Abschnitt 6 — sie gehören in die
   Retrospektiv-DEC der Generation 3, nicht in diese Runde.

---

## 11. Nacharbeit 1 (Merge-Prüfung: FAIL, B 1 / M 4 / N 4)

Die Merge-Prüfung hat den Merge selbst als sauber gemessen (fünf Patches `--3way` rc 0 in
Reihenfolge, 24 Handarbeitsdateien alle erklärt, keine unbenannte Kollision, 13 Rot-zuerst
reproduziert). Was folgt, sind die neun Befunde.

### B1 — die Naht S9 war nur in EINER Richtung fail-closed

`guard_fs_tripwire.read_the_line` hat einen unsicheren Verzeichniswechsel ÜBERSPRUNGEN und die alte
Position stehen lassen. Das ist fail-closed, solange der übersprungene Wechsel von einem Fach WEG
führt. Führt er ZURÜCK zur Wurzel, bleibt eine harmlose Basis stehen, während die Shell das ganze
Projekt fegt. Reproduziert über jeden Haken, den das Office-Kit auf `Bash` registriert, als
Prozesse (`_round-scratch/TSK-0120/verify_tools/b1_repro.py`), mit `rm -rf .` allein bei rc 2:

| Befehlszeile | vorher | nachher |
|---|---|---|
| `cd outbox && cd .. && rm -rf .` | **rc 0** | rc 2 |
| `cd outbox && cd .. ; rm -rf .` | **rc 0** | rc 2 |
| `cd outbox ; true && cd .. ; rm -rf .` | **rc 0** | rc 2 |
| `pushd outbox > /dev/null ; popd ; rm -rf .` (N1/`H150`) | **rc 0** | rc 2 |
| zwölf Kontrollen (`rm -rf .`, `cd outbox ; rm -rf .`, `cd docs && git clean -fdx`, `cd archive && rm -rf .`, die vier H144-Formen, …) | unverändert | unverändert |

**Gebaut:** die Position ist eine MENGE möglicher Positionen. Ein sicherer Wechsel ERSETZT sie,
jeder andere FÜGT einen Kandidaten HINZU, und die Zerstörung wird verweigert, sobald IRGENDEIN
Kandidat ein Fach von Rang enthält. Drei Zeilen in `guard_fs_tripwire.py`
(`:662`, `:723-729`, `:761`).

**Preis, benannt:** drei Über-Verweigerungen — `true && cd outbox ; rm -rf .`,
`cd outbox ; cd .. | true ; rm -rf .`, `cd outbox ; cd $X ; rm -rf .`.

**Rot zuerst, in einer Kopie außerhalb des Repos, jede Hälfte einzeln:**

| # | Wiederhergestellter Defekt | Test | Ergebnis |
|---|---|---|---|
| R19 | ein unsicherer Wechsel fügt keinen Kandidaten mehr hinzu | `test_a_change_the_shell_may_not_have_made_leaves_both_positions_open` | **1 failed** |
| R20 | ein unberechenbarer Wechsel fügt die Wurzel nicht mehr hinzu (`H150`) | dito | **1 failed** |
| R21 | die Zerstörung fragt nur den NEUESTEN Kandidaten | `test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` | **1 failed** |
| — | Kontrolle ohne Mutation | beide | 2 passed |

R21 ist die Messung, die meinen ersten Anlauf korrigiert hat: sie wurde von dem Test, der sie
behauptete, **nicht** rot gemacht — in seinen Formen ist der neueste Kandidat der gefährliche. Der
Test, der sie hält, ist der H144-Schiedsrichter, und beide Docstrings sagen seitdem, welche Hälfte
sie halten und welche nicht. Ein zweiter Anlauf mit „erst `cd archive`, dann unsicher `cd outbox`"
sah aus, als messe er es, und tat es nicht: `_filing`s eigene Basen folgen jedem `cd`, also
verweigert die LÖSCH-Regel die Zeile, bevor die Fege-Regel erreicht wird — auch das gemessen und
im Test benannt.

**Drei Prosa-Sätze wahr gemacht**, die vorher Schutz behaupteten, den der Code nicht baute:
`_filing.changes_the_calling_shell` (der Satz „fail-closed" gilt nicht dieser Antwort, sondern dem,
was der Aufrufer mit ihr tut), der Wächterkopf :123 (drei Preise statt einem, `H144` **und**
`H150`), und `moves_the_working_directory` :415 („UNCOMPUTABLE STAYS UNMOVED" nannte den Nutzen
ohne die Kosten).

### N1 → `H150`, und der B1-Fix trifft ihn NICHT von selbst — gemessen

Der Prüfer bat, das zu messen statt anzunehmen. Ergebnis: mit dem B1-Fix allein bleibt
`pushd outbox > /dev/null ; popd ; rm -rf .` **rc 0** — `popd` gibt gar kein Ziel heraus, also gibt
es nichts hinzuzufügen. Ein Prototyp außerhalb des Repos (`n1_probe.py`) zeigte, dass drei Zeilen
genügen und alle zwölf Kontrollen unverändert bleiben, bei zwei weiteren benannten
Über-Verweigerungen. Weil die Kette in einer Sitzung durchläuft, ist er **gebaut** statt nur
gefilt — `H150` trägt Mechanismus, Kette (auch an `e45c0ca`), Preis und Test.

### M1–M4, N2–N4

* **M1** `H125` auf den Stand nach B1 gebracht: die Tabellenzeile `cd outbox & rm -rf .` sagt jetzt
  „rc 0 → rc 2", Absatz (d) und das Urteil zählen `H144` nicht mehr zu den nicht gedeckten Klassen
  (drei statt vier).
* **M2** die zwei Zeiger, die mit dem zurückgezogenen zweiten Scope-Leser verloren gingen, stehen
  wieder dort, wo die Regel heute lebt: `H142`/`H143` in den Docstrings von `scopes.overlaps` und
  `scopes.owns_anything_outside`. Damit stimmt der Satz in `tools/check_scope_overlap.py:20`.
* **M3** die Zahl „0 fehlend" in §7 war gegen den Stand VOR dem Neubeurteilen gemessen; korrigiert
  auf 28, mit der Aufteilung je Eintrag.
* **M4** die vier Auftrags-Befunde stehen als Zeilen 9–12 in §6.
* **N2** der Schiedsrichter für die gegenstandslose Dashboard-`VIEWS`-Naht ist keine
  Zeichenkettensuche mehr, sondern der Sammler (`--collect-only` = no tests).
* **N3** E's Satz (a) ist additiv — zur Kenntnis genommen, nichts zu bauen.
* **N4** die Sammelzahl steht ausschließlich in §8 — mit dem Lauf, dem heutigen Stand und der Differenz; hier nur der Zeiger.

### Läufe der Nacharbeit 1

Nur lesende Knoten während der Arbeit; nach der letzten Kit-Code-Änderung und nach dem zweiten
Stempel dann VOLL jede Suite, die eine geänderte Datei liest (DEC-0063 (4)). Geänderte Dateien:
`team-kits/office-team/hooks/guard_fs_tripwire.py`, `team-kits/office-team/hooks/_filing.py`,
`team-kits/kernel/scopes.py`, `tools/test_hooks.py`, `docs/POST_V2_WISHLIST.md`,
`project_memory/staging/TSK-0120/merge-protocol.md`, die drei `VERSION`.

| Lauf | liest | Ergebnis | Dauer |
|---|---|---|---|
| `tools/test_hooks.py` (voll) | die acht Office-Haken als Prozesse, `guard_fs_tripwire`, `_filing` | **943 passed, 13 skipped** | 17:20 |
| `test_hooks_v2` + `test_office_duties` + `test_parallel_scopes` + `test_parallel_streams` + `test_repo_hygiene` + `test_shortening_net` + `test_ci_lint_pinned` + `test_context_budget` + `test_disposition` + `test_kernel` (alle voll) | die Haken, `kernel/scopes.py`, `tools/**` als Text, die Stempel | **2465 passed** | 18:48 |
| `.claude/hooks/test_gates.py` (voll) | `docs/POST_V2_WISHLIST.md`, `CLAUDE.md`, `.claude/hooks/**` | **489 passed** | 28:33 |
| `ruff`, `validate.py` | — | sauber | — |

### Der zweite Stempel dieser Runde, mit Grund

Die Nacharbeit ändert Kit-Code (`office-team/hooks/guard_fs_tripwire.py`,
`office-team/hooks/_filing.py`, `kernel/scopes.py`), also verlangt `validate.py` einen neuen
Stempel: dev/office/research **`2026.09.04-1`**. Das ist der zweite Stempel der Runde und kein
Verstoß gegen „ein Stempel": die Regel meint einen Stempel je Änderungsstand, und ein Paket, dessen
Kit-Code sich nach dem Stempel bewegt, ist nicht gestempelt.


---

## 12. Nacharbeit 2 (Wiederholungsprüfung: FAIL, B 1 / M 4 / N 1)

Die Wiederholungsprüfung bestätigt den B1-Fix aus Nacharbeit 1 (drei ALLOWs und `H150` rc 2, zwölf
Kontrollen, R19–R21 je Hälfte, Kandidatenmenge bei 500 unsicheren Wechseln 3,29 s). Was folgt, sind
die sechs Befunde.

### B2 — dieselbe Stelle war ein zweites Mal verkürzt

Die Kandidatenmenge aus Nacharbeit 1 rechnete den nächsten Wechsel aus dem **neuesten** Kandidaten
aus und ersetzte bei einem sicheren Wechsel die ganze Menge durch dieses eine Ergebnis. Ein
RELATIVES Ziel bedeutet aber von jedem Kandidaten aus etwas anderes: `cd ../outbox` landet von
`docs` aus im `outbox` des Projekts und von der Wurzel aus außerhalb. Nach einem unsicheren
Wechsel ist der neueste Kandidat gerade die Position, an der die Shell vielleicht nie war — der
Wurzel-Kandidat fiel weg.

**Schiedsrichter war eine echte bash**, nicht eine Überlegung
(`_round-scratch/TSK-0120/verify_tools/shell_truth.py`, `b2_repro.py`; jeder Haken, den das Kit auf
`Bash` registriert, als Prozess; Pilot um `docs/inner` und `outbox/sub` erweitert):

| Befehlszeile | echte bash steht danach in | vorher | nachher |
|---|---|---|---|
| `cd docs \| true ; cd ../outbox ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| `false && cd docs ; cd ../outbox ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| `cd docs \| true ; cd ../docs/inner ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| KONTROLLE `cd docs ; cd ../outbox ; rm -rf .` | `outbox` | rc 0 | rc 0 |
| 17 weitere Kontrollen und Preise | — | unverändert | unverändert |

**Gebaut** (vier Zeilen, `guard_fs_tripwire.py:735-741`): der Wechsel wird aus JEDEM Kandidaten
ausgerechnet (`mapped`), ein sicherer Wechsel ersetzt die Menge durch die Ergebnisse, jeder andere
legt sie daneben; Reihenfolge und Eindeutigkeit über `dict.fromkeys`. Der `H150`-Zusatz (die Wurzel
tritt bei einem unberechenbaren Wechsel hinzu) sitzt jetzt im selben Ausdruck.

**Rot zuerst**, in einer Kopie außerhalb des Repos:

| # | Wiederhergestellter Defekt | rot in | grün geblieben |
|---|---|---|---|
| R22 | die ganze Lesart der Nacharbeit 1 kehrt zurück | `test_a_relative_change_is_computed_from_every_position_it_could_start_in` | die drei anderen Schiedsrichter |
| R23 | der Wechsel wird nur aus dem neuesten Kandidaten gerechnet | derselbe | dito |
| — | Kontrolle ohne Mutation | — | 4 passed |

Das ist genau der Grund, warum dieser Befund einen EIGENEN Test braucht: die Formen der drei
bestehenden Schiedsrichter bewegen sich von der Wurzel WEG, also fangen sie diese Hälfte nicht.

**Wächterkopf und Funktions-Docstring** sagen seitdem, dass der Wechsel aus jedem Kandidaten
gerechnet wird, nennen beide gescheiterten Zwischenstände mit ihrer Messung, und führen vier statt
drei Preise. `H144` und `H150` ebenso.

### M5 — die Preisliste, und eine Entscheidung mit Messung statt einer Annahme

Zwei Zeilen standen zur Prüfung.

* `pushd outbox ; pushd sub ; popd ; rm -rf .` (mit vorhandenem `outbox/sub`): echte bash steht
  danach in `outbox`, der Wächter verweigert. **Echte Über-Verweigerung** — als vierter Preis in
  `H144`, in `H150` und im Wächterkopf benannt.
* `cd <absoluter Pfad>/outbox ; rm -rf .` unquotiert: **kein Preis, gemessen.** Eine echte bash
  antwortet auf dieselbe Zeile `cd: too many arguments` und bleibt stehen, weil der Pfad ein
  Leerzeichen trägt und unquotiert zwei Argumente sind — der Wächter gibt also die RICHTIGE
  Antwort. Quotiert folgen beide, Shell und Wächter (rc 0). Der Grund liegt damit nicht in der
  Absolutheit, sondern in der Wortzerlegung, und ein „folgen lassen" wäre eine Antwort auf eine
  Frage, die die Shell selbst anders beantwortet. Auf diesem Host trägt jedes zulässige
  Piloten-Verzeichnis ein Leerzeichen (`C:\Offline Repos\…`), also ist die leerzeichenfreie
  Variante hier nicht messbar — das ist benannt und nicht behauptet.

### M6, M7, M8, N5

* **M6** die Sammelzahl steht jetzt an genau einem Ort (§8), mit Lauf, heutigem Stand und Differenz.
* **M7** die Zählregel steht neben der Zahl. Nach der richtigen Regel — eine nicht-leere Zeile, die
  nicht als GANZE ZEILE im Ergebnis vorkommt — sind es A 9, B 10, D 11; die schwächere
  Teilzeichenketten-Regel zählt zwei weniger. Beide Messungen und der Unterschied stehen in §7.
* **M8** `tools/test_e2e.py` (fährt `guard_fs_tripwire.py` als Prozess) und `tools/test_migrate.py`
  (öffnet die Löcherliste) fehlten in der Leserliste der Nacharbeit 1. Beide sind jetzt in der
  Tabelle unten und nach der B2-Änderung erneut gefahren.
* **N5** der Fließtext, der in der Lauf-Tabelle von §8 stand, steht darunter.

### Der dritte Stempel dieser Runde, mit Grund

Die Nacharbeit ändert `office-team/hooks/guard_fs_tripwire.py` und sonst keine Kit-Datei, also
stempelt `bump_kit_version.py` genau ein Kit: office **`2026.09.04-2`**, dev und research bleiben
auf `2026.09.04-1`. Der Stempler entscheidet das aus dem Hash und nicht aus einer Ansage — das ist
die Probe darauf, dass die Änderung wirklich nur ein Kit berührt.

### Läufe der Nacharbeit 2

Geänderte Dateien: `team-kits/office-team/hooks/guard_fs_tripwire.py`, `tools/test_hooks.py`,
`docs/POST_V2_WISHLIST.md`, `project_memory/staging/TSK-0120/merge-protocol.md`,
`team-kits/office-team/VERSION`.

| Lauf | liest | Ergebnis | Dauer |
|---|---|---|---|
| `tools/test_hooks.py` + `tools/test_e2e.py` + `tools/test_migrate.py` (alle voll) | die Haken als Prozesse, `guard_fs_tripwire`, die Löcherliste | **1105 passed, 13 skipped** | 21:24 |
| `tools/test_parallel_scopes.py` + `tools/test_parallel_streams.py` (voll) | `kernel/scopes.py` | **43 passed** | 27 s |
| die drei Löcherlisten-Knoten aus `tools/test_migrate.py` | `docs/POST_V2_WISHLIST.md` | **3 passed** | 3 s |
| die fünf Löcherlisten-Knoten aus `.claude/hooks/test_gates.py` | dito | **5 passed** | 2 s |
| `ruff`, `validate.py` | — | sauber | — |

`tools/test_e2e.py` und `tools/test_migrate.py` sind die zwei Leser, die in Nacharbeit 1 fehlten
(Prüferbefund M8); sie stehen seitdem in dieser Tabelle und laufen mit.

---

## 13. Abschlusszeilen (dritte Merge-Prüfung: PASS, 0 B / 0 M / 2 N)

### N6 — der fünfte Preis gehört PowerShell

`_filing.changes_the_calling_shell` liest ein einzeichiges `|` als Subshell, weil eine
Bash-Pipeline eine ist. Eine PowerShell-Pipeline ist keine — sie läuft im selben Prozess —, also
verweigert die Regel dort mehr, als sie müsste. Nachgemessen über die auf `PowerShell`
registrierten Haken als Prozesse: `Set-Location docs | Out-Null ; Set-Location ../outbox ; rm -rf .`
ist **rc 2**, während die Shell wirklich in `outbox` steht; `Set-Location outbox ; rm -rf .` bleibt
rc 0 und `Set-Location archive ; rm -rf .` rc 2. Fail-closed, also kein Loch — aber ein Preis, und
er steht jetzt in `H144`, in `H150` (als Zeiger) und im Wächterkopf.

### N7 — die dritte Hälfte ist gehalten, nur nicht von einem einzelnen Test

Die Prüfung meldete, dass die Mutation „nur aus `standing[0]`" in
`test_a_relative_change_is_computed_from_every_position_it_could_start_in` grün bleibt. Gemessen,
statt es als fail-closed abzuhaken: **keine** Ein-Kandidaten-Lesart überlebt die Datei.

| Mutation | rot in |
|---|---|
| die Zerstörung fragt nur den NEUESTEN Kandidaten | `test_a_relative_change_is_computed_from_every_position_it_could_start_in` **und** `test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` |
| die Zerstörung fragt nur den ERSTEN Kandidaten | `test_a_change_the_shell_may_not_have_made_leaves_both_positions_open` (dessen `cd outbox && cd .. && rm -rf .` hat `outbox` zuerst und die Wurzel danach) |

Ein Fall, der die ERSTE-Lesart im B2-Test allein rot macht, ist versucht und **verworfen, gemessen**:
mit zwei Kandidaten, die beide im Projekt liegen, folgen `_filing`s eigene Basen jedem `cd`, also
verweigert die LÖSCH-Regel die Zeile, bevor die Fege-Regel erreicht wird — derselbe Trugschluss wie
in Nacharbeit 1, zum zweiten Mal gemessen und diesmal im Docstring festgehalten. Geblieben ist eine
Gegenrichtung: zwei Kandidaten, keiner die Wurzel, keiner mit einem Fach → rc 0.

### H144 — „auf diesem Host nicht messbar" war zu bequem

Der Prüfer hat es in einem leerzeichenfreien Piloten gemessen (`C:/tmp_nospace_probe/office`,
danach gelöscht): `cd C:/…/office/outbox ; rm -rf .` ist rc 0, quotiert ebenso, und
`…/archive` rc 2 — der Wächter folgt einem absoluten `cd` **vollständig**, in dieser Klasse gibt es
keinen Preis. Der Satz ist durch diese Messung ersetzt; was wie eine Über-Verweigerung aussah, ist
die Wortzerlegung eines unquotierten Pfades mit Leerzeichen, und dort gibt der Wächter dieselbe
Antwort wie die Shell.

### Der vierte Stempel dieser Runde, mit Grund

Der Wächterkopf ist Kit-Code, also stempelt `bump_kit_version.py` erneut — und wieder nur das eine
Kit, dessen Hash sich bewegt hat: office **`2026.09.04-3`**, dev und research unverändert
`2026.09.04-1`.

### Läufe der Abschlusszeilen

Geänderte Dateien: `team-kits/office-team/hooks/guard_fs_tripwire.py`, `tools/test_hooks.py`,
`docs/POST_V2_WISHLIST.md`, `team-kits/office-team/VERSION`, dieses Protokoll.

| Lauf | Ergebnis | Dauer |
|---|---|---|
| die `H144`/`H150`-Knoten und die Tripwire-/Sweep-/Tray-Knoten aus `tools/test_hooks.py` | **68 passed** | 4:25 |
| die Löcherlisten-Knoten aus `tools/test_migrate.py` | **3 passed** | 3 s |
| die Löcherlisten-Knoten aus `.claude/hooks/test_gates.py` | **5 passed** | 2 s |
| `ruff`, `validate.py` | sauber | — |
