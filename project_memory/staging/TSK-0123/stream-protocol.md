# TSK-0123 — Strom G4-3 „Verfahren und Rückschau" (PR-0006, AC-1..AC-4) — Stand nach Nacharbeit 1

| | |
|---|---|
| Item | `TSK-0123`, Ziel `PR-0006`, Freigabe `APR-0005` (Plan-Freigabe, `DEC-0068`) |
| Arbeitsbaum | `C:/Offline Repos/v2-testbed/_worktrees/g4-procedure`, Branch `g4/procedure`, Basis `75a00d1` |
| Scratch | `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0123/` (ausschließlich) |
| Stempel | **provisorisch**: dev/office/research je `2026.09.05-2` — der Release stempelt einmal, nach dem Merge |
| Patch | `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0123/stream-procedure.patch` — 20 Köpfe, **127 110 B**, 0 CR, **ohne** die `VERSION`-Hunks |
| Umfang | 22 geänderte Dateien, 1 neue |
| Commit / Push / Install | keiner, keiner, keiner |
| Reservierte Löcher | `H157`, `H158`, `H159` — die im Item reservierten und keine weiteren |
| Prüfrunde 1 | `verify-round-1.md` — FAIL, B1–B4 blockierend, R1–R5 als Reste. **Alle vier geschlossen**, alle fünf Reste bearbeitet; zwei davon (R1, R2 zur Hälfte) gebaut statt nur aufgeschrieben |
| Prüfrunde 2 | `verify-round-2.md` — **PASS** auf allen Kriterien und Pflichten; zwei nicht blockierende Reste (N1, N2) und ein Nit. **Beide Reste geschlossen und rot nachgemessen**, der Nit korrigiert |
| Prüfrunde 3 | `verify-round-3.md` — **PASS**, Schlussurteil; ein kleiner Rest (N3). **Geschlossen und in beide Richtungen gemessen.** Der Strom ist damit zu; die nächste Prüfung ist die der Merge-Runde über den ganzen Patch |

---

## 1. Vorgefunden — gelesen, nicht erinnert

| Frage | Befund | Wo gemessen |
|---|---|---|
| Gibt es eine „Planprüfung", die eine Auftragszeile verweigert? | **Nein.** `gate_dispatch` prüft den Dispatch-Kopf gegen die Lease und sagt das selbst („WHAT THIS GATE PARSES: the header, and only the header … Free prompt prose is never evidence of anything"); Gate 2 dieses Repos verlangt nur eine Id, die auflöst und nicht terminal ist | `team-kits/dev-team/hooks/gate_dispatch.py` Kopf, `.claude/hooks/gate_spawn_needs_item.py` Kopf |
| Wer löst den Auditor-Lauf aus? | Ein **Takt**, keine Anlässe: `_routine.audit_period_id` ist die ISO-Woche, `_routine.routine_duties` antwortet aus Datum + Laufprotokoll | `team-kits/*/hooks/_routine.py` |
| Ist das project-auditor-SKILL gespiegelt? | Nein (72/79/74 Zeilen). `test_shared_skill_contract` spiegelt nur REFERENZ-Skills; der Auditor ist ein Rollen-Skill | `wc -l`, `tools/test_shared_skill_contract.py` |
| Liegt ein Lead-SKILL im Byte-Budget? | Nein — `lead_package.files` = Verfassung + Agent-Datei des Leads; das SKILL ist `on_demand_files`. Die **Verfassung** liegt drin, also zieht die Nacharbeit für B4 am Ratschen-Rekord | `tools/lead_package.py` |
| Ist ein Lead-SKILL gepinnt? | **Ja** — `_pinned_files = _lead_package + on_demand_files + _reference_doc` | `tools/test_shortening_net.py` |
| Liest irgendetwas Zeiger in `.claude/agents/`? | **Nein.** `test_repo_hygiene._texts_that_answer_for_a_claim` walks `team-kits/` und `docs/`; `test_gates.py` sein eigenes Verzeichnis | `tools/test_repo_hygiene.py` |
| Stand die zweite Hälfte von FR-0084 irgendwo im Kit? | **Nein** — Befund B4 der Prüfung. Vor der Nacharbeit nur ein Aufzählungspunkt in `.claude/agents/harness-implementer.md` | Prüfbericht Runde 1, B4 |
| Zeilenenden | alle berührten Dateien reines LF, 0 CR-Bytes | `_round-scratch/TSK-0123/eol_check.py` |

---

## 2. Plan und der verworfene Weg

Gebaut: der Rückschau-Schritt im Auditor-SKILL **und** in der Auditor-Rollendefinition aller drei
Kits (AC-1, erste Hälfte); die Pflicht des verworfenen Weges als **geteilter Absatz in allen drei
Verfassungen** (AC-1, zweite Hälfte, FR-0084 (2)); die zwei Lesungen vor dem Auftrag, byte-gleich, in
allen drei Lead-SKILLs mit einer Zeigerzeile in jeder Arbeitsschleife (AC-2 + AC-3); die drei
Orchestrator-Regeln und die Generation-3-Lektionen in den drei Harness-Rollentexten (AC-4); dazu
`tools/test_review_procedure.py`, das jeden dieser Texte **geparst nach Einheit** liest, und drei
Löcher-Einträge.

**Der verworfene Weg (eine Zeile, FR-0084-Form):** verworfen wurde, die Pflicht des verworfenen Weges
nur als Prosa im Rollentext dieses Repos stehen zu lassen und die Kit-Hälfte als benannte Ausnahme zu
führen — verworfen, weil der Wunsch die Verfassungen ausdrücklich als Ort nennt, weil `CLAUDE.md` für
eine gemessene offene Lücke keinen dritten Zustand kennt, und weil die Verfassung als einziges der
berührten Dokumente wirklich LÄDT und damit jede bauende Rolle erreicht statt nur die, die ihr SKILL
öffnet; **was der kleinere Weg nicht abgedeckt hätte:** die drei Kits, also jedes Projekt außer
diesem. Der Preis des gewählten Weges ist gemessen und bezahlt: +886 B je Kit im geladenen Lead-Paket,
mit Begründung im Ratschen-Journal.

---

## 3. Nahttabelle

| Naht | Datei / Sache | Wer | Wann |
|---|---|---|---|
| **empfangen bei Zuschnitt** | — | — | **keine** |
| erwartet beim Merge | Test-Umfangs-Gate (FR-0086/FR-0057) | **G4-1** | Merge |
| erwartet beim Merge | SR-Pflicht, Inbox-Regel, Löcher als Items, Lease-Verweigerung | **G4-2** | Merge |
| erwartet beim Merge | keine erwartet | G4-4 | — |
| **gesendet an G4-1** | `team-kits/*/hooks/_routine.py` + `session_status.py` | G4-1 baut, ich schreibe nur Text | Merge — Satz unten |
| geteilt | `team-kits/*/VERSION` | jeder Strom stempelt provisorisch, der Release stempelt einmal | Merge |
| geteilt | `docs/POST_V2_WISHLIST.md` | abschnittsweise mergen; `H157`–`H159` und ihre drei Zeilen in der Übersichtstabelle sind meine | Merge |
| geteilt | `docs/reviews/phase0-disposition.md` | von `pin_constitution_sections.py` und `record_lead_package_sizes.py` angehängt: **16 neue Journalzeilen** (13 vom Pin-Skript, 3 vom Größen-Skript). Der Diff zählt 21 Zeilen mehr — vier Leerzeilen als Trenner und eine ältere Größenzeile, die nur verschoben wurde | Merge |
| geteilt | `tools/constitution_section_pins.json` | von demselben Pin-Skript geschrieben | Merge |
| geteilt | `tools/lead_package_sizes.json` | **NEU seit Nacharbeit 1** — die Verfassungsänderung für B4 bewegt den Byte-Ratschen. Geteilt mit **jedem** Strom, der ein Lead-Paket wachsen lässt: der Rekord ist eine Zeile je Kit, und zwei Ströme schreiben dieselbe | Merge |
| geteilt | `team-kits/*/constitution/AGENTS.md` | **NEU seit Nacharbeit 1** — ein geteilter Absatz, byte-gleich, unter der Lead-in-Regel. Geteilt mit **G4-1 und G4-2**, deren Sätze in dieselben Verfassungen kommen; die Lead-in-Regel (`tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`) ist beim Merge der Schiedsrichter | Merge |
| geteilt | `tools/` | ein NEUES Modul; keine bestehende Datei unter `tools/` geändert außer den zwei erzeugten Datensätzen | Merge |

### Der Satz an G4-1, wörtlich

> Der Rückschau-Schritt des `project-auditor` hängt an vier ANLÄSSEN (eine Phase ist zu Ende, etwas
> wurde gemergt oder ausgeliefert, eine Befundklasse wiederholt sich, die Prämisse einer
> Entscheidung hat sich bewegt). Gebaut ist bis heute nur ein TAKT: `_routine.routine_duties`
> beantwortet die Fälligkeit allein aus dem Datum und dem Laufprotokoll unter
> `project_memory/.audit/hook_events.jsonl` — gemessen in
> `tools/test_review_procedure.py::test_no_occasion_makes_the_audit_run_due_and_that_is_the_seam`:
> zwei Projekte desselben Tages, eines mit einem auf `DELIVERED` gelaufenen Ziel, melden dieselbe
> Pflicht Wort für Wort. Wer den Ereignis-Auslöser baut, baut ihn in `_routine.py` und meldet ihn
> über `session_status.py`; **dieser Test geht dann rot**, und mit ihm ist die Grenzaussage in den
> drei Auditor-SKILLs und den drei Auditor-Rollendefinitionen zu korrigieren („None of the four
> reaches you as a trigger … no hook and no gate watches for an occasion"). Der Eintrag ist `H158`.

---

## 4. Je Abnahmekriterium: Abnahmezeile und Rot-Messung

Alle Rot-Messungen liefen in einer **Kopie außerhalb des Repos** (`_round-scratch/TSK-0123/red/`,
ohne `.git`), gefahren von `_round-scratch/TSK-0123/redcase.py` — einem Rig, das (a) sich weigert,
außerhalb seines eigenen Verzeichnisses zu schreiben, (b) **binär** liest und schreibt, (c) **einen
Fall pro Aufruf** macht, und (d) jede Textstelle über einen **ASCII-Marker lokalisiert und
herausschneidet**, statt sie als Byte-Literal zu buchstabieren: die Texte tragen Geviertstriche, und
ein Byte-Literal mit einem darin ist ein Syntaxfehler, sobald irgendeine Schicht zwischen Autor und
Datei ein Escape neu liest — das ist mich in dieser Runde zweimal Zeit gekostet. Journal:
`_round-scratch/TSK-0123/redfirst.log`.

**Basisläufe:** vor dem ersten Fall rc 0 / 18 passed, nach dem letzten rc 0 / 18 passed.

### AC-1 (FR-0084) — Rückschau als EREIGNIS, und der verworfene Weg in JEDEM Plan

**Abnahmezeile, erste Hälfte:** Der `project-auditor` aller drei Kits führt einen Rückschau-Schritt
mit vier Anlässen und vier gemessen zu beantwortenden Fragen; das Ergebnis geht als drei Zeilen für
den Nutzer in die Evidence `summary`; der Schritt steht **byte-gleich** in allen drei Kits und die
Anlassregel **zusätzlich in der Rollendefinition**, weil der Skill-Zustellweg an einen Subagenten
unbestimmt ist. Der Ereignis-Auslöser ist NAHT zu G4-1 und wird im Text als fehlend benannt.

**Abnahmezeile, zweite Hälfte (neu in Nacharbeit 1, B4):** Die Pflicht „dein Plan nennt den
verworfenen Weg" steht als **ein Absatz, byte-gleich, in allen drei Verfassungen**, im Abschnitt
„Your work loop — the SEQUENCE, and the duties that have no gate behind them". Sie bindet damit jede
bauende Rolle eines Kits, nicht nur die, deren Prozedurdokument dieser Strom schreiben darf; sie nennt
ihren Wunsch (`FR-0084`) und den Test, der sie hält; und sie sagt ihre eigene Grenze.

| # | Mutation | rc | rot geworden |
|---|---|---|---|
| 0 | Rückschau-Schritt aus allen drei Auditor-SKILLs (HEAD-Blob) | 1 | `test_the_auditing_role_of_every_kit_runs_a_retrospective_and_it_is_one_text`, `test_the_retrospective_step_states_the_limit_it_runs_under` |
| 1 | Schritt bleibt, eine Kit-Kopie um **ein Wort** umformuliert | 1 | `…runs_a_retrospective_and_it_is_one_text` |
| 2 | die vier Anlass-Marken gestrichen | 1 | dito |
| 3 | ehrliche Grenze **ersetzt** durch eine Überbehauptung | 1 | `test_the_retrospective_step_states_the_limit_it_runs_under` |
| 4 | Überbehauptung **hinzugefügt**, ehrliche Grenze bleibt | 1 | dito |
| 5 | Anlass-Punkt aus allen drei Rollendefinitionen (HEAD-Blob) | 1 | `test_the_occasion_rule_stands_in_the_file_a_spawn_actually_loads` |
| 6 | Punkt bleibt, eine Kit-Kopie umformuliert | 1 | dito |
| 31 | **die drei Zeilen für den Nutzer gelöscht** (R2, vorher folgenlos) | 1 | `…runs_a_retrospective_and_it_is_one_text` |
| 26 | **Verfassungsabsatz aus allen drei Kits entfernt** (B4) | 1 | `test_every_constitution_asks_a_plan_for_the_way_it_rejected`, `test_the_rejected_alternative_rule_claims_no_enforcement_it_does_not_have` |
| 27 | Absatz bleibt, eine Kit-Kopie um **ein Wort** umformuliert | 1 | `test_every_constitution_asks_a_plan_for_the_way_it_rejected` |
| 28 | der Absatz verliert seinen eigenen Zeiger | 1 | beide |
| 29 | die ehrliche Grenze des Absatzes durch eine Überbehauptung ersetzt | 1 | `test_the_rejected_alternative_rule_claims_no_enforcement_it_does_not_have` |

**Pilot, aufgesetzt und gemessen** (`_round-scratch/TSK-0123/pilot/`, eigenes HOME, keine
Installation in den globalen Speicher; `init_project_memory.sh dev-team` rc 0, `scaffold_team.sh
dev-team` rc 0):

| was ankommt | wo | Treffer |
|---|---|---|
| die Pflicht „verworfener Weg" | `AGENTS.md` (die Verfassung, über den `CLAUDE.md`-Shim geladen) | 1 |
| ihr Test-Zeiger | `AGENTS.md` | 1 |
| der Rückschau-Schritt | `.claude/skills/project-auditor/SKILL.md` | 1 |
| die Anlassregel | `.claude/agents/project-auditor.md` | 1 |
| die Auftragslesung | `.claude/skills/project-manager/SKILL.md` | 2 |

Damit sitzt die zweite Hälfte von FR-0084 in dem einen Text, der bei jedem Sitzungsstart LÄDT
(`lead_package.files`) — nicht in einem, den jemand erst öffnen muss.

**Kanal-Abweichung, benannt (R5):** AC-1 sagt „the session brief carries … three lines to the user".
Gebaut ist der Weg über die Evidence-`summary`. Grund, gemessen: `kernel/report.generate_session_brief`
schreibt `kit`, `active_roots`, `active_tasks`, `open_approvals`, `staging_pointers`,
`standing_decisions`, `budget_status` — **keine Evidence und keine `summary`**; der Auditor darf den
Nutzer nicht ansprechen (Hard limit seines eigenen Rollentextes), also ist der einzige Weg zum Nutzer
das Feld, das der Orchestrator weiterreicht. Dass dieses Feld existiert und Pflicht ist, steht im
laufenden Vertrag (`kernel/schemas/result_envelope.yaml`), und der Test liest es dort ab statt es zu
buchstabieren. Der Weg über den Session-Brief bliebe eine Kernel-Änderung — verbotener Bereich dieses
Stroms.

### AC-2 (FR-0005) — Zuschnitt-Kritiker vor dem Auftrag

**Abnahmezeile:** Eine byte-gleiche Sektion in allen drei Lead-SKILLs mit dem mechanischen Auslöser,
den drei Auflagen aus FR-0005 und der Pflicht, die Wahl als Decision-Item (`DEC`) festzuhalten; dazu
eine Zeigerzeile in **jeder** Arbeitsschleife, die **an einer Satzgrenze** sitzt.

| # | Mutation | rc | rot geworden |
|---|---|---|---|
| 7 | Sektion aus allen drei Lead-SKILLs (HEAD-Blob) | 1 | drei Tests |
| 10 | die drei Auflagen des kleineren Plans gelöscht | 1 | `test_every_kit_lead_is_given_the_ways_a_work_order_line_goes_wrong` |
| 11 | die Zeigerzeile aus der Arbeitsschleife entfernt | 1 | `test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix` |
| 12 | ehrliche Grenze **ersetzt** | 1 | `test_the_order_reading_claims_no_enforcement_it_does_not_have` |
| 13 | Überbehauptung **hinzugefügt**, Grenze bleibt | 1 | dito |
| 20 | **die Zeigerzeile zurück in die Mitte ihres Satzes** (B1) | 1 | `test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix` |
| 30 | **Überbehauptung als Haken-DATEINAME** (R1, vorher folgenlos) | 1 | `test_the_order_reading_claims_no_enforcement_it_does_not_have` |
| 32 | **die Aufzeichnungspflicht gelöscht** (R2, vorher folgenlos) | 1 | `test_every_kit_lead_is_given_the_ways_a_work_order_line_goes_wrong` |

### AC-3 (FR-0010) — die fünf Fehlformen

**Abnahmezeile:** Dieselbe Sektion trägt die fünf Formen als Prüfschritte, jede mit ihrem Fall und dem
Entscheidungs-Item, das ihn hält (`DEC-0010`, `DEC-0011`, `DEC-0012`).

| # | Mutation | rc | rot geworden |
|---|---|---|---|
| 8 | **eine** der fünf Formen gelöscht | 1 | `test_every_kit_lead_is_given_the_ways_a_work_order_line_goes_wrong` (+2 Nachbarn) |
| 9 | ein Fall-Zeiger auf ein Item gedreht, das der Zustand nicht hält | 1 | derselbe |

### AC-4 (DEC-0070) — Orchestrator-Regeln und die Lektionen der Arbeiter-Texte

**Abnahmezeile:** `.claude/agents/harness-lead.md` trägt die Regeln **1, 2 und 5** — als MENGE
geprüft, nicht gezählt —, jede mit einem Zeiger, der ihre Regelnummer nennt, und jede mit einem
Mechanismus in Backticks (`check-scopes`, `guard_fs_tripwire`, `ListAgents`), den eine Umformulierung
fallen lässt. `harness-implementer.md` und `harness-verifier.md` tragen die Generation-3-Lektionen als
**eigene Aussagen mit eigenem Zeiger** (`FR-0084`, `DEC-0070`, `TSK-0120`), keine zwei hinter einer.

| # | Mutation | rc | rot geworden |
|---|---|---|---|
| 14 | Regeln aus `harness-lead.md` (HEAD-Blob) | 1 | `test_the_lead_role_text_carries_the_orchestrator_rules_with_their_pointers` |
| 15 | **eine** der drei Regeln gelöscht | 1 | derselbe |
| 16 | zwei Regeln verlieren ihren Zeiger | 1 | derselbe |
| 17 | eine Regel zeigt auf ein Item, das der Zustand nicht hält | 1 | derselbe + `test_every_item_pointer_the_harness_role_texts_write_resolves` |
| 24 | **Regel 2 gelöscht, Regel 1 verdoppelt — die Zahl bleibt drei** (B3) | 1 | `…carries_the_orchestrator_rules_with_their_pointers` |
| 25 | **Regel 5 zur Parole umformuliert, Zeiger bleibt** (B3) | 1 | derselbe |
| 18 | die Lektionen aus beiden Arbeiter-Texten (HEAD-Blob) | 1 | `test_every_harness_role_text_answers_for_the_lessons_it_was_given` |
| 19 | ein Rollentext nennt einen Test, den es nicht gibt | 1 | `test_every_test_pointer_the_harness_role_texts_write_resolves` |
| 21 | **alle drei Umsetzer-Lektionen gelöscht, Überschrift bleibt** (B2) | 1 | `test_every_harness_role_text_answers_for_the_lessons_it_was_given` |
| 22 | **EINE Umsetzer-Lektion gelöscht** (B2) | 1 | derselbe |
| 23 | **die Rig-Lektion des Prüfer-Textes gelöscht** (B2) | 1 | derselbe |

---

## 5. Können die Prüfungen scheitern?

Jeder Leser dieses Moduls wurde in **beide** Richtungen mutiert, in derselben Kopie außerhalb des
Repos (`redfirst_readers.py`, `red_rule_reader.py`, `red_readers2.py`):

| Leser-Mutation | rc | rot |
|---|---|---|
| Grundlauf / zurückgesetzt | 0 | — |
| `_item_citations` matcht **nichts** | 1 | 6 Tests |
| `_item_citations` matcht **jedes Großwort** | 1 | 4 Tests |
| `_question_steps` nimmt **jeden** Schritt | 1 | 2 Tests |
| `_order_reading_sections` nimmt **jede** Sektion | 1 | 3 Tests |
| `_rule_pointer_rx` matcht **jede Erwähnung** | 1 | `test_the_rule_reader_can_tell_a_rule_from_a_mention_and_a_slogan_from_a_rule` |
| `_rule_pointer_rx` matcht **nichts** | 1 | derselbe + der Regel-Test |
| `_ends_a_sentence` sagt **jede** Zeile endet einen Satz | 1 | `test_the_position_reader_can_tell_a_sentence_boundary_from_the_middle_of_one` |
| `_ends_a_sentence` sagt **keine** | 1 | derselbe + `…is_a_step_of_the_work_loop_and_not_an_appendix` |
| `_lead_in_units` findet **keine** Aussage | 1 | 4 Tests |
| `_lead_in_units` macht die **ganze Datei** zu einer Aussage | 1 | 4 Tests |
| `_mechanism_terms` findet **immer** einen Mechanismus | 1 | der Regel-Boden |
| `_mechanism_terms` findet **nie** einen | 1 | derselbe + der Regel-Test |

### Die zwei Grenzen, am Piloten außerhalb des Repos gemessen

* **Kein Leser urteilt über den Wortlaut einer Auftragszeile.** Ein `TSK`, dessen `expected_outputs`
  einen Baustein nennt, den kein Abnahmekriterium seines Ziels nennt, wird erfasst, geleast und steht
  auf `LEASED` (`…::test_nothing_reads_what_a_work_order_LINE_says`, Eintrag `H157`).
* **Kein Anlass macht den Auditor-Lauf fällig.** Zwei Projekte desselben Tages, eines mit einem auf
  `DELIVERED` gelaufenen Ziel: ohne Laufprotokoll dieselbe Pflicht Wort für Wort, mit Laufprotokoll
  beide still (`…::test_no_occasion_makes_the_audit_run_due_and_that_is_the_seam`, `H158`, NAHT).

Beide Tests sind geschrieben, um **rot zu werden**, sobald jemand die jeweilige Prüfung baut.

---

## 6. Was bewusst NICHT geschlossen, aber benannt ist

1. **`H157` — kein gebauter Leser urteilt über den Wortlaut einer Auftragszeile.** Nicht geschlossen,
   weil FR-0010 das vor der Messung entschieden hat („ein Test dafür ist eine Heuristik über Prosa,
   also bauen wir keinen") und `DEC-0056` (b) ein Gate nur für eine gemessene IRRTUMS-Klasse zulässt.
   Begrenzt durch: die Lesung steht IN der Arbeitsschleife **und an einer Satzgrenze**, jede Form
   nennt ihr Entscheidungs-Item, die Wahl wird als `DEC` festgehalten, und der Abschnitt behauptet
   keinen Schutz — alles gemessen.
2. **`H158` — die Rückschau hat keinen Ereignis-Auslöser.** NAHT zu G4-1; die Verdrahtung liegt im
   verbotenen Bereich dieses Stroms.
3. **`H159` — der Zeigerleser sieht nur Backticks und nur Item-Ids.** Vier Sorten fauler Zeiger
   bleiben grün (`_round-scratch/TSK-0123/residue.py`, alle rc 0 / 18 passed gegen die Kontrolle mit
   Backticks bei rc 1). Dieselbe Entscheidung, die `test_gates._points_into_this_file` für
   `.claude/hooks/` getroffen hat.
4. **Was eine Aussage SAGT, prüft niemand — nur dass sie da ist und woher sie kommt.** Gemessen und
   nicht geschlossen: eine Regel oder eine Lektion, die um ihren eigenen Zeiger herum umformuliert
   wird und ihren Mechanismus-Namen behält, bleibt grün; und ein Fehler, den alle drei Kits
   GLEICHZEITIG und GLEICH machen, bleibt grün, weil die Gleichheitsprüfung die Kits gegeneinander
   hält und nicht gegen einen Maßstab. Zwei der drei Fälle, die die Prüfung dafür anführte, sind
   inzwischen zu: die drei Zeilen für den Nutzer und die Aufzeichnungspflicht haben je einen aus
   laufendem Code abgeleiteten Anker (`result_envelope`-Feld `summary`, Typschlüssel `DEC`) und sind
   rot messbar (Fälle 31, 32). Was bleibt, ist der dritte: dieselbe falsche Umformulierung in allen
   drei Kits.
5. **Die Ehrlichkeitsprüfung bleibt endlich — aber deutlich weiter als am Anfang.** Drei Runden,
   drei Messungen, drei Verengungen bzw. Erweiterungen, jede in beide Richtungen gemessen:
   * **R1 (Runde 1):** `gate` matcht nicht in `gate_dispatch` — eine Überbehauptung in dieser
     Schreibweise ging durch. `_mechanism_words` nimmt seither die Namen der Haken dazu (Fall 30, rot).
   * **N2 (Runde 2):** die erste Fassung las dafür das VERZEICHNIS `hooks/` und nahm jede Helferdatei
     mit; `hooks/reading.py`, nirgends registriert, machte zwei ehrliche Blöcke rot. Jetzt entscheidet
     die **Registrierung** in `settings/settings.json` (`red_n2.py`: mit der neuen Fassung grün, mit
     der Verzeichnis-Fassung genau die zwei gemeldeten Fehlschläge).
   * **N3 (Runde 3):** eine Registrierung ist eine KOMMANDOZEILE, und der Runner eines Kits nimmt die
     Haken als Argumente (`_gate.py gate_ledger_valid.py gate_second_booking.py`) — das letzte Wort zu
     lesen verlor den Runner und jeden verketteten Haken bis auf einen. Jetzt wird **jedes `.py`-Wort**
     der Zeile gelesen; das Vokabular wächst von 22/21/19 auf **25/27/22** Namen je Kit (`red_n3.py`:
     mit der neuen Fassung rot, mit der Letztes-Wort-Fassung grün).
   **Was bleibt, ausdrücklich:** (a) eine Überbehauptung, die **gar keinen** Mechanismus benennt
   („der Apparat verweigert das“), fällt weiter durch; (b) der Leser schaut **nicht auf das
   Dateisystem** — eine Registrierung, die eine Datei nennt, die das Kit nicht ausliefert, steuert ihren
   Namen bei und ist hier weder Absturz noch Signal (ob ein registrierter Haken existiert, fragt
   `tools/test_shortening_net.py`); (c) die Texte mussten so gestellt werden, dass die Verneinung VOR
   dem Namen steht, was ein Leser dieser Art verlangt und nicht misst.
6. **Eine Prosa-Aussage in `harness-lead.md` hält eine Lesung und keinen Test:** „no gate reads what
   an order LINE says — gate 2 asks only that the spawn names an item that resolves and is not
   terminal", gegen den Kopfkommentar von `.claude/hooks/gate_spawn_needs_item.py` gelesen.
   `test_gates.py` liegt im verbotenen Bereich, und ein Test unter `tools/`, der eine NICHT-Eigenschaft
   eines Gates behauptet, wäre eine Behauptung über alles, was das Gate nicht tut. Für die Kit-Seite
   derselben Aussage gibt es den Test.
7. **Der Positions-Leser sieht zwei Dinge nicht, und beide sind gemessen.** Er prüft die Satzgrenze,
   nicht welche unter mehreren Grenzen die RICHTIGE ist — das bleibt eine Lesung. Und er findet einen
   Einschub nur, wenn dieser **fett eingeleitet** ist: `_statement_around` steigt zur nächsten fett
   beginnenden Zeile hoch, weil das die Form einer Aussage in dieser Prosa ist, also steigt ein
   unfetter Einschub über seinen eigenen Anfang hinaus und wird an fremder Grenze beurteilt. Die
   Prüfung Runde 2 (N1) hat das gemessen: derselbe Zerriss wie B1, nur ohne Fettung, bleibt rc 0.
   Die andere Hälfte von N1 ist **zu**: der Leser läuft jetzt über ALLE Nennungen der Überschrift und
   nicht mehr nur über die erste, sodass eine saubere Zeigerzeile eine zerrissene weiter unten nicht
   mehr verdeckt (Fall 33, rot; Boden im Modul selbst).
8. **Das Rot-Rig hat keine Sperre.** Zwei gleichzeitige Läufe bauen dieselbe Kopie und zerstören
   einander — einmal durch meinen eigenen Fehler passiert, ohne Folgen für den Arbeitsbaum.

---

## 7. Läufe

| Lauf | Ergebnis |
|---|---|
| `test_role_contracts` + `test_shared_skill_contract` + `test_kit_neutrality` + `test_review_procedure` | **60 passed** in 11,99 s |
| `test_shortening_net` + `test_parallel_streams` | **65 passed** in 79,28 s |
| `test_reference_skills` | **18 passed** in 118,93 s |
| `test_repo_hygiene` + `test_routine_feed` | **54 passed** in 128,59 s |
| **Summe der lesenden Suiten** | **197 passed, 0 failed** |
| `python -B -m ruff check .` | All checks passed |
| `python -B tools/validate.py` | all structural checks passed |
| `tools/pin_constitution_sections.py --write --note …` | zweimal gefahren (6 + 4 + 3 Änderungen), je mit Journalzeile |
| `tools/record_lead_package_sizes.py --write --note …` | dev/office/research je **+886 B**, mit Grund im Journal |
| `tools/bump_kit_version.py` | dev/office/research je `2026.09.05-2` (**provisorisch**); nach Nacharbeit 2 `unchanged` — diese Runde hat nur `tools/` berührt, und der Kit-Hash liest `team-kits/` |

**Die volle Suite lief NICHT** (`DEC-0050`, `DEC-0063` (4), `DEC-0070` (4)); sie gehört zum Merge. Die
Läufe wurden in **vier kurze Fenster** geteilt, weil auf diesem Host andere Ströme arbeiten und die
Runde vier harte Abschaltungen erlebt hat.

---

## 8. (g)-Zeile für die Rückschau der Generation 4 — vollständig

| | |
|---|---|
| Wanduhr, gearbeitet | ~2 h bis zum ersten Bericht + ~1 h 15 Nacharbeit 1 + ~30 min Nacharbeit 2 + ~25 min Nacharbeit 3 = **~4 h 10** |
| Wanduhr, Spanne | 2026-09-04 06:13 bis 2026-09-05 ~02:0x — dazwischen vier harte Abschaltungen des Hosts und ~11 h Stillstand, die nicht Arbeitszeit sind |
| **Tokens (Umsetzer, alle Runden)** | erste Runde ~365 k · Nacharbeit 1 ~210 k · Nacharbeit 2 ~90 k · Nacharbeit 3 ~75 k = **~740 k** |
| Runden | **1 Bericht, 3 Nacharbeiten (2 auf Befunde + 1 Abschluss), 3 Verifikationen** (Runde 1 FAIL, Runde 2 PASS mit N1/N2, Runde 3 PASS mit N3) |
| Unterbrechungen | vier harte Abschaltungen des Hosts; Ursache vom Lead gemessen: das 16-Brenner-Lastrig eines Nachbarstroms sättigte alle 16 logischen Kerne neben den Suiten der anderen Ströme. Kein Befund, keine Auftragsänderung; der Arbeitsbaum lag jedes Mal vollständig auf der Platte. Gekostet: ein vollständiger Rot-Lauf und ein Suite-Lauf — daher ein Fall pro Aufruf und vier kurze Suite-Fenster |
| Befunde der Prüfung | 4 blockierend (B1–B4), 5 Reste (R1–R5), 2 Reste (N1, N2), 1 Rest (N3). **Fünf davon sind DIESELBE Klasse:** ein Zähler statt einer Identifikation, bzw. ein Leser, der weniger liest als sein Docstring behauptet (B2, B3, N1, N2, N3) |
| Selbstbefunde vor jeder Meldung | 2 (eine gefressene Zeilenschaltung; ein Regel-Zähler, der das Löschen einer Regel nicht sah) |
| Berührte Dateien | 22 geändert, 1 neu |
| Rot-zuerst-Messungen | **35 Defekt-Fälle** (`redcase.py`, Journal `redfirst.log`: 37 Zeilen rc 1, weil Fall 30 dreimal gefahren wurde — nach jeder Änderung am Vokabular — und 5 Basisläufe rc 0), **12 Leser-Mutationen**, **4 Rest-Mutationen**, **4 Gegenrichtungen** (N2 und N3 je in beide Richtungen) = **55**, alle in einer Kopie außerhalb des Repos |
| Nähte gesendet | **1** an G4-1 (Ereignis-Auslöser in `_routine.py` + `session_status.py`), wörtlich in §3, mit dem Test, der beim Bau rot wird (`H158`) |
| Nähte empfangen | bei Zuschnitt **keine**; erwartet beim Merge von G4-1 und G4-2, von G4-4 keine |
| Löcher | `H157`, `H158`, `H159` — genau die im Item reservierten |

### Die drei Zeilen, die die Merge-Runde von diesem Strom anfassen muss

1. **`tools/lead_package_sizes.json`** — drei Zeilen, je `+886 B` (dev 49 208→50 094, office
   54 779→55 665, research 52 213→53 099), geschrieben von
   `python tools/record_lead_package_sizes.py --write --note "…"`. Der Grund steht im Journal und
   lautet: der Absatz für FR-0084 (2) in den drei Verfassungen. Jeder andere Strom, der ein
   Lead-Paket wachsen lässt, schreibt in dieselbe Datei — beim Merge zusammenführen, nicht
   überschreiben.
2. **`docs/reviews/phase0-disposition.md`** — 16 neue Journalzeilen aus zwei Erzeugern (13 vom
   Pin-Skript in drei Läufen 6+4+3, 3 vom Größen-Skript); im Diff stehen 21 Zeilen mehr, weil vier
   Leerzeilen als Trenner dazukommen und eine ältere Größenzeile nur verschoben wurde. Reine
   Anhänge — abschnittsweise mergen.
3. **Der Verfassungsabsatz** „Before you build, your plan names the way it REJECTED." steht
   byte-gleich in allen drei Verfassungen. Schiedsrichter beim Merge ist
   `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`: ein fetter
   Lead-in in zwei Verfassungen verlangt den dritten und Byte-Gleichheit. Kommen die Sätze von G4-1
   und G4-2 in dieselben Abschnitte, entscheidet dieser Test über das Ergebnis — und die
   Abschnitts-Pins müssen danach einmal neu geschrieben werden.

---

## 9. Übergabe

* Der Patch liegt unter `_round-scratch/TSK-0123/stream-procedure.patch` und trägt **keine**
  `VERSION`-Hunks (`DEC-0070` (1)). **Gemessen:** 20 `diff --git`-Köpfe (19 geänderte Dateien + das
  neue Testmodul, angehängt über `git diff --no-index`, damit der Index des Arbeitsbaums unberührt
  bleibt); **127 110 B**, **0 CR-Bytes**. Auf einen unberührten HEAD-Baum angewandt
  (`git archive HEAD | tar -x`, dann `git -c core.autocrlf=false apply`): rc 0, und danach sind
  **1792 Dateien byte-gleich** mit dem Arbeitsbaum, **0** unterscheiden sich in den Zeilenenden, und
  verschieden sind **nur** die drei `VERSION`-Dateien.
  *Korrektur gegenüber Runde 1:* der dort vermutete CRLF-Unterschied war ein Artefakt meines
  Prüf-Rigs (`git apply` lief unterhalb eines Repos mit `core.autocrlf=true`) und kein Merkmal des
  Patches — die Prüfung Runde 1 hat das richtig gemessen, ich hatte es falsch beschrieben.
* Der Prüfer arbeitet in einer Kopie **ohne** die `.git`-Datei des Arbeitsbaums.
* Kein Commit, kein Push, keine Installation in den globalen Speicher — der Pilot lief gegen ein
  eigenes HOME unter `_round-scratch/TSK-0123/pilot/`.
* Alle Arbeitsdateien der Runde liegen ausschließlich unter `_round-scratch/TSK-0123/`.
