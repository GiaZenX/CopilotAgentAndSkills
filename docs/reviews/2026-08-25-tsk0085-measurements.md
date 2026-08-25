# TSK-0085 — Bestandsaufnahme: jedes aktive FR und BUG gegen das GEBAUTE gelesen

Auftrag: TSK-0085 (aus FR-0058, entschieden in DEC-0051). Rolle: `harness-implementer`.
Arbeitsverzeichnis ausserhalb des Repos: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0085\`.
Gemessen am 2026-08-25 gegen HEAD `f6dada2` plus den Arbeitsbaum dieser Runde.

Dieses Dokument ist die Messung. Was der LEAD daraus über den Kernel ausführen kann, steht in
Abschnitt 6; der Umsetzer schreibt `project_memory/` nicht.

---

## 1. Was gebaut wurde (Schritt 1) — die Ableitung

`kernel/report.py`:

| Funktion | Antwort |
|---|---|
| `closed_by_delivery(state)` | `{item id: [EVD id, …]}` — jedes Item, das eine Lieferung geschlossen hat |
| `delivered_but_open(state, active_items=None)` | dieselbe Antwort minus alles, was auch im Statusfeld geschlossen ist |
| `closing_route(item_type, status)` | `{"steps": […], "choices": […]}` — der Weg zum geschlossenen Status und was vor jedem Schritt steht |
| `delivery_closure_rollup(state)` | die Zeilen für einen Leser: `{item, type, status, evidence, route}` |

**Die Definition** (keine Liste von Nummern): ein Item ist geschlossen, wenn das AKTUELLE
Lieferurteil jeder Art, die es nennt, `pass` sagt — und mindestens eine Art es nennt. Welche
Dateien Lieferurteile sind und welches von mehreren gilt, kommt aus `_delivery_evidence` und
`_newest_per_kind`, also aus derselben Antwort, die `gate_git` über `qa_verdicts` liest. Ein nach
einem PASS erfasster FAIL öffnet das Item damit wieder.

**Wo es ein Leser trifft:** `python -m kernel.cli --root <state> validate` druckt die Zeilen NEBEN
den Findings, ohne Schweregrad und ohne Exit-Code, und `doctor` trägt sie unter
`delivery_closure`. Bewusst KEIN Finding: eine Zeile, die ein Projekt nicht räumen kann, ist als
Fehler eine Sperre, die nie aufgeht, und als Warnung ein Alarm, aus dem niemand herauskommt —
genau das ist hier gemessen der Fall (H39, Abschnitt 3). Das ist dieselbe Form, in der
`record_scan_coverage` seit 2026-08-07 neben den Findings steht.

**Nicht auf dem Hookpfad**: `validate_state` läuft in den dev-/research-Kits aus
`gate_memory_complete` bei jedem Bash-Aufruf. Die Ableitung hängt deshalb an den beiden Befehlen,
die ein Mensch tippt, nicht an `validate_state` — der Gate-Pfad zahlt keinen zusätzlichen Lauf
über das Evidence-Verzeichnis.

### Was die Ableitung beweist — und was nicht

Sie beweist, dass ein bestandenes Lieferurteil das Item GENANNT hat. Nicht, dass alles gebaut ist,
was das Item verlangt. Gemessen am eigenen Speicher: `EVD-0041` (pass) nennt `FR-0004`, während der
Commit, den es beurteilt (`b013423`), im eigenen Kopf „FR-0004 part 1" trägt. Für einen Wunsch,
den ein Projekt in Teilen liefert, liest die Ableitung also einen Teil zu früh als geschlossen.

In der Gegenrichtung ist sie am eigenen Speicher **zu leise**: bis `EVD-0035` (2026-08-15) nannten
die Urteile nur die TASK, nie den BUG. Deshalb weist sie 10 von 65 aktiven BUGs als geschlossen
aus, während das Lesen (Abschnitt 4) 48 gelieferte findet. Die Ableitung ist eine untere Schranke,
kein Ersatz für Abschnitt 4 — und `FR-0035` ist der Fall, der das beweist: seine Deckung kam aus
`FR-0049`, einer FREMDEN Nummer, die kein Namens- und kein Referenzabgleich verbindet.

**Ein Teil dieser Leise ist aber schon überbrückt, und zwar vom Kernel selbst.** Gemessen am
eigenen Speicher (Skript `reach.py`, beide Leser über denselben Zustand):

| Leser | erreicht |
|---|---|
| `closed_by_delivery` (nennt das Item wörtlich) | 12 Items — 10 BUG + FR-0004 + FR-0013 |
| `qa_verdicts` → `evidence_covers` → `_hangs_from` (der Weg, den `gate_git` geht) | dieselben 12 **plus 24 weitere BUGs** über den Referenzgraphen: BUG-0002, 0004, 0005, 0007, 0010, 0011, 0013, 0015, 0016, 0018, 0020, 0021, 0025, 0026, 0034, 0035, 0036, 0038, 0039, 0046, 0047, 0049, 0058, 0060 |

Genau die Klasse „das Urteil nannte nur die TASK" überbrückt der Graph-Weg also bereits — ein
Urteil an `TSK-0046` deckt `BUG-0004` über `derives_from`. **Der rohe Weg ist trotzdem nicht die
Ableitung**, und das ist gemessen: er meldet zusätzlich `PR-0001`, `PR-0003`, `SR-0001` und
`SR-0008` als grün, weil ein Task-Urteil auch zu der Wurzel hochläuft, unter der die Aufgabe
abgelegt ist. Für „darf dieser Merge laufen" ist das richtig, für „ist dieses Item fertig" falsch.
Beide Lesarten bleiben deshalb getrennt; was sie teilen (welche Dateien Urteile sind, welches
gilt) und was nicht (das Subjekt), steht im Docstring von `closed_by_delivery` und wird von
`test_report.test_a_task_verdict_does_not_close_the_item_the_task_hangs_from` von beiden Enden
gehalten.

**Ein archiviertes Urteil zählt nicht** (`_delivery_evidence` liest nur aktive Evidence): eine
Evidence zu archivieren ÖFFNET das Item wieder. Für ein abgelöstes Urteil ist das richtig — so
sieht Spec II.2 die Ablösung vor —, für eine Aufräum-Archivierung eines noch gültigen Urteils
überraschend. Das trifft direkt den Nachtrags-Weg in 6b und ist deshalb dort noch einmal genannt;
gehalten wird es von `test_report.test_archiving_a_verdict_reopens_the_item_it_had_closed`.

### Rot ohne den Fix (in einer Kopie ausserhalb des Repos)

Klon: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0085\mutant\`. Basislauf grün (7 Tests).

| Mutation | Rot |
|---|---|
| M0 `report.py`+`cli.py` auf `HEAD` zurückgesetzt (der Zustand vor dieser Runde) | alle 7 |
| M1 `results == {"pass"}` → `"pass" in results` („irgendein PASS gewinnt") | `test_a_later_fail_reopens_what_an_earlier_pass_had_closed` |
| M2 Automaten-Filter entfernt (Record-Typen zählen mit) | `test_a_verdict_that_judges_no_lifecycle_closes_nothing` |
| M3 Terminal-Übersprung in `delivered_but_open` entfernt | `test_an_item_already_in_a_terminal_status_is_not_reported_as_open` |
| M4 `choices` in `closing_route` auf `[]` festgenagelt | `test_the_closing_route_of_a_request_offers_the_terminals_it_may_become` |
| M5 `_guarded_edge`-Evidenzhalbe auf `None` | `test_the_closing_route_of_a_bug_names_both_guards_between_it_and_verified`, `test_the_delivery_rollup_is_printed_beside_the_findings_and_is_none_of_them` |
| M6 der Rollup ALS Warning-Finding in `validate_state` | `test_the_delivery_rollup_is_printed_beside_the_findings_and_is_none_of_them` |
| M7 `cli.py` druckt den Rollup nicht mehr | dasselbe (die Prozesshälfte) |
| M8 `closed_by_delivery` auf den Graph-Weg von `qa_verdicts` gelegt | `test_a_task_verdict_does_not_close_the_item_the_task_hangs_from`, `test_a_passing_delivery_closes_every_item_it_names` |
| M9 `_delivery_evidence` liest auch archivierte Urteile | `test_archiving_a_verdict_reopens_the_item_it_had_closed` |

---

## 2. Was die Ableitung am eigenen Speicher sagt

`python -B -m kernel.cli --root store validate` gegen eine Kopie von `project_memory/`:

```
Delivered but still open: 12 item(s) …
  BUG-0040 TRIAGED (EVD-0035): TRIAGED -> APPROVED (needs a 'scope' approval) -> FIXED -> VERIFIED (needs a passing 'test' Evidence)
  BUG-0041 TRIAGED (EVD-0037)   … dieselbe Route
  BUG-0042 TRIAGED (EVD-0038)
  BUG-0044 TRIAGED (EVD-0037)
  BUG-0051 TRIAGED (EVD-0036)
  BUG-0059 OPEN    (EVD-0056)   OPEN -> TRIAGED -> APPROVED (needs a 'scope' approval) -> FIXED -> VERIFIED (needs a passing 'test' Evidence)
  BUG-0063 OPEN    (EVD-0057)
  BUG-0064 OPEN    (EVD-0057)
  BUG-0065 OPEN    (EVD-0057)
  BUG-0066 OPEN    (EVD-0057)
  FR-0004  TRIAGED (EVD-0041):  TRIAGED -> one of CONVERTED, MERGED, REJECTED
  FR-0013  TRIAGED (EVD-0042):  TRIAGED -> one of CONVERTED, MERGED, REJECTED
```

`closed_by_delivery` nennt insgesamt 63 Items; die übrigen 51 sind TSK-Items, die längst im
Archiv liegen. `BUG-0017` steht korrekt NICHT darin: sein aktuelles `acceptance`-Urteil ist
`EVD-0020` = `fail`.

---

## 3. H39 ist breiter als DEC-0051 ihn beschreibt — gemessen

DEC-0051 nennt einen Grund, warum ein reparierter BUG hier keinen ehrlichen Endzustand hat: die
Kante `TRIAGED -> APPROVED` verlangt eine gemintete Freigabe, und diese Werkstatt fährt kein Kit.
Gemessen (`test_the_closing_route_of_a_bug_names_both_guards_between_it_and_verified`, gegen den
laufenden Kernel, nicht gegen den Routentext) stehen **zwei** Wächter auf dem Weg:

1. `TRIAGED -> APPROVED` — braucht eine `scope`-Freigabe (`approvals.APPROVAL_TRANSITIONS`);
   `state.transition` verweigert die Kante ohne sie.
2. `FIXED -> VERIFIED` — braucht ein `test`-Urteil mit `pass`, das den BUG deckt
   (`state.CONFIRMING_EVIDENCE = {"BUG": "test"}`, `state._assert_confirmed`).

Der zweite ist in diesem Speicher **auch dann nicht erfüllt, wenn der Mint da wäre**: alle 57
Evidence-Datensätze sind `review` (53), `acceptance` (3) und `audit` (1) — kein einziges
`test`-Urteil. `EVD-0057` etwa, das BUG-0063…0066 nennt, ist `kind: review`. Ein reparierter BUG
bräuchte hier also zusätzlich eine `test`-Evidence je BUG.

Folge für Schritt 3: die BUG-Hälfte der Buchführungsschuld ist mit den heutigen Mitteln **nicht**
über den Automaten schliessbar. Die Ableitung ist die Wahrheit über den Stand; das Statusfeld ist
es nicht.

---

## 4. Die BUG-Bilanz — 65 aktive Items, jedes gegen das Gebaute gelesen

Beweisarten: **A** = die Ableitung aus Abschnitt 1 (EVD nennt den BUG direkt), **T** = die aus dem
BUG geschnittene TSK ist mit bestandenem Urteil geliefert, **C** = Commit, **K** = Stelle im
laufenden Code / im Test, die den Fix trägt, **L** = Live-Lauf.

### 4a. Geliefert (48)

| Item | Status | Beweis |
|---|---|---|
| BUG-0001 | TRIAGED | T TSK-0045 · C `02247e4` · K `kernel/cli.py` `update`-Subkommando |
| BUG-0002 | TRIAGED | T TSK-0049/EVD-0015 · C `2f7ca98` · K `office-team/hooks/_filing.py`, `guard_fs_tripwire.py` |
| BUG-0003 | TRIAGED | T TSK-0050 · C `2f7ca98` · K `office-team/hooks/_filing.py` (aufgelöste Zeichenkette) |
| BUG-0004 | TRIAGED | T TSK-0046/EVD-0013 · C `c6f9782` · K `report._check_premise_recheck` |
| BUG-0005 | TRIAGED | T TSK-0051/EVD-0016 · C `c784e9d` · K `report._brief_decision_rows` |
| BUG-0006 | TRIAGED | T TSK-0035 · C `06da6f1` · K `tools/test_hooks_v2.py` (transitive Ordering-Ableitung) |
| BUG-0007 | TRIAGED | T TSK-0038/EVD-0009 · C `86b144f` · K `ruff.toml` `select`, `tools/test_ci_lint_pinned.py` |
| BUG-0008 | TRIAGED | T TSK-0037 · C `c188d5f` · K `.gitignore` `Microsoft/` + `tools/test_repo_hygiene.py` |
| BUG-0009 | TRIAGED | T TSK-0047 · C `c6f9782` · K `report._check_fr_result_link`, `_check_dec_supersedes` |
| BUG-0010 | TRIAGED | T TSK-0048/EVD-0014 · C `230b817` · K `dispatch.assert_lease_backed_transition_locked` |
| BUG-0011 | TRIAGED | T TSK-0052/EVD-0017 · C `426d7cd` · K `tools/test_handover_marker.py`, `session_status.py` |
| BUG-0012 | TRIAGED | T TSK-0009/EVD-0029 · C `eeb9779` · K `.claude/hooks/test_gates.py:1654` mit drei Gegenenden |
| BUG-0013 | TRIAGED | T TSK-0034/EVD-0007 · C `06da6f1` · K `_stdlib_guard.py` in allen drei Kits |
| BUG-0015 | TRIAGED | T TSK-0033/EVD-0030 + TSK-0060/EVD-0032 · C `7de1537`, `3598444` · K `backlog_types.field_elements` |
| BUG-0016 | TRIAGED | T TSK-0053/0054, EVD-0023 (Live) · C `29bc987`, `e4b0aaa`, `8ffadf0` · K `user/claude/hooks/handover_guard.py` |
| BUG-0018 | TRIAGED | T TSK-0028/EVD-0004 · C `24792f0` · K `cli._pin_utf8` |
| BUG-0020 | TRIAGED | T TSK-0043/EVD-0011 · C `2dde226` · K `gate_write_scope.py` (alle drei Kits) |
| BUG-0021 | TRIAGED | T TSK-0044/EVD-0012 · C `02247e4` · K `kernel/cli.py` (BOM auf stdin) |
| BUG-0025 | OPEN | T TSK-0036/EVD-0008 · C `c188d5f` · K `.gitattributes`, `tools/test_context_budget.py` |
| BUG-0026 | OPEN | T TSK-0039/EVD-0010 · C `569fb34` · K `migrate.record_deposit_of` |
| BUG-0027 | OPEN | T TSK-0040 · C `569fb34` · K `kernel/migrate.py` (READY-Zeile mit Flags) |
| BUG-0028 | OPEN | T TSK-0041 · C `569fb34` · K `report.record_scan_coverage` `deposits` |
| BUG-0029 | OPEN | T TSK-0042 · C `569fb34` · K `kernel/report.py` (doctor-Kit-Antwort) |
| BUG-0030 | OPEN | K gemessen 2026-08-25: kein Byte `0x08` in einer der **89** Dateien `team-kits/**/hooks/*.py` (AC-1 über alle drei Kits erfüllt) |
| BUG-0034 | TRIAGED | T TSK-0056/EVD-0025 · C `e92511d` · K `.claude/hooks/test_gates.py` (Eigenschaft statt Wort) |
| BUG-0035 | TRIAGED | T TSK-0058/EVD-0028 · C `7b94766` · K `.claude/hooks/test_gates.py` (abgeleiteter Stolperdraht) |
| BUG-0036 | TRIAGED | T TSK-0057/EVD-0027 · C `6c8e05f` · K `kernel/report.py` (zustandsgenaue hook_trust-Begründung) |
| BUG-0038 | TRIAGED | T TSK-0059/EVD-0031 · C `179c5c8` · K `backlog_types.REFERENCE_LIST_FIELDS` + `report._check_reference_list_shape` |
| BUG-0039 | TRIAGED | T TSK-0061/EVD-0034 · C `2ada1ac` · K `gate_approval.py` (alle drei Kits), `kernel/approvals.py` |
| BUG-0040 | TRIAGED | **A** EVD-0035 · T TSK-0062 · C `c7d8d74` |
| BUG-0041 | TRIAGED | **A** EVD-0037 · T TSK-0064 · C `64fd704` · K `kernel/presets.py` |
| BUG-0042 | TRIAGED | **A** EVD-0038 · T TSK-0065 · C `4eedcb9` · K `kernel/checkpoints.py` |
| BUG-0043 | TRIAGED | T TSK-0076/EVD-0048 · C `1263f36` · K `user/claude/CLAUDE.md` (Sign-off als Antwort) |
| BUG-0044 | TRIAGED | **A** EVD-0037 · C `64fd704`, `1263f36` · K Preset-Frage im Einstiegsinterview (`user/claude/CLAUDE.md:74-88`). **Sein AC-1 verlangt einen Test, der ohne den Fix rot wird, und den gibt es nicht**: die Preset-Frage ist Prosa in der Einstiegsdatei, und der einzige Preset-Fragen-Test misst die Kit-Verfassungen, nicht sie. Das Urteil „geliefert" steht auf A + C + K, das AC bleibt unerfüllt |
| BUG-0045 | TRIAGED | T TSK-0076/EVD-0048 · C `1263f36` · K `user/claude/CLAUDE.md` (Uhr lesen statt erfinden) |
| BUG-0046 | TRIAGED | T TSK-0074/EVD-0046 · C `19d93f2` · K `guard_agent_spawn.py` (alle drei Kits) |
| BUG-0047 | TRIAGED | T TSK-0072/EVD-0045 · C `bc6e198` · K `gate_write_scope.py` (Rollengedächtnis-Tür) |
| BUG-0048 | TRIAGED | T TSK-0073 · C `bc6e198` · K `tools/test_role_contracts.py`, `kernel/dispatch.py`, `kernel/cli.py` |
| BUG-0049 | TRIAGED | T TSK-0075/EVD-0047 · C `b01cd76` · K `gate_subagent_output.py` (alle drei Kits) |
| BUG-0050 | TRIAGED | T TSK-0075/EVD-0047 · C `b01cd76` · K `guard_question_context.py` (alle drei Kits) |
| BUG-0051 | TRIAGED | **A** EVD-0036 · T TSK-0063 · C `54c0807` |
| BUG-0059 | OPEN | **A** EVD-0056 · T TSK-0081/EVD-0054 · C `6705a8e` · **L** Lauf 2 am 2026-08-23 (Hebung ohne Nutzer-Shell) |
| BUG-0061 | OPEN | T TSK-0082/EVD-0055 · C `297a649` · **L** Lauf 3 am 2026-08-23 (10 Regeln, null Nachforderungen) |
| BUG-0062 | OPEN | T TSK-0082/EVD-0055 · C `297a649` · K `tools/provider_observations.json` `hook_deadlines` + Eigenschaftstest |
| BUG-0063 | OPEN | **A** EVD-0057 · T TSK-0083 · C `f6dada2` |
| BUG-0064 | OPEN | **A** EVD-0057 · C `f6dada2` · K `office-team/hooks/gate_ledger_valid.py` |
| BUG-0065 | OPEN | **A** EVD-0057 · C `f6dada2` · K `office-team/hooks/gate_ledger_valid.py` |
| BUG-0066 | OPEN | **A** EVD-0057 · T TSK-0084 · C `f6dada2` · K `_compat.py`/`gate_write_scope.py` (alle drei Kits) |

Zwei Einschränkungen, die für Zeilen dieser Tabelle gelten und die ein Leser kennen muss:
BUG-0016, 0043, 0044 und 0045 werden von Dateien unter `user/` getragen, die der Installer ins
Heimatverzeichnis legt — im Repo ist der Fix da, ob die Kopie des Nutzers ihn trägt, ist von hier
aus nicht messbar (FR-0048 Hälfte 2). Und BUG-0030 hat neben der erfüllten AC-1 keinen
Stolperdraht: `ruff.toml` wählt `E4,E7,E9,F`, `PLE2510` ist nicht darin — ein neues Steuerzeichen
fiele wieder nur einem Prüfer auf.

### 4b. Teilweise geliefert (5)

| Item | Was steht | Was fehlt — gemessen |
|---|---|---|
| BUG-0017 | (a) erfundene `/hooks`-Zeremonie und (b) die wortgleiche Relais-Ablehnung sind gebaut (C `29bc987`, `e4b0aaa`, `2ada1ac`; K `gate_approval.py`) | (c) der Mint im Headless-/SDK-Betrieb ist von MIR nicht nachgemessen. Das jüngste `acceptance`-Urteil auf BUG-0017 ist `EVD-0020` = **fail**, erfasst 2026-08-12T21:47:11 — also NACH `29bc987` (19:20) und VOR `e4b0aaa` (22:55) und `2ada1ac` (2026-08-15): zwei der drei Fixes sind jünger als das Urteil, einer älter. Am Schluss ändert das nichts (das Urteil kann die beiden jüngeren nicht beurteilt haben), an der Begründung schon. Was es entscheidet: eine neue `acceptance`-Evidence aus einem echten Lauf |
| BUG-0033 | der Test ist umgebaut: die Registrierung wird aus den Kosten DIESES Hosts abgeleitet (`test_gates.py:4386-4398`), und ein Host, der die Eigenschaft nicht zeigen kann, scheitert mit dem Grund statt unlesbar rot zu werden (`:4511-4515`) | ob die Rot-unter-Last-Klasse damit weg ist, entscheidet nur ein voller Leerlauf-Lauf der Gate-Suite (~68 min). Nicht gefahren: diese Runde fasst `.claude/` nicht an |
| BUG-0058 | Mechanismus gebaut und am Hook gemessen (C `7b42e1b`, T TSK-0080/EVD-0053; frische Lease rc 0, abgelaufenes Bindefenster ohne Kind rc 2, zweiter Befund rc 0) | AC-2: ob der Provider `exit 2` auf dem `Stop`-Ereignis honoriert — im Live-Lauf trat der Fall nicht ein (Bericht 2026-08-23, „Offen nach diesem Lauf" 1) |
| BUG-0060 | der Briefing-Satz existiert und ist in beiden Richtungen am Hook gemessen (C `297a649`, K `report.accepted_without_a_verdict` + `_kernel.unverified_delivery_briefing`) | ob der Satz den PM bewegt — ungemessen; der Lauf kam nicht bis Phase 5 |
| BUG-0067 | die Commit-Gefahr ist zu: die acht Formulare stehen in `.gitignore` und `tools/test_repo_hygiene.py` hält „getrackt ∩ ignoriert = leer"; gemessen `git status --porcelain --ignored` → `!!` | AC-1 (der Seeding-Pfad darf nicht auf die Repo-Wurzel zeigen) und AC-2 (die acht Dateien liegen noch im Arbeitsbaum — gemessen heute) sind offen |

### 4c. Wirklich offen (12 Zeilen: 11 offen + 1 nicht entscheidbar)

| Item | Messung von heute |
|---|---|
| BUG-0014 | **nicht entscheidbar ohne einen Lauf.** Der genannte Test lebt weiter (`test_gates.py:3119`) und hat weiter eine Kontrolle. Was es entscheidet: ein Leerlauf-Vollauf der Gate-Suite |
| BUG-0022 | kein Mechanismus, der einen CR erzwingt; `CR` kommt im dev-PM-Skill 5× vor wie vorher |
| BUG-0023 | `backlog_types.NONEMPTY_FIELDS = {"EVD": (…)}` — `TSK.expected_outputs` ist NICHT darin, eine leere Liste wird weiter angenommen |
| BUG-0031 | `user/codex/AGENTS.md:24-25` entscheidet die Übergabe weiter an „contains the marker" — unverändert |
| BUG-0032 | `report.validate_state` entscheidet „orphaned staging dir" weiter über `entry not in active_items` (reiner Namensabgleich) |
| BUG-0037 | **heute nachgemessen, indem `transition()` AUSGEFÜHRT wurde**: `transition({'state':'hooks_trust_required','hook_bundle_hash':'AAA'}, 'AAA')` → `('active', None)`. Der Kopfkommentar bei `kit_trust_state.py:23-24` sagt weiter „nothing here leads OUT of `hooks_trust_required`". Kommentar behauptet Schutz, den der Code nicht baut |
| BUG-0052 | `project_memory/.audit/hook_events.jsonl` ist weiter getrackt (`git ls-files`) und die `.gitignore`-Regel ist für diese Datei ausdrücklich ein No-op. Der Suite-Lauf dieser Runde hat die Datei erneut wachsen lassen (Abschnitt 7) |
| BUG-0053 | `gate_shell_hygiene._flag_name` (`:166-167`) trennt weiter nur an `=`; die angehängte Kurzform `-pother` bleibt unerkannt |
| BUG-0054 | kein einziges Vorkommen von `architecture_refs` in `kernel/staging.py` — der Erzeuger fehlt weiter |
| BUG-0055 | `approvals._SCOPE_FIELDS` (`:179-181`) trägt weiter kein Wireframe-Feld; die DEC steht aus |
| BUG-0056 | unverändert (keine Codestelle nennt den Befund; die V1-Kenntnis der Migration liest kein Gate) |
| BUG-0057 | `report._settings_layers` liest weiter ausschliesslich die drei `.claude`-Schichten |

Das sind **BUG-0014, 0022, 0023, 0031, 0032, 0037, 0052, 0053, 0054, 0055, 0056, 0057** — zwölf
Zeilen, davon elf gemessen offen und eine (BUG-0014) nicht entscheidbar.

### 4d. Zählung

| | Anzahl |
|---|---|
| aktive BUG-Items | 65 |
| geliefert | 48 |
| teilweise geliefert | 5 |
| wirklich offen | 11 |
| nicht entscheidbar | 1 (BUG-0014) |

48 + 5 + 11 + 1 = 65.

FR-0058 schätzte „rund 26 von 66" als überzeichnet. Gemessen sind es **48 von 65** — die
Überzeichnung ist fast doppelt so gross wie die Schätzung.

---

## 5. Die FR-Bilanz — 46 aktive Items

| Item | Urteil | Beweis / was fehlt |
|---|---|---|
| FR-0002 | teilweise | F1 (leere Regelliste blockiert die erste Ablage) ist praktisch zu: das Onboarding erzeugt die Regeln (BUG-0061, TSK-0082, Live-Lauf 3: 10 Regeln, null Nachforderungen). Die Vorlage liefert weiter `rules: []` aus (Absicht). F2–F8: kein Commit nennt sie, diese Runde nicht nachgemessen |
| FR-0003 | offen — und **Dublette** | inhaltlich vollständig in FR-0036 aufgegangen („folds FR-0003 in", dessen eigener Text) |
| FR-0004 | teilweise | Teil 1 geliefert (TSK-0069, EVD-0041, C `b013423`, `docs/reviews/2026-08-16-tsk0069-ii12-side-check.md`); Teil 2 (seitliche RC-Installation) offen und von FR-0041 abhängig |
| FR-0005 | offen | keine Zuschnitt-Kritiker-Rolle in `.claude/agents/` oder in einem Kit |
| FR-0007 | offen | gemessen: `SR-0008`/„Kommentardisziplin" kommt in KEINER Datei unter `team-kits/` vor; die drei Verfassungen zählen 0 Treffer. `eeb9779` hat die Regel in `.claude/agents/` und `CLAUDE.md` dieses Repos gelegt, nicht in die Kits |
| FR-0010 | offen | gemessen: kein Treffer für „Fehlform"/„five forms"/„order-line" unter `team-kits/` |
| FR-0011 | teilweise | die Nebenläufigkeit existiert (`test_gates.AT_ONCE = 10`); das Ziel (Wandzeit runter) ist nach der letzten Messung im Item selbst nicht erreicht (4101,94 s). Diese Runde nicht nachgemessen |
| FR-0012 | offen | kein Fänger für Entscheidungen in Prosa |
| FR-0013 | **geliefert — auf der eigenen Option (c) des Items, mit benanntem Rest** | TSK-0070, EVD-0042, C `bccaf81`. Gemessen von mir am 2026-08-25 als echte Hook-Prozesse gegen das ausgelieferte Kit (31 Fälle, alle grün): **refused rc 2** sind 19 Umleitungs-Schreibweisen samt `echo pwned > services/pay.py`, `>>`, `>|`, `&>`, `>&`, Heredoc, quotiertem Ziel, `cd services && echo … > pay.py`, `~/`, `~+/` und einer in derselben Zeile zugewiesenen Variablen; **rc 0 und als Rest BENANNT** sind acht POSIX-Formen — darunter wörtlich `python -c "open('services/pay.py','w').write('pwned')"`, `sed -i`, `tee`, `cp`, `mv`, `rm -f`, `> $(…)`, `> $F` (unzugewiesen) — plus vier PowerShell-Cmdlets. **Beide Schreibweisen, die der `request_text` nennt, sind damit in der Antwort: die erste gesperrt, die zweite der Rest.** Das ist keine offene Lücke, sondern die vom Item selbst angebotene Option (c) („vielleicht ist die 95%-Grenze mit einem ehrlichen Löcherlisten-Eintrag im Kit die günstigere Antwort"), und der Rest ist von beiden Enden verdrahtet (`tools/test_hooks.py:12087`). Der Unterschied zu FR-0035 ist in den Items selbst messbar: FR-0035 verlangt „enforced not advised" und nennt keinen zulässigen Rest. **Achtung: `triage_result` des Items ist veraltet**; der Ersatztext steht wörtlich in 6a |
| FR-0014 | teilweise | der erste Office-Pilot ist gefahren (Pilot 4 Hälfte 3, `docs/pilot/2026-08-22-pilot-4-befunde.md:123` „die Kernbehauptung des Nutzers hält"; dazu Live-Lauf 3). Die einzelnen Abnahmekriterien des FR habe ich NICHT gegen den Pilotbericht abgeglichen |
| FR-0015 | offen | keine API-Produktpflege im Office-Kit |
| FR-0016 | offen | Provider-Fähigkeit unverändert |
| FR-0017 | offen | kein Gliederungsknoten-Typ in `backlog_types.py` |
| FR-0018 | offen | `capture` erkennt weiter nur Id-Dubletten |
| FR-0019 | offen | kein Übergabeweg für Nutzerdateien |
| FR-0020 | offen | vom Nutzer geparkt |
| FR-0021 / FR-0022 / FR-0023 / FR-0024 / FR-0025 | offen | post-release; nichts gebaut |
| FR-0028 / FR-0029 | offen | Office-Werkzeugagnostik, Research-Pilot: nichts gebaut |
| FR-0031 | offen | Aktenplan-Standardentwurf + gerenderter Baum: die Vorlage liefert weiter `rules: []`, keine Baumansicht im Kit |
| FR-0032 | offen | kein Finanz-Dashboard im Office-Kit; `scripts/` liefert `euer_report.py` und `ledger_add.py`, keinen Renderer für eine Übersicht |
| FR-0033 | offen | die zehn Office-Agenten enthalten keine Korrespondenzrolle, und kein PROC-Vorlagenweg für Briefe ist ausgeliefert |
| FR-0034 | offen | kein Fristenregister im Zustand, kein Fälligkeits-Satz im Sitzungsbrief |
| FR-0035 | **teilweise — und das ist der Fall aus FR-0058** | Gebaut ist die Vier-Augen-Schleife als ROLLENWEG: `office-team/agents/filing-reviewer.md`, `skills/filing-reviewer/SKILL.md`, `kernel/schemas/filing_proposal.yaml` + `filing_verdict.yaml`, Verfassung `:102` (TSK-0078, C `5ee0f26`, FR-0049). **Nicht gebaut ist der Hook, den FR-0035 wörtlich verlangt**: gemessen liest KEIN Office-Hook `filing_verdicts.yaml` (grep über `team-kits/office-team/hooks/*.py`: null Treffer für `filing_verdict`/`filing_proposal`/`filing-reviewer`), und `gate_filing` prüft ausschliesslich Ziel gegen Regel. Das Kit sagt es selbst: `office-team/hooks/ENFORCEMENT.md:32` — „the review pipeline in front of it is procedure and not a mechanism … a proposal nobody reviewed reaches this gate exactly like any other move". Ein Zug ohne zweite Lesung wird also nicht gesperrt |
| FR-0036 | offen | Wunsch-Prosa-Abgleich; nimmt FR-0003 auf |
| FR-0037 | offen | gemessen: die Zeichenkette `240` kommt in `kernel/report.py` nicht vor |
| FR-0038 | offen | N4: kein Erzeuger für `last_completed`/`next_due`, kein Fälligkeitsmelder beim Sitzungsstart |
| FR-0039 | offen | N6: `INV.verified` hat weiter keinen Schreiber; `gate_test_coverage` liest INV nach `scope`, nie nach Status |
| FR-0040 | offen | N7: `REQUIRED_FIELDS["EVD"]` nennt weder Befehl noch Umfang eines Laufs — ein `-k`-Lauf ist von einem Vollauf nicht unterscheidbar |
| FR-0041 | offen | N8: die Kommandofläche hat weder `pin` noch `rollback` |
| FR-0042 | offen | N9: `tools/test_e2e.py` fährt die dev-Kette; keine RQ→HYP→EXP→Report-Kette in der Suite |
| FR-0043 | offen | N10: der **ausgelieferte** CI-Workflow (dev- und research-Vorlage) hat einen einzigen Job `quality` mit **sieben** Schritten; kein Treffer für `bench`/`p95`/`latency`. Korrigiert nach der Prüfung: die erste Fassung dieser Zeile nannte `check` mit vier Schritten — das ist der Workflow **dieses Repos**, den kein Kit ausliefert, also das falsche Artefakt gemessen und „gemessen" genannt. `FR-0043.request_text` trug die richtige Zahl bereits. Am Urteil ändert sich nichts: in beiden Workflows 0 Treffer |
| FR-0044 | offen | N13: `greenfield` kommt in `scaffold_team.sh`, `scaffold_team.ps1`, `init_project_memory.sh` und in keiner Datei unter `team-kits/kernel/` vor (je 0 Treffer). Es kommt anderswo vor — `dev-team/hooks/_kernel.py`, die dev-Vorlage `project_config.yaml`, `generate_dashboard.py` —, nur nicht an der Stelle, die der Wunsch meint |
| FR-0045 | offen | 2026-08-23 mit echtem Export gemessen; das Schema ist nicht gebaut |
| FR-0046 | offen | Feldtest an echten Altkopien: Lauf 2 am 2026-08-23 hat EINEN Altbestand gehoben (`git archive 3598444`), die drei echten Projektkopien sind nicht gefahren |
| FR-0047 | offen | recherchiert (Triage trägt das Ergebnis); nichts gebaut |
| FR-0048 | teilweise | Hälfte 1 geliefert (TSK-0076, EVD-0048, C `1263f36`); Hälfte 2 (Rollout ins Heimatverzeichnis) wartet auf den NUTZER — DEC-0045 nennt das eine externe Freigabe |
| FR-0052 | teilweise | Harness-Seite steht (`CLAUDE.md`); Kit-Seite offen: die drei PM-/Manager-Skills nennen `decisions/active/` nur im Zusammenhang mit bewussten Auslassungen, nicht als Nachschlagepflicht vor einer SOLL-Antwort |
| FR-0054 | offen | gemessen: `related_sr` kommt in keiner Datei unter `team-kits/kernel/` vor |
| FR-0055 | offen | gemessen: `user/claude/settings.json` führt `remoteControlAtStartup` ausdrücklich unter „Deliberately NOT shipped" |
| FR-0057 | offen | gemessen: die `description` von `dev-team/agents/quality-engineer.md` sagt weiter „run the tests" ohne Umfang |
| FR-0058 | teilweise | diese Runde: Ableitung gebaut (Abschnitt 1), Bestandsaufnahme gemacht (Abschnitte 4/5). Offen bleibt die HÄLFTE (a) — die Zustandsänderungen selbst, die nur der Lead schreiben darf |

Zählung über die 46 aktiven FR: **1 geliefert** (FR-0013), **8 teilweise** (FR-0002, 0004, 0011,
0014, 0035, 0048, 0052, 0058), **37 offen**.

---

## 6. Was der LEAD über den Kernel ausführen kann (Schritt 3)

### 6a. FR — der Automat lässt es zu, mit zwei Pflichten je Ziel

`FR` läuft `OPEN -> TRIAGED -> {MERGED | CONVERTED | REJECTED}`; ein Terminal ist nur aus
`TRIAGED` erreichbar. `TRIAGED` schuldet `triage_result`, `MERGED` und `CONVERTED` schulden
`resulting_item`, und das genannte Item muss existieren (`report._check_fr_result_link`). Beide
Felder gehen über `update`, der Status über `transition`.

**Eine Frage, die ich NICHT entscheide, weil sie dem Nutzer gehört:** FR-0058 plant „gelieferte
Wünsche auf MERGED". Die einzige geschriebene Definition der beiden Ausgänge in diesem Speicher
steht in FR-0003 selbst — „CONVERTED (wurde eine Anforderung) / MERGED (Dublette)". Nach dieser
Lesart ist für einen GELIEFERTEN Wunsch `CONVERTED` der richtige Ausgang und `MERGED` der für eine
Dublette. Der Kernel unterscheidet die beiden nicht; beide verlangen dasselbe Feld. Vorschlag
unten entsprechend, aber das ist eine Nutzerentscheidung, keine Messung.

| FR | Ziel | `resulting_item` | Grund |
|---|---|---|---|
| FR-0013 | CONVERTED | TSK-0070 | geliefert auf Option (c) des Items, Rest benannt und verdrahtet |
| FR-0003 | MERGED | FR-0036 | echte Dublette (FR-0036 nimmt es auf) |

**FR-0013 wird nur zusammen mit diesem Ersatztext geschlossen — der Rest darf beim Schliessen
nicht verlorengehen.** `CONVERTED` schuldet nur `resulting_item`; was das Item an gemessenem Rest
trägt, trägt danach allein `triage_result`. Zwei Kernel-Aufrufe, in dieser Reihenfolge:

```
update FR-0013   (JSON-Body auf stdin)
{"triage_result": "<Text unten, woertlich>", "resulting_item": "TSK-0070"}
transition FR-0013 CONVERTED
```

`triage_result`, wörtlich:

> delivered by TSK-0070 (EVD-0042, commit bccaf81) on this item's OWN option (c) -- bind what a
> command line can decide, name and tripwire the rest, rather than copy the shell apparatus into
> the kits. What was built: the shell half lives in `gate_write_scope.handle_shell`, the file
> property in `guard_pm_scope.production_code()` -- one answer, two doors. `guard_pm_scope` itself
> stays registered on `Edit|Write|MultiEdit|NotebookEdit` alone; that is the split, not the gap.
> MEASURED 2026-08-25 as real hook processes against the shipped kit, 31 cases: refused rc 2 are
> the redirect spellings including `echo pwned > services/pay.py`, `>>`, `>|`, `&>`, `>&`, a
> heredoc, a quoted target, `cd services && echo … > pay.py`, `~/…`, `~+/…` and a variable
> assigned on the same line. NAMED RESIDUE, rc 0: a write a tool performs from INSIDE its own
> language or arguments -- `python -c "open('services/pay.py','w').write('pwned')"` (the second
> spelling this request_text names), `sed -i`, `tee`, `cp`, `mv`, `rm -f` -- plus a redirect target
> built by an expansion the gate cannot resolve (`> $(…)`, an unassigned `$F`), plus the
> PowerShell `Out-File`/`Set-Content`/`Add-Content`/`Tee-Object` cmdlets. Refusing those needs the
> verb list `L4` calls the wrong shape of check, which is why option (c) was taken and not (a)/(b).
> The residue is held from BOTH ends -- it reddens if a later round closes one of them -- by
> `tools/test_hooks.py::test_the_shell_writes_no_command_line_can_decide_stay_the_named_residue`
> and `::test_a_powershell_cmdlet_write_is_the_named_residue_too`, and it is stated in each kit's
> `hooks/ENFORCEMENT.md`. (This field previously read "still registers guard_pm_scope only on
> Edit|Write|MultiEdit|NotebookEdit" and described the gap as if it still stood.)

Warum das nicht dieselbe Lage wie FR-0035 ist, obwohl beide einen Rest tragen: der Unterschied
steht in den beiden Items selbst. FR-0035 verlangt „ON TOP, **enforced not advised**" und lässt
keinen Rest zu — dort fehlt der verlangte Mechanismus ganz. FR-0013 stellt die Frage
ausdrücklich als Nutzen-gegen-Wartungslast und bietet (c) als zulässige Antwort an. Wer beide
gleich behandelt, ignoriert genau die Stelle, an der die Items sich unterscheiden.

Für die acht teilweise gelieferten (FR-0002, 0004, 0011, 0014, 0035, 0048, 0052, 0058)
empfehle ich **keinen** Statuswechsel: ein halb geliefertes Item auf ein
Terminal zu setzen verliert genau die Resthälfte. Was sie brauchen, ist ein aktualisierter
`triage_result`.

### 6b. BUG — nichts davon ist heute schliessbar

Für alle 48 gelieferten BUGs gilt Abschnitt 3: `REJECTED` und `DUPLICATE` wären eine Lüge,
`VERIFIED` verlangt zwei Wächter, die diese Werkstatt nicht bedienen kann. Was der Lead tun kann,
ohne zu lügen:

1. `python -B -m kernel.cli --root project_memory validate` gibt die Ableitung ab sofort neben den
   Findings aus; dieselben Zeilen stehen in `doctor` unter `delivery_closure`.
2. **Nachtrags-Evidence — für 16 BUGs, nicht für 38.** Die Zahl ist nachgerechnet, nachdem der
   Prüfer nachgewiesen hat, dass der Kernel einen Teil der Lücke selbst überbrückt (Abschnitt 1).
   Aufteilung der 48 gelieferten:

   | | Anzahl | wer erreicht sie |
   |---|---|---|
   | ein EVD nennt den BUG wörtlich | 10 | `closed_by_delivery` **und** `qa_verdicts` |
   | kein EVD nennt ihn, aber ein Urteil an der aus ihm geschnittenen TSK deckt ihn über `derives_from` | 22 | nur `qa_verdicts` (der Weg, den `gate_git` geht) |
   | kein Leser erreicht sie | **16** | keiner |

   Die 16: BUG-0001, 0003, 0006, 0008, 0009, 0012, 0027, 0028, 0029, 0030, 0043, 0045, 0048,
   0050, 0061, 0062. **Nur für diese trägt eine neue Evidence eine Tatsache nach**; für die 22
   steht die Tatsache schon im Speicher und ist über `qa_verdicts` abrufbar — eine Zeile dafür
   würde nur den Rollup lauter machen und wäre 22-mal Arbeit für null neue Information.

   Die Form ist die, die `EVD-0057` schon hat: ein Kernel-Schreibvorgang (`kernel.cli evidence`),
   kein Statuswechsel, und er erfindet nichts — er trägt nach, was der Commit ohnehin sagt:
   `evidence --kind review --result pass --related BUG-0001 --related BUG-0003 … --summary "…"
   --artifact-ref docs/reviews/2026-08-25-tsk0085-measurements.md`

   **Zwei Dinge, die der Lead dabei wissen muss.** Erstens: die Nachtrags-Evidence ist über die
   Ablage wieder rückgängig — `_delivery_evidence` liest nur AKTIVE Evidence, ein Archivieren
   öffnet das Item also wieder (Abschnitt 1, gehalten von
   `test_report.test_archiving_a_verdict_reopens_the_item_it_had_closed`). Zweitens: eine
   `review`-Evidence bringt den BUG in die Ableitung, aber **nicht** näher an `VERIFIED` — dafür
   verlangt der Kernel ein `test`-Urteil (Abschnitt 3).
3. Der Rest gehört in DEC-0051 Stufe 2 (Freigabe-Weg nachrüsten) — dann, und erst dann, ist
   `VERIFIED` ohne Lüge erreichbar, sofern zusätzlich je BUG ein `test`-Urteil existiert
   (Abschnitt 3).

### 6c. Was ich NICHT entscheiden konnte

| Fall | Was es entscheiden würde |
|---|---|
| BUG-0014 (Gate-Suite rot?) | ein Leerlauf-Vollauf `python -B -m pytest .claude/hooks/test_gates.py -q` (~68 min) |
| BUG-0033 (Rot unter Last) | derselbe Lauf, einmal solo und einmal unter paralleler Last |
| BUG-0017 (c) (Mint headless) | eine neue `acceptance`-Evidence aus einem echten Lauf; das letzte Urteil ist ein `fail` von vor den Fixes |
| BUG-0058 AC-2 / BUG-0060 Wirkung | ein Live-Lauf, der den Fall überhaupt erreicht (steht so im Bericht vom 2026-08-23) |
| FR-0002 F2–F8 | ein Abgleich von `docs/office-kit-from-field.md` gegen das Office-Kit, Punkt für Punkt |
| FR-0011 (Wandzeit) | eine frische Zeitmessung der Gate-Suite |
| FR-0014 (Abnahmekriterien) | ein Abgleich der FR-Kriterien gegen `docs/pilot/2026-08-22-pilot-4-befunde.md` Hälfte 3 |
| MERGED vs. CONVERTED | eine Nutzerentscheidung (6a) |

**Wo ich im Zweifel welchen Fehler riskiert habe:** ein falsches „geliefert" kostet den Nutzer
echte Arbeit, ein falsches „offen" nur Zeit. Deshalb steht in 4a **47 der 48 Zeilen** auf zwei
unabhängigen Belegen (Commit UND Code/Test oder Evidence), und wo nur einer davon vorlag, steht
das Item in 4b oder 4c.

**Die eine Ausnahme ist BUG-0030, und sie steht bewusst so.** Diese Zeile trägt nur einen Beleg
(K), weil es keinen zweiten gibt: kein Commit nennt den Fehler, keine Aufgabe wurde aus ihm
geschnitten, kein Urteil nennt ihn. Ein zweiter Beleg ist hier aber auch nicht nötig, und das ist
der Unterschied zu den anderen 47: sein AC-1 ist eine reine BYTE-Eigenschaft über einen
abzählbaren Bestand („keine Steuerzeichen in Kit-Hook-Quellen, gemessen über alle drei Kits"), und
die habe ich vollständig gemessen — 89 Dateien `team-kits/**/hooks/*.py`, null Vorkommen von
`0x08`. Wo ein AC so gebaut ist, IST die Messung der Beleg; ein Commit-Verweis würde nichts
hinzufügen, was die Bytes nicht schon sagen. Wo ein AC dagegen Verhalten verlangt, reicht eine
Messung allein nicht, und dort habe ich die zwei Belege verlangt.

Bewusst in Richtung „offen" geirrt habe ich bei BUG-0014, BUG-0017, BUG-0033, FR-0002 und
FR-0014 — dort ist die Deckung wahrscheinlich grösser, als ich sie hier ausweise.

---

## 7. Nebenbefunde dieser Runde

* **BUG-0052 live reproduziert.** `project_memory/.audit/hook_events.jsonl` ist weiter getrackt,
  und der Suite-Lauf dieser Runde hat ihn erneut verändert. Die Zahlen stehen im Rundenbericht,
  nicht hier — sie gehören zu einem Lauf, nicht zum Datensatz.
* **BUG-0037 ist heute durch AUSFÜHREN widerlegt worden**, nicht durch Lesen: der Kopfkommentar
  behauptet eine Absperrung, die `transition()` nicht baut.
* **`FR-0013.triage_result` ist veraltet** und beschreibt eine Lücke, die TSK-0070 geschlossen hat.
  Ein Leser, der nur das Feld liest, bekommt die falsche Antwort — dieselbe Klasse, die FR-0058
  überhaupt ausgelöst hat, nur ein Feld weiter.
* **Die Ableitung ist am eigenen Speicher zu leise** (Abschnitt 1) — aber weniger, als diese
  Runde zunächst schrieb: der Referenzgraph-Leser des Kernels überbrückt 22 der 48 gelieferten
  BUGs schon selbst. Der Nachtrags-Weg in 6b Punkt 2 gilt darum für **16** BUGs, nicht für 38.
* **Ein archiviertes Urteil öffnet das Item wieder.** Wer Nachtrags-Evidence schreibt, muss wissen,
  dass die Ablage dieser Evidence die Aussage zurücknimmt (Abschnitt 1, 6b Punkt 2).
