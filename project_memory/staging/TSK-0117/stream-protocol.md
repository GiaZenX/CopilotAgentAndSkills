# TSK-0117 — Strom C „Freigaben & Beweismittel" (Generation 3)

FR-0074 (primär), FR-0082, FR-0083, BUG-0089 — plus die während der Runde übergebene
MST-Naht aus Strom A (DEC-0064).

Worktree: `C:/Offline Repos/v2-testbed/_worktrees/g3-approvals` (Branch `g3/approvals`, ab
`e45c0ca`). Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0117/stream-approvals.patch`.
Alles Scratch unter `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0117/`.
Kein Commit, kein Push, keine Installation in den globalen Store.

---

## 0. Vorgefunden (gemessen, bevor eine Zeile geschrieben wurde)

| Frage | Messung am Stand `e45c0ca` |
|---|---|
| Wie viele Nutzerfreigaben kostet ein Produktziel? | **drei** — `required_approval_kinds` über die Kette von `PR`/`RQ`: `scope` (DRAFT→APPROVED), `delivery` (APPROVED→IN_DELIVERY), `acceptance` (DELIVERED→ACCEPTED). Zehn Ziele = 30 Fragen allein aus dem Automaten |
| Gibt es eine Kante `TSK: READY -> DRAFT`? | **nein** — `AUTOMATA["TSK"]` hat überhaupt keine Kante *nach* DRAFT (`edges into DRAFT: []`); von READY sind nur CANCELLED und LEASED erreichbar. Die gedruckte Abhilfe war unbegehbar (BUG-0089) |
| Wie entscheidet `gate_git` heute über ein Urteil? | `entry["result"] != "pass"` — also schließt **jeder** Nicht-Pass bereits. Ein dritter Wert wäre am Tag seiner Aufnahme schließend, aber der Verweigerungstext hätte ihn als *Fehlschlag* gemeldet |
| Kann heute ein Programm prägen? | **nein** — `_assert_minting_caller` kennt genau eine Route (Haken-Datei, als `__main__`). Gemessen: ein fremdes Skript, das `approvals.mint` ruft, wird verweigert |
| Ist `_AUTOMATON_TYPES` abgeleitet? | **nein** — ein handgeschriebenes Zehner-Tupel neben `AUTOMATA`. Beim elften Typ (`MST`) schrieb `capture` das Item **ohne `status`-Schlüssel**, ohne dass irgendetwas auslöste |

## 1. Plan, und der verworfene Weg in einer Zeile (FR-0084-Form)

Gebaut wurde die Empfehlung der Entscheidungsvorlage: eine eigene Freigabeart `plan`, deren
Manifest die bestätigte Zielliste samt Scope-Hash je Ziel trägt.
**Verworfen (eine Zeile):** die bestehende Bündelung auf `scope` auszudehnen — sie hätte
`assert_apr_in_force`s Item-Bindung (`apr["item"] == item["id"]`) aufweichen müssen, also genau
die Prüfung, die eine Freigabe an *diesen* Vorgang bindet; die neue Art lässt sie unberührt und
bekommt ihre eigene, engere Deckungsprüfung.

**Reihenfolge, wie beauftragt:** die DEC-Vorlage (`dec-plan-approval.json`) wurde ZUERST
geschrieben (07:34) und dem Lead im Zwischenbericht gemeldet; FR-0082, BUG-0089 und FR-0083 sind
unabhängig davon gebaut worden; FR-0074 danach in der empfohlenen Form. **Bis zur Übergabe ist
keine Nutzerentscheidung zur Vorlage eingetroffen** — gebaut ist also die Empfehlung, nicht ein
Beschluss.

## 2. Nahttabelle

| Naht | Wer | Zustand bei Übergabe |
|---|---|---|
| `docs/POST_V2_WISHLIST.md` (Löcherliste + Übersichtstabelle) | alle Ströme | H132/H133/H134 angehängt, je mit Eintrag **und** Tabellenzeile; `test_repo_hygiene` beide Richtungen grün |
| Verfassungs- und PM-Skill-Sätze zu FR-0074 | Strom D / Merge | **nicht geschrieben**, wörtlich unten in §6 |
| Rollen-SKILLs: der dritte Evidence-Ausgang | Merge | **5 Dateien offen**, Liste in §5; die eine Stelle im Kernel (`staging.py`) ist gebaut |
| `guard_no_adhoc.ITEM_TYPES` ×3 (`"mst"`) | Merge (Haken, verbotener Scope) | offen, Test rot (§5) |
| `guard_memory_budget._ID` ×3 (`MST`) | Merge (Haken, verbotener Scope) | offen, Test rot (§5) |
| `templates/repo/scripts/generate_dashboard.py` (`VIEWS`) | Merge (Templates, verbotener Scope) | offen, Test rot (§5) |
| `backlog_tree.VIEWS` / `_LABELS` (`MST`) | **Strom A** | offen, Test rot (§5) — wie vom Lead angekündigt |
| `templates/project_memory/milestones/active/.gitkeep` ×3 | Merge | offen; `test_board.test_each_kit_renders_the_types_its_own_template_ships` bleibt **grün** (er prüft nur Typen, deren Verzeichnis ein Kit liefert) |
| `DEC-0064.yaml` liegt im Hauptrepo, nicht im Worktree-Checkout | Merge | `test_repo_hygiene.test_every_decision_pointer_in_a_shipped_kit_file_resolves` ist hier rot, **gemessen grün**, sobald die Datei danebenliegt (§5) |
| `hooks/ENFORCEMENT.md` (Zeile `gate_git`) | Merge (verbotener Scope) | beschreibt die beiden neuen Zähne nicht |
| Die vier Texte, die die Befehlsoberfläche AUFZÄHLEN | Merge (verbotener Scope) | `check-scopes` fehlt in `team-kits/{dev,office,research}-team/constitution/AGENTS.md` und in `README.md`; Test rot (§5) |
| C-1/C-4 aus Strom D (FR-0021) | **dieser Strom** | gebaut, §10 |
| C-2/C-3 aus Strom D | Merge / Generation 4 | **nicht gebaut**, mit Grund und den zwei rot werdenden D-Tests in §10.4 |
| Löcher `H135`/`H136`, von `kernel/scopes.py` und `kernel/cli.py` zitiert | Merge | beide stammen aus **Strom D** und stehen erst nach dem Merge in der Löcherliste; ein Test, der H-Zeiger auflöst, existiert **nicht** (der vorhandene Prüfer liest Testnamen und DEC-Nummern) |

---

## 3. Je FR: was gebaut ist, und der Test, der ohne den Fix rot wird

### FR-0074 — Freigabe auf Planebene

**Abnahmezeile.** Eine Freigabeart `plan` (`approvals.PLAN_KIND`), deren Subjekt-Manifest die
bestätigte Zielliste ist — je Ziel Id, Titel, Revision und
`subject_manifest_hash(item_subject_manifest(item, "scope"))`, also derselbe Hash, an den eine
Einzelfreigabe bindet, mitsamt Akzeptanzkriterien. Nach der Freigabe geht jedes gelistete Ziel
`DRAFT → APPROVED` ohne weitere Frage; die Lieferseite (`delivery`, `acceptance`) bleibt je Ziel.
Was Frage bleibt, ist eine **Eigenschaft** (`approvals.IRREVERSIBLE_KINDS`: was das Projekt nicht
aus eigener Kraft zurücknehmen kann) und keine Liste. Ein Ziel, dessen Inhalt sich ändert, fällt
aus der Deckung und wird erneut gefragt.

**Gemessen** (`_round-scratch/TSK-0117/m1_plan.py`, `m2_plan_invalidate.py`; Pilot außerhalb des
Repos, `gate_approval.py` als Prozess):

```
goals: ['PR-0001', 'PR-0002']
QUESTION: Freigabe erbeten: plan für den Plan aus PR-0001 „Checkout flow" (Revision 1);
          PR-0002 „Search" (Revision 1) …
hook rc 0 → APR-0001
after: APPROVED APR-0001  APPROVED APR-0001
delivery refused OK: PR-0001 APPROVED -> IN_DELIVERY is the transition a delivery approval commits …
lease ok: [...] LEASED                      # Task unter einem plan-gedeckten Ziel dispatcht
b after edit: DRAFT 2 None
re-asked OK: PR-0002 DRAFT -> APPROVED … none is in force for PR-0002 at revision 2
a still covered: True
```

**Rot ohne den Fix** (Kopie außerhalb des Repos, `redfirst/mutate.py`):

| Mutation | roter Test |
|---|---|
| R1: Plan-Rückfall aus `assert_transition_approved` entfernt | `tools/test_approvals_dispatch.py::test_one_plan_approval_walks_every_goal_and_the_delivery_side_still_asks` |
| R2: Hash-Vergleich in `_assert_the_plan_covers` entfernt | `…::test_a_plan_stops_covering_a_goal_the_moment_its_scope_moves` |
| R3: Statusfilter in `plan_goals` entfernt | `…::test_the_plan_covers_every_open_goal_and_only_those` |

Zusätzlich zwei Stolperdrähte, beide Enden: `…::test_a_plan_can_only_stand_in_for_the_question_a_plan_answers`
(rot, sobald eine andere item-abgeleitete Art aus reinem Planinhalt baubar würde) und
`…::test_every_approval_kind_is_classified_as_takeable_back_or_not` (rot bei einer neuen,
unklassifizierten Freigabeart — gemessen mit einer erfundenen Art `wire_transfer`).

**Wichtig zu R2:** die erste Fassung des Tests wurde von R2 **nicht** rot — die Revisionsprüfung
fing die Änderung schon ab. Der Test hat seither eine zweite Hälfte, die am Kernel vorbei in die
Item-Datei schreibt (die Bearbeitung, für die der Hash überhaupt existiert); damit ist er rot.

### FR-0082 — der dritte Evidence-Ausgang

**Abnahmezeile.** `EVIDENCE_RESULTS` kennt `blocked`. `gate_git` schließt darauf wie auf `fail`
(strukturell: jeder Wert außer `backlog_types.PASSING_RESULT` schließt) und sagt in einem eigenen
Zweig, **was** den Lauf verhindert hat und **dass nichts geprüft wurde**. Ein `blocked` ohne
diesen Satz wird vom Kernel verweigert — und der Satz unter jedem anderen Ergebnis ebenso. Der
Merge liest den Satz über `report._newest_per_kind`, das ihn mit dem Urteil ausliefert, damit die
Schranke den Beweisspeicher kein zweites Mal liest.

**Gemessen** (`m4_gate.py`, ausgelieferter `gate_git.py` als Prozess):

```
capture EVD: result is 'blocked' and blocked_reason is empty. … Remedy: pass --blocked-reason '<what stopped the run>'.
EVD-0003 test: blocked
B rc 2
[team-kit gate_git] the current QA verdict records a run that did NOT happen — PR-0001: test blocked (EVD-0003).
Nothing was checked: test (EVD-0003): no Chromium on this runner. A blocked verdict closes this merge exactly
as a failing one does, and the harness does not verify the reason — it is what the recording role stated.
```

**Rot ohne den Fix:**

| Mutation | roter Test |
|---|---|
| R4: Paar-Prüfung aus `capture_preflight` entfernt | `tools/test_state.py::test_a_blocked_evidence_owes_its_sentence_and_the_sentence_owes_its_verdict` |
| R5: `blocked` aus `EVIDENCE_RESULTS` entfernt | `tools/test_backlog_types.py::test_a_blocked_verdict_is_in_the_vocabulary_and_carries_its_own_field_name` **und** `tools/test_hooks.py::test_gate_git_closes_on_a_blocked_verdict_and_says_nothing_was_checked` (die CLI verweigert dann `--result blocked`) |
| R6: `blocked`-Zweig aus `gate_git` entfernt | `tools/test_hooks.py::test_gate_git_closes_on_a_blocked_verdict_and_says_nothing_was_checked` |
| R11: ein Leser, der auf `"fail"` **beim Namen** entscheidet | `tools/test_backlog_types.py::test_only_the_passing_result_opens_anything_the_kernel_decides` (liest die laufenden Leser per `ast`, nicht den Text) |

### FR-0083 — Provenienz einer Freigabe

**Abnahmezeile.** Jede Freigabe trägt `minted_via`, **abgeleitet davon, wer läuft**
(`_assert_minting_caller` gibt die erkannte Route zurück) und niemals aus einem Parameter.
Zwei Routen: der Freigabe-Haken (`user_answer_via_approval_hook`) und die Kernel-Brücke
`kernel/sdk_approval.py`, die ein einbettendes Programm aus dem `canUseTool`-Rückruf des Agent
SDK ruft (`program_answer_via_agent_sdk`). `approvals.approval_card` liest die Route **aus dem
Datensatz** und wird von beiden Oberflächen gedruckt. Der Kernel verweigert einem Programm jede
Art aus `IRREVERSIBLE_KINDS`; `gate_git` verweigert jeden Merge/Push über einen Vorgang, dessen
vorgezeigte Freigabe ein Programm geprägt hat. Gebaut auf der **Korrektur** von §10 (headless ist
erreichbar, `H80`), nicht auf der widerlegten Prämisse.

**Gemessen** (`m3_sdk.py`, `m4_gate.py`):

```
1 interactive minted_via: user_answer_via_approval_hook
1 card: Freigabe APR-0001 (scope) für PR-0001. Erteilt von einem Menschen, über die Freigabe-Frage des Programms.
2 programmatic minted_via: program_answer_via_agent_sdk
2 card: … Erteilt von einem PROGRAMM (Agent SDK, canUseTool) — nicht von einem Menschen. …
3 refused OK: a 'push' approval authorises something this project cannot take back …
4 refused OK: an approval can only be minted from the gate_approval.py hook …
A rc 2 [team-kit gate_git] PR-0001 stands on approval APR-0001, and a PROGRAM minted it …
```

**Rot ohne den Fix:**

| Mutation | roter Test |
|---|---|
| R7: `minted_via`-Stempel aus `mint` entfernt | `tools/test_hooks.py::test_the_approval_hook_stamps_the_interactive_route_and_prints_it_on_the_card` (KeyError) und `tools/test_approvals_dispatch.py::test_the_card_names_the_route_that_minted_the_approval` |
| R8: `_assert_the_route_may_decide_this` aus `mint` entfernt | `…::test_a_program_cannot_mint_a_permission_the_project_cannot_take_back` |
| R9: Provenienz-Zahn aus `gate_git` entfernt | `tools/test_hooks.py::test_gate_git_refuses_a_merge_whose_authorisation_a_program_gave_itself` |

**Eine Korrektur an meinem eigenen Test, gemessen:** die erste Fassung von
`test_the_approval_hook_stamps_…` fragte `approvals.minted_via(apr)` — das antwortet für einen
Datensatz **ohne** Feld `INTERACTIVE_MINT`, also konnte der Test für seine eigene Behauptung nicht
scheitern. Er liest jetzt das gespeicherte Feld direkt; unter R7 ist er rot (KeyError).

### BUG-0089 — die Abhilfe kommt aus dem Automaten

**Abnahmezeile.** Die Verweigerung eines eingefrorenen Arbeitsauftrag-Feldes leitet ihre Abhilfe
zur Verweigerungszeit aus `AUTOMATA` ab (`backlog_types.replanning_route`: die vom aktuellen
Status **in einem Schritt** erreichbare Planungsstatus-Menge und die erreichbaren Endzustände).
Die Einfrier-Bedingung selbst liest denselben Fakt (`initial_status(item_type)` statt der
Zeichenkette `"DRAFT"`), damit Bedingung und Rat nicht auseinanderlaufen können. **Es wurde keine
Kante `READY -> DRAFT` ergänzt** — was das kostet, steht in §5.

**Gemessen** (`m5_bug89.py`):

```
REFUSAL: TSK-0001 is READY -- its work-order fields (expected_outputs) are frozen outside DRAFT
because gates read them … Remedy: transition TSK-0001 to CANCELLED and capture a new task with the
corrected work order -- re-planning has to be visible, not a field write.
names DRAFT? False
```

**Rot ohne den Fix:** R10 (alter Prosa-Satz zurück) → `tools/test_state.py::test_a_frozen_field_refusal_names_only_walkable_transitions`.
Beide Enden über alle ausgelieferten Automaten:
`tools/test_backlog_types.py::test_the_replanning_route_names_only_edges_the_automaton_has`.

### MST (DEC-0064) — die Kernel-Zeilen der Naht aus Strom A

**Abnahmezeile.** `AUTOMATA["MST"]` (PLANNED→REACHED; Endzustände REACHED/MISSED/DROPPED, die
letzten beiden nur aus PLANNED), `ACTIVE_DIRS["MST"] = "milestones/active"`,
`REQUIRED_FIELDS["MST"] = ("title", "due", "derives_from")`, **kein** Eintrag in
`APPROVAL_TRANSITIONS` und `INVALIDATION_TARGET`, plus die Datumsprüfung von `due` in
`state.capture_preflight` (`date.fromisoformat`, sonst Verweigerung mit Satz).

**Ein Fund unterwegs, gemessen:** `state._AUTOMATON_TYPES` war ein handgeschriebenes Tupel neben
`AUTOMATA`. Der elfte Typ landete dadurch **ohne `status`-Feld** im Speicher, und nichts löste
aus. Jetzt `frozenset(AUTOMATA)`.

**Gemessen** (`m6_mst.py`):

```
captured: MST-0001 PLANNED 2026-10-01     file: True
  refused 'Oktober' / '2026-13-01' / '2026-10-01T00:00' / ''  -> "not a calendar date"
edges: [('PLANNED','DROPPED'), ('PLANNED','MISSED'), ('PLANNED','REACHED')]
reached: REACHED    missed: MISSED
reached -> missed refused: illegal transition MST: REACHED -> MISSED (allowed from REACHED: -)
no approval kind: []
```

**Rot ohne den Fix:**

| Mutation | roter Test |
|---|---|
| R13: `_AUTOMATON_TYPES` zurück auf das Zehner-Tupel | `tools/test_state.py::test_every_type_with_an_automaton_is_captured_with_its_initial_status` (KeyError `status`) |
| R14: `DATE_FIELDS`-Schleife aus `capture_preflight` entfernt | `tools/test_state.py::test_a_date_field_that_is_not_a_date_is_refused_at_capture` |
| R15: `MST` in `APPROVAL_TRANSITIONS` aufgenommen | `tools/test_backlog_types.py::test_the_milestone_automaton_can_only_end_a_milestone_once` |
| R16: ein `DATE_FIELDS`-Eintrag, den der Typ nicht hat | `tools/test_backlog_types.py::test_every_declared_date_field_is_a_field_its_type_really_has` |

*(Eine Kante aus einem Endzustand heraus fängt bereits die Konstruktions-Selbstprüfung von
`_Automaton` beim Import — gemessen: `AssertionError: terminal state 'REACHED' must not have
outgoing edges`, Collection-Fehler. Deshalb misst der Test oben die Hälfte, die der Import **nicht**
sieht.)*

---

## 4. Zwei Fixtures der Suite, die meine Änderungen brauchten (und warum das kein Nachgeben ist)

* `tools/test_state.py::_contract_payload` füllte jedes Pflichtfeld mit dem **alphabetisch ersten**
  Vokabelwert — mit `blocked` in `EVIDENCE_RESULTS` traf es ab sofort die neue Paar-Regel, und mit
  `MST` die Datumsregel. Die Fixture erfüllt beide jetzt **aus den Kernel-Konstanten**
  (`BLOCKED_REASON_FIELD`, `DATE_FIELDS`), statt einen Wert festzuschreiben.
* `tools/test_staging_cli.py::SUBJECT_SAMPLES` reichte jedem Manifest-Bauer `"x"`; das Plan-Subjekt
  ist eine **Liste** von Zielsätzen. Der Sample ist mit den Kernel-Feldnamen gebaut
  (`approvals.GOAL_ITEM_FIELD`, `GOAL_SCOPE_HASH_FIELD`). `plan_subject_manifest` verwirft
  außerdem alles, was kein Zielsatz ist, und landet dann auf seiner eigenen Verweigerung.
* `tools/test_report.py` — die exakte Wörterbuch-Gleichheit auf ein Urteil wurde **nicht**
  aufgeweicht, sondern um den neuen Schlüssel ergänzt; und der Korpus von
  `test_every_captured_type_that_hangs_from_a_root_reaches_it` hat jetzt ein `MST`.

## 5. Bewusst NICHT geschlossen, aber benannt

**Löcherliste** (Einträge + Übersichtszeilen, `docs/POST_V2_WISHLIST.md`), Nummern H132–H134 wie
zugeteilt:

* **H132** — eine Antwort autorisiert N Ziele. Begrenzt (gemessen): nur die Scope-Frage; Hash über
  Liste *und* Scope-Manifest je Ziel; leere Liste verweigert; die Frage nennt jedes Ziel.
  **Nicht** begrenzt: die Länge der Liste.
* **H133** — der SDK-Weg trägt die dritte Bedingung von `_assert_minting_caller` nicht; jedes
  Programm, das die Brücke ruft, prägt. Begrenzt: Stempel + Karte, Kernel-Verweigerung der
  unumkehrbaren Arten, `gate_git` am Merge. **Nicht** begrenzt: der vorsätzliche Fälscher (der
  konnte auch die Haken-Route schon).
* **H134** — `blocked` ist ein Zustand, keine Messung. Begrenzt: ein falsches `blocked` kauft
  nichts (es schließt wie `fail`), der Datensatz ist unveränderlich, und die Einschränkung steht
  an drei gebauten Stellen. **Nicht** begrenzt: die Wahrheit der Begründung, in beide Richtungen.

**BUG-0089, die andere Hälfte:** ein `READY`-Task lässt sich nach wie vor **nicht** neu planen,
nur abbrechen und neu erfassen. Ich habe die Kante `READY -> DRAFT` bewusst nicht ergänzt: sie ist
die einzige Kante rückwärts aus der Warteschlange und hätte Folgen für Index, Brief und den
Lease-Lebenszyklus, die dieser Strom nicht misst. BUG-0089 lässt beide Wege ausdrücklich zu; der
gewählte ist der, den der Lead in derselben Sache selbst gegangen ist (TSK-0107 stehen gelassen,
TSK-0113 neu geschnitten).

**Ein `MST` mit leerer `derives_from`-Liste** ist erfassbar und hängt dann an nichts. Ich habe
`NONEMPTY_FIELDS` **nicht** erweitert, weil diese Zeile nicht in der übergebenen Tabelle stand;
sie wäre der offensichtliche Nachtrag, gehört aber dem, der DEC-0064 besitzt.

**Vier Tests bleiben rot, alle aus verbotenem Scope, alle gemessen:**

| roter Test | was fehlt | wem gehört es |
|---|---|---|
| `tools/test_board.py::test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view` | `backlog_tree.VIEWS`/`_LABELS` um `MST` | **Strom A** (vom Lead als erwartete Naht-Röte angekündigt) |
| `tools/test_hooks.py::test_no_adhoc_covers_every_item_type` | `guard_no_adhoc.ITEM_TYPES` ×3 um `"mst"` | Merge |
| `tools/test_hooks.py::test_dashboard_views_cover_every_item_type` | `templates/repo/scripts/generate_dashboard.py` `VIEWS` | Merge |
| `tools/test_hooks_v2.py::test_the_id_prefixes_match_the_kernels_item_types` | `guard_memory_budget._ID` ×3 um `MST` | Merge |

**Ein fünfter, aus FR-0082 und in der Naht-Ankündigung nicht vorgesehen:**
`tools/test_hooks.py::test_no_instruction_text_names_an_evidence_kind_or_verdict_the_kernel_refuses`
verlangt, dass eine Prosa-Auswahl von Ergebnissen **vollständig** ist. Sechs Stellen schrieben
`--result <pass|fail>`; eine davon lag in meinem Scope und ist gebaut
(`team-kits/kernel/staging.py` → `<pass|fail|blocked>`). Die fünf übrigen sind Skills und damit
verboten:

```
team-kits/dev-team/skills/project-auditor/SKILL.md
team-kits/dev-team/skills/quality-engineer/SKILL.md
team-kits/office-team/skills/project-auditor/SKILL.md
team-kits/research-team/skills/project-auditor/SKILL.md
team-kits/research-team/skills/reviewer/SKILL.md
```

Das ist genau die Zeile, die Wunschliste §7 als Teil des Baus verlangt („die Rollen-SKILLs, die
sagen, wann welcher Ausgang zu buchen ist"). Sie gehört an den Merge — zusammen mit dem Satz,
**wann** `blocked` zu buchen ist.

**Ein siebter, aus C-1:** `tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`
verlangt, dass jeder Text, der die Befehlsoberfläche aufzählt, sie GANZ aufzählt. `check-scopes`
fehlt in vier Texten, alle verboten:

```
team-kits/dev-team/constitution/AGENTS.md
team-kits/office-team/constitution/AGENTS.md
team-kits/research-team/constitution/AGENTS.md
README.md
```

Je eine Zeile in der Befehlstabelle genügt. Die eine Stelle in meinem Scope war `kernel/cli.py`
selbst (der Rumpf von `build_parser` las sich als Teilliste, sobald der Name dort dreimal
vorkam) — gelöst, indem der Befehlsname jetzt genau EINMAL steht
(`cli.CHECK_SCOPES_COMMAND`) und die Flaggenhilfe auf das Modul statt auf den Befehl zeigt.

**Ein achter, der sich am Merge von selbst löst:**
`tools/test_repo_hygiene.py::test_every_decision_pointer_in_a_shipped_kit_file_resolves` ist rot,
weil die gebauten Zeilen `DEC-0064` nennen und diese Entscheidung im Worktree-Checkout (`e45c0ca`)
noch nicht liegt. **Gemessen**: mit `DEC-0064.yaml` daneben ist der Test grün
(`_round-scratch/TSK-0117/decprobe/`, `2 passed`).

**`hooks/ENFORCEMENT.md`** beschreibt `gate_git` weiterhin ohne die beiden neuen Zähne (blockiertes
Urteil, programmatische Freigabe). Kit-spezifische Datei, verbotener Scope — Merge.

## 6. Nahtsätze für Strom D — wörtlich, nicht von mir geschrieben

Für Verfassung und PM-Skill der Kits (`team-kits/*/constitution/**`, `team-kits/*/skills/**`),
falls und sobald der Nutzer die Vorlage `dec-plan-approval.json` entscheidet:

> Die Planungsphase ist absichtlich gründlich: der Project Manager leitet die vollständige Liste
> der Produktziele aus dem Masterplan ab, geht jedes einzeln mit dir durch, bringt dabei eigene
> Vorschläge ein und denkt um die Ecken, und hält jedes bestätigte Ziel mit seinen
> Abnahmekriterien fest.

> Ist die Liste bestätigt, holt der Project Manager EINE Freigabe für den ganzen Plan ein. Danach
> arbeitet das Team die Ziele der Reihe nach ab, ohne dich je Ziel noch einmal nach dem Umfang zu
> fragen.

> Was danach noch gefragt wird, ist keine Liste, sondern eine Eigenschaft: alles, was das Projekt
> nicht aus eigener Kraft zurücknehmen kann oder was Geschmackssache ist — Merge und Push,
> Gestaltungsentscheidungen, Geld, und alles, was der Plan nicht geklärt hat.

> Die Lieferseite bleibt je Ziel: Urteile, Beweismittel und die Merge-Schranke gelten weiter für
> jedes einzelne Ziel. Ein Ziel, das sich nicht wie geplant bauen lässt, kommt als Frage zu dir
> zurück und wird nicht improvisiert.

Für die QA-/Auditor-Skills (FR-0082), als Ergänzung zur `evidence`-Zeile:

> `--result blocked` ist für einen Lauf, der gar nicht stattgefunden hat — kein Browser, kein
> Gerät, kein Netz. Er braucht `--blocked-reason "<was den Lauf verhindert hat>"`; ohne diesen
> Satz nimmt der Kernel den Datensatz nicht an. Ein blockiertes Urteil schließt den Merge genau
> wie ein Fehlschlag; es sagt nur etwas anderes: es wurde nichts geprüft.

## 7. Suiten-Läufe (nur die betroffenen — die volle Suite gehört an den Merge, DEC-0050)

| Lauf | Ergebnis |
|---|---|
| `tools/test_approvals_dispatch.py test_backlog_types test_state test_kernel test_report test_staging_cli` (Abschlusslauf, nach der letzten Änderung) | **629 passed** (3:35) |
| `tools/test_hooks.py` (voll) | 902 passed, 13 skipped, **3 failed** (15:06) — die drei aus §5 |
| `tools/test_hooks_v2.py test_migrate test_report test_kernel test_e2e test_schemas test_disposition test_role_contracts` | 2607 passed, **3 failed** (25:27); zwei davon danach behoben (`test_report`-Korpus, `validate_py_is_green` durch den zweiten Versionsstempel), einer bleibt (`id_prefixes`, §5) |
| `tools/test_board.py test_repo_hygiene test_kit_neutrality test_shared_skill_contract test_reference_skills` | 102 passed, **2 failed** (3:07) — beide aus §5 |
| `tools/test_staging_cli.py` | 98 passed |
| `tools/test_hooks.py test_hooks_v2 test_role_contracts test_e2e test_report` (Abschlusslauf nach C-1/C-4) | 3203 passed, 13 skipped, **5 failed** (33:48) — die fünf aus §5; der fünfte (`command_surface`) danach auf die vier verbotenen Texte reduziert |
| `tools/test_state test_backlog_types test_approvals_dispatch test_kernel test_staging_cli test_parallel_scopes test_repo_hygiene` (Abschlusslauf) | 548 passed, **1 failed** (4:30) — der DEC-0064-Zeiger aus §5 |
| `tools/test_parallel_scopes.py` (11 Tests, 8 davon als Prozess) | 11 passed |
| `.claude/hooks/test_gates.py` | **489 passed** (21:01) |
| `python -m ruff check .` | grün |
| `python tools/validate.py` | „all structural checks passed" |

## 8. Versionsstempel (vorläufig)

`python tools/bump_kit_version.py` — viermal gefahren (nach `staging.py` und nach dem C-1/C-4-Nachtrag):
**2026.09.03-6** in allen drei Kits. `team-kits/kernel/sdk_approval.py`, `team-kits/kernel/scopes.py` und
`tools/test_parallel_scopes.py` sind neu und mit `git add` in den Index genommen — ohne das meldet `validate.py`, die Datei gehe in einen
Kit-Hash ein, sei aber nicht getrackt. **Kein Commit.**

## 9. Zahlen für die (g)-Tabelle

| | |
|---|---|
| Wanddauer | ~3 h Runde + ~1 h 10 min Nacharbeit 1 + ~40 min Nacharbeit 2 + ~25 min Abschluss |
| Tokens (Kontextverbrauch dieses Umsetzers) | ~0,60 Mio (Runde + Nacharbeit 1) |
| Patch | 24 Dateien, +2879 / −131 (231 318 B, reines LF, sha256 `e3ab4ceac6b0`) |
| Neue Tests | **35**, gemessen über den Patch (`grep '^+def test_'`): 5 Prozess-Tests über ausgelieferte Haken, 9 Prozess-Tests über `check-scopes`, davon einer über den ausgelieferten `scripts/harness.py` |
| Gemessene Rot-zuerst-Mutationen | 27 (R1–R22 der Runde, W1–W5 Nacharbeit 1, W6–W7 Nacharbeit 2; jede einzeln gefahren und zurückgesetzt) |
| Ausgelassen im Patch | `project_memory/.audit/hook_events.jsonl` (2 Zeilen, Nebenprodukt der Testläufe im Worktree, kein Arbeitsergebnis) |

---

## 10. Nachtrag: die Kernel-Anforderungen aus Strom D (C-1 und C-4), während der Runde übergeben

**Empfang bestätigt** für beide Zwischenaufträge des Leads: die MST-Naht (DEC-0064) — gebaut, §3 —
und die vier Anforderungen aus `project_memory/staging/TSK-0118/stream-protocol.md` §3. Gebaut sind
**C-1 und C-4**, wie vom Lead vorgegeben; **C-2 und C-3 nicht** (§10.4).

### C-1 — das Kernel-Verb `check-scopes`

**Abnahmezeile.** `kernel/scopes.py` plus der Unterbefehl `check-scopes` auf der Kernel-Oberfläche,
also hinter `scripts/harness.py`. Das Prädikat ist **das laufende**: `gate_write_scope._matches`
wird importiert, nicht nachgeschrieben — die Gate-Datei wird relativ zum **Kernel-Paket** gefunden
(`.claude/hooks` neben `.claude/kernel` im installierten Projekt, `team-kits/<kit>/hooks` im
Werkstatt-Checkout), also braucht kein Aufrufer einen Pfad zu übergeben. Zwei Universen wie in der
Vorlage: die realen Dateien (`git ls-files -c -o --exclude-standard`) und je ein Zeuge pro
Scope-Eintrag, damit ein noch leeres Verzeichnis nicht unsichtbar ist. rc 2 bei Überlappung, rc 0
bei Disjunktheit, und „nichts verglichen" teilt mit keinem der beiden ein Wort.

**Gemessen am echten Generation-3-Schnitt** (Kopie des Hauptrepo-Zustands unter
`_round-scratch/TSK-0117/cutprobe/`, das Verb **durch den ausgelieferten `scripts/harness.py`** als
Prozess, Kernel über eine Mini-Installation `.claude/{hooks,kernel}`):

```
--only TSK-0115..0119                                    -> rc 2, "refused: 10 overlapping pair(s)"
--only TSK-0115..0119 --seam docs/** tools/** team-kits/*/VERSION
                                                         -> rc 0, "disjoint"
```

Das ist genau die Messung, die Strom D in seinem Protokoll nennt (10/10 ohne Deklaration, 0/10 mit
den drei Nähten) — hier über die Kunden-Route reproduziert. Über alle offenen Aufträge des
Hauptrepos (ohne `--only`) sind es 15 Paare; die zusätzlichen kommen von `TSK-0088`, einem alten
offenen Auftrag mit weitem Scope — auch das ein echter Befund über den Schnitt und keiner über das
Werkzeug.

**Rot ohne den Fix** (Kopie außerhalb des Repos, `redfirst/mutate2.py`):

| Mutation | roter Test |
|---|---|
| R17: Unterbefehl von der Oberfläche genommen | `tools/test_parallel_scopes.py::test_two_orders_with_the_same_scope_are_refused_and_disjoint_ones_are_not`, `…::test_the_verb_runs_through_the_shipped_entry_point`, `…::test_the_check_command_is_on_the_shipped_parser` |
| R18: `witnesses` liefert nichts | `…::test_an_overlap_that_exists_only_in_an_empty_directory_is_still_an_overlap` |
| R21: `fnmatch` statt des ausgelieferten Prädikats | `…::test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling` |

### C-4 — die Naht als Item-Feld (`seam_scope`)

**Abnahmezeile.** Optionales `TSK`-Feld `seam_scope`, in `TSK_PLAN_FIELDS` mit eingefroren, mit
einer Flagge an `create-task`, und von `scopes.pair_seam` **vor** dem Vergleich subtrahiert —
**nur, wenn BEIDE Aufträge des Paares es deklarieren**. Das ist die fail-closed Lesart: eine Naht
ist eine Datei, die kein Strom allein besitzen kann (DEC-0062 (5)); deklariert nur einer, wurde
der andere geschnitten in dem Glauben, die Datei gehöre ihm.

**Rot ohne den Fix:**

| Mutation | roter Test |
|---|---|
| R20: `pair_seam` als VEREINIGUNG statt Schnittmenge | `tools/test_parallel_scopes.py::test_a_seam_only_one_of_the_two_declares_is_not_a_seam` |
| R19: Feld aus dem Typvertrag genommen | `…::test_the_seam_field_is_declared_once_and_read_from_there` |
| R22: Feld aus `TSK_PLAN_FIELDS` genommen | `…::test_the_seam_field_is_frozen_with_the_rest_of_the_work_order` |

**Eine Behauptung, die ich gemessen und dann zurückgenommen habe:** die erste Fassung des
C-4-Tests behauptete, ohne den Vertragseintrag verweigere der Kernel die Erfassung. **Gemessen:
tut er nicht** — ein `TSK` mit einem undeklarierten Feld wird gespeichert und `validate_state`
meldet nichts dazu. Der Vertragseintrag ist also eine **Deklaration** und keine Wand; das steht
jetzt so im Test und in seinem Docstring, und die Wand, die die Naht wirklich hat, ist das
Einfrieren.

### Was das kostet, benannt

`seam_scope` in `TSK_PLAN_FIELDS` heißt: eine Naht lässt sich an einem `READY`-Auftrag nicht mehr
nachtragen. Das ist gewollt (sie entscheidet einen Schnitt, der schon verteilt ist), aber es ist
eine echte Einschränkung — und in Verbindung mit BUG-0089 heißt sie: abbrechen und neu erfassen.
Beide Hälften stehen in §5 bzw. hier.

### C-2 und C-3 — nicht gebaut, benannt

* **C-2** (Verweigerung in `create_lease` bei überlappendem Scope) und **C-3** (Worktree-Feld auf
  der Lease) sind **nicht gebaut**. Grund in einem Satz: beide machen zwei Tests von Strom D rot
  und verlangen Korrekturen an Verfassungsabsatz und `parallel-streams`-Skill, die in meinem
  verbotenen Scope liegen — also wäre das Ergebnis dieselbe Art unfertiger Naht, die diese Runde
  schon viermal trägt, in einem Bereich (`dispatch.create_lease`), den ich sonst nicht anfasse.
* Wer sie baut, macht damit **wörtlich** rot:
  `tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`
  (C-2) und `tools/test_parallel_streams.py::test_the_lease_carries_no_tree_of_its_own` (C-3), und
  muss den Verfassungsabsatz („nothing compares two of them") sowie die Abschnitte 2 und 7 des
  `parallel-streams`-Skills korrigieren — beides von Strom D als Mutationen M13/M14 vorgeführt.

### Naht: die Werkstatt-Vorlage von D

`C:/Offline Repos/v2-testbed/_worktrees/g3-parallel/tools/check_scope_overlap.py` bleibt als
Werkstatt-Instrument bestehen und ist jetzt der **zweite** Leser derselben Frage. Die Merge-Runde
entscheidet, ob es auf `kernel.scopes` umgestellt oder entfernt wird; solange beide da sind, ist
das eine zweite Schreibweise derselben Antwort — genau die Klasse, die dieses Repo sonst entfernt.
Ich habe es **nicht** angefasst (fremder Worktree).

**Wo die beiden auseinandergehen, gemessen und für die Merge-Runde (TSK-0120) benannt:** Prädikat und Regel stimmen überein, die **Eingabe** nicht — D's Werkzeug nimmt die Naht nur von der Kommandozeile, das Kernel-Verb zusätzlich aus dem Itemfeld `seam_scope`. Ein Schnitt, der seine Naht am Item deklariert, ist für D's Werkzeug daher unsichtbar: es meldet als Kollision, was das Kernel-Verb als „seam only“ führt.

---

## 11. Nacharbeit 1 (Prüfurteil FAIL: B 2 / M 2 / N 7)

Alle Rot-zuerst-Messungen dieser Nacharbeit in einer Kopie außerhalb des Repos
(`_round-scratch/TSK-0117/rw1/`, Mutationen W1–W5, je einzeln gefahren und zurückgesetzt).

### B1 — eine Planfreigabe schloss Merge UND Push

**Ursache.** `state._transition_locked` stempelt seit dieser Runde die genehmigende APR in
`approval_ref`. Eine Plan-APR trägt `item: None` und `revision: None` (ihr Subjekt ist die
Zielliste). `report.validate_state` rechnete den Revisionsvergleich **selbst** — also las es jedes
plan-gedeckte Ziel als Out-of-band-Edit, `gate_memory_complete` blockte darauf, und beide Hälften
des Rats waren falsch: es gab keine Änderung, und eine erneute Planfreigabe schreibt wieder `None`.

**Fix.** Der Validator fragt die EINE Definition von „in Kraft" —
`approvals.assert_apr_in_force` —, die `assert_transition_approved` und der Dispatch schon
benutzen und die den Plan-Zweig kennt. Die zwei privaten Vergleiche (Revision, Inhalts-Hash) sind
damit weg; der Satz kommt aus dem Kernel-Zweig, `_approval_integrity_finding` trennt ihn an seinem
eigenen `Remedy:` in die zwei Spalten des Befunds.

**Gemessen** (`_round-scratch/TSK-0117/n1_merge.py`, `gate_memory_complete.py` als Prozess):

```
BEFORE git merge feat/PR-0001-x   rc=0     BEFORE git push origin main   rc=0
AFTER  git merge feat/PR-0001-x   rc=0     AFTER  git push origin main   rc=0
validate_state errors: []
```

**Keine Verschärfung an echtem Zustand:** derselbe Speicher (Kopie von
`AgentAndSkills/project_memory`, 6 Freigabedatensätze) ergibt mit dem alten und dem neuen
`report.py` identisch **0 errors / 54 warnings** — der Wechsel auf die gemeinsame Definition
bringt keine neuen Befunde auf einem Bestandsprojekt.

**Rot ohne den Fix (W1):** `tools/test_report.py::test_a_plan_approved_goal_is_not_reported_as_an_out_of_band_edit`
und `tools/test_hooks.py::test_a_plan_approval_does_not_close_the_merge_gate` (Haken als Prozess,
beide Zeilen — Merge und Push). Der zweite Test hält genau die gemessene Kette; der erste hält
zusätzlich die Gegenrichtung: ein echter Out-of-band-Edit an einem plan-gedeckten Ziel **bleibt**
ein Fehler.

**Ein Nachbar-Test musste mitziehen und wurde nicht abgeschwächt:**
`test_out_of_band_hand_edit_detected_via_hash` verlangte die Wortfolge „re-approve or revert" —
die Formulierung des entfernten Duplikats. Er liest jetzt die **beiden Auswege** (re-approve,
restore) statt einer Schreibweise, mit dem Grund im Docstring.

### M1 — die Prüfung faltete nicht, der Haken schon

**Ursache.** `kernel.scopes` importierte `gate_write_scope._matches`, aber nicht `_norm`. Der
Haken faltet BEIDE Seiten (`_scope_entries` den Eintrag, `_repo_relative(fold=True)` den Pfad),
also beantwortete die Prüfung eine andere Frage als das Gate: `Tools/**` × `tools/**` mit realer
`tools/x.py` kam als `disjoint` rc 0 zurück, während der Haken beiden Aufträgen dieselbe Datei
freigibt.

**Fix.** `matcher()` gibt einen Wrapper zurück, der beide Seiten durch das ausgelieferte `_norm`
schickt; `_shipped_halves()` liefert die zwei Funktionen, damit der Test ihre Identität lesen kann
statt einer Behauptung. Der Kopfabsatz nennt jetzt beide Hälften und die gemessene Fehlform.

**Rot ohne den Fix (W2):** `tools/test_parallel_scopes.py::test_a_case_only_difference_is_the_same_ownership_the_gate_grants`
(rc 2 statt rc 0, mit `tools/x.py` in der Ausgabe) und
`…::test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling`.

### M2 — `due: None` wurde gespeichert

**Ursache.** Der Kommentar sagte, ein fehlender Wert sei Sache der Pflichtfeldschleife; die
refüsiert aber nur ein **abwesendes** Feld. `due: None` lief durch die Datumsprüfung
(`if value is None: continue`) und landete im Speicher — auf einem Typ, den nichts mehr ändert.

**Fix.** Präsenz statt Wahrheitswert: `if field not in fields: continue`. Ein Schlüssel, der da
ist, wird beurteilt, was immer er hält. Der Kommentar sagt jetzt genau das.

**Rot ohne den Fix (W3):** `tools/test_state.py::test_a_date_field_that_is_not_a_date_is_refused_at_capture`,
das `None` jetzt in seiner Werteliste führt.

### N1 — eine Schreibweise je Tag

**Fix.** `backlog_types.normalised_date` ist der eine Leser: `capture_preflight` verweigert damit,
`capture` **speichert damit**. `20261001` wird als `2026-10-01` abgelegt, also sortiert jeder
Leser, der nach `due` ordnet, richtig. Was der Interpreter entscheidet — welche Formen überhaupt
angenommen werden — bleibt seins und steht als **H147** mit der gemessenen Tabelle in der
Löcherliste. Der Test fragt die Standardbibliothek erst, bevor er die kompakte Form prüft, damit
er auf einer älteren Version nicht aus dem falschen Grund rot wird.

**Rot ohne den Fix (W4):** derselbe Test.

### N3 — eine Naht, die einen Auftrag verschluckt, ist keine

**Fix.** `scopes.owns_anything_outside`: eine Deklaration wird nur subtrahiert, wenn **beide**
Aufträge danach noch etwas Eigenes besitzen. Sonst bleibt das Paar eine Kollision, und die Ausgabe
sagt warum („NOT A SEAM: … leaves TSK-0001 owning nothing of its own"). Die Regel ist eine
Eigenschaft und keine Form — `**`, „alle Einträge aufgezählt" und `docs/**` bei zwei Aufträgen,
die nur `docs/**` besitzen, fallen gleich.

**Gemessen** (`_round-scratch/TSK-0117/n3_seam.py`, `check-scopes` als Prozess):

| Naht auf beiden Aufträgen | rc |
|---|---|
| `**` | 2 |
| `docs/**`, wo beide nur `docs/**` besitzen | 2 |
| `team-kits/**`, wo beide daneben Eigenes besitzen | **0** |
| die echte Naht `team-kits/*/VERSION` | 0 |

Die dritte Zeile ist die bewusst offene Restklasse und steht als **H148** in der Löcherliste, mit
dem Grund, warum die engere Regel („nicht mehr als die tatsächliche Schnittmenge") hier NICHT
gebaut ist: sie würde die legitime Glob-Naht `team-kits/*/VERSION` verbieten.

**Rot ohne den Fix (W5):** `tools/test_parallel_scopes.py::test_a_seam_that_leaves_an_order_owning_nothing_is_refused`,
der beide Enden hält — der Totalfall wird verweigert, die echte Naht bleibt erlaubt.

### Kleinbefunde

* **N2** — `kernel/scopes.py` (:8, :33, :168) und `kernel/cli.py` (:888) zitieren `H135`/`H136`.
  Diese Löcher stammen aus **Strom D** und stehen erst nach dem Merge in `docs/POST_V2_WISHLIST.md`;
  ein Test, der H-Zeiger auflöst, existiert nicht (der vorhandene Prüfer liest Testnamen und
  DEC-Nummern). → Zeile in der Nahttabelle (§2).
* **N5** — die Zahl der neuen Tests steht jetzt gemessen (`grep '^+def test_'` über den Patch): **35**.
* **N6** — das Urteil von `H132` zeigt nicht mehr auf die Vorlage, sondern auf **`DEC-0068`**; die
  Vorlage bleibt als historischer Stand liegen und ist ausdrücklich nicht mehr der Maßstab. Die
  Kostenaussage in §3 dieses Protokolls ist geprüft: sie sagt „ein geändertes Ziel fällt aus der
  Deckung, während die übrigen gedeckt bleiben" — **je Ziel**, wie gemessen, nicht für alle.
* **N7** — der Worktree-Diff trägt `project_memory/.audit/hook_events.jsonl` (zwei Zeilen aus
  Testläufen im Worktree). Der Patch schließt die Datei aus; sie ist hier benannt und ist kein
  Arbeitsergebnis.

### Ein eigener Fehler dieser Nacharbeit, gemessen und behoben

Die erste W3-Mutation war auf **eine Zeile** verankert (`if field not in fields:`), und dieselbe
Zeile steht weiter oben in `_assert_origins_resolve`. Zwei Folgen, beide gemessen: der Test blieb
grün, also hätte ich einen unbewiesenen Fix übergeben; und ein Lauf des Rigs aus dem falschen
Arbeitsverzeichnis schrieb die Mutation in **`AgentAndSkills/team-kits/kernel/state.py`**.
Beides ist behoben: die Mutation ist auf die Schleife verankert, das Rig verweigert seit
`mutate3.apply` jeden Lauf außerhalb seines eigenen Verzeichnisses, und die Änderung im Hauptrepo
ist zurückgenommen — `git diff --exit-code -- team-kits/kernel/state.py` ist dort leer, die Datei
ist byte-identisch mit `HEAD`. Kein `git restore`, `checkout` oder `stash` benutzt: die eine
Ersetzung wurde gezielt rückgängig gemacht.

### Läufe der Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `tools/test_report test_state test_backlog_types test_parallel_scopes test_kernel test_approvals_dispatch test_repo_hygiene` | 568 passed, 2 failed (4:01) → beide behoben bzw. bekannt: `out_of_band_hand_edit` (Wortfolge, nachgezogen) und der DEC-0064-Zeiger (§5) |
| dieselben Suiten nach dem Nachziehen, gezielt | grün |
| `tools/test_hooks.py -k "plan_approval_does_not_close or gate_git or memory_complete or …"` | 119 passed, 4 failed — genau die vier bekannten Naht-Roten aus §5 |
| `python -m ruff check .` | grün |
| `python tools/validate.py` | „all structural checks passed" |
| Spiegel | `gate_approval.py` 3×, `gate_git.py` 2× byte-identisch (diese Nacharbeit fasst keine Haken an) |
| Stempel | **2026.09.03-5** |

---

## 12. Nacharbeit 2

Rot-zuerst wie zuvor in `_round-scratch/TSK-0117/rw1/` (Mutationen W6, W7), je einzeln gefahren
und zurückgesetzt.

### M (blockierend) — das Edit-Verb las das Datumsfeld gar nicht

**Ursache.** Die Datumsprüfung und die Normierung standen in `capture_preflight`/`capture`;
`_update_item_locked` rief keines von beiden. Eine Regel, die nur eines von zwei schreibenden
Verben durchsetzt, hat eine zweite Tür.

**Fix.** Eine Funktion, drei Aufrufstellen, keine Kopie: `state._dates_in(item_type, fields,
operation)` verweigert, was `normalised_date` nicht lesen kann, und GIBT die kanonischen Werte
zurück. `capture_preflight` ruft sie als Verweigerung, `capture` schreibt ihr Ergebnis, und
`_update_item_locked` ruft dieselbe Funktion — **vor** dem Hashed-Field-Vergleich, damit ein
Neuschreiben desselben Tages keine Änderung ist. Das Verb steht im Verweigerungstext, weil eine
Rolle ihn mitten im Befehl liest.

**Gemessen als Prozess** (`_round-scratch/TSK-0117/w2_update.py`, `kernel.cli … update`):

```
captured: MST-0001 '2026-12-25'
update {"due": "Weihnachten"}  rc=1  stored='2026-12-25'  update MST: due is 'Weihnachten', which is not a calendar date…
update {"due": null}           rc=1  stored='2026-12-25'  update MST: due is None, which is not a calendar date…
update {"due": "20261225"}     rc=0  stored='2026-12-25'  MST-0001 PLANNED rev 1
update {"due": "2026-12-31"}   rc=0  stored='2026-12-31'  MST-0001 PLANNED rev 1
```

Die dritte Zeile trägt beide Hälften: normiert gespeichert **und** die Revision bleibt stehen —
dieselbe Schreibweise eines Tages ist keine Änderung.

**Rot ohne den Fix (W6):** `tools/test_state.py::test_the_update_path_reads_a_date_field_exactly_as_capture_does`.
Der Test prüft zusätzlich, dass ein verweigertes `update` den Datensatz unangetastet lässt.

**H147 ist danach wahr gemacht.** Die drei absoluten Sätze („genau eine Schreibweise", „allein die
Frage, ob eine Eingabe durchkommt", „der gespeicherte Datensatz bleibt lesbar") sind ersetzt: der
Eintrag nennt jetzt die Bedingung — beide Verben lesen **denselben** Leser, also gilt die eine
Schreibweise für alles, was durch sie in den Speicher kommt —, zitiert die Messung, die die alte
Fassung widerlegte, und benennt als weiterhin unbegrenzt einen Schreiber **außerhalb** dieser
beiden Verben (Handedit, Import).

### N1 — die Naht wurde ungefaltet verglichen

**Ursache.** Nur der `matcher`-Wrapper faltete; `scope_entries` nicht. `pair_seam` schneidet die
beiden `seam_scope`-Listen als rohe Zeichenketten, also war `["Docs/**"]` gegen `["docs/**"]` keine
gemeinsame Naht. Das fiel fail-closed aus (rc 2, kein Loch), aber der Leser bekam „ihr überlappt"
statt „eure Naht ist zweimal verschieden geschrieben" — eine andere Reparatur.

**Fix.** Die Faltung sitzt jetzt an der Tür (`scope_entries` ruft das ausgelieferte `_norm`), also
bedient sie alle drei Felder — `allowed_scope`, `forbidden_scope`, `seam_scope`. Eine Schreibweise
eines Pfades ist damit überall in diesem Modul ein Eintrag.

**Rot ohne den Fix (W7):** `tools/test_parallel_scopes.py::test_a_seam_the_two_orders_spell_differently_is_still_one_seam`
(rc 0 „seam only" statt rc 2), mit der Gegenprobe, dass dasselbe Paar **ohne** Deklaration
weiterhin rc 2 ist.

### N2 — das Rot-Rig konstruiert seine Pfade

`rw1/mutate3.py` prüfte die Position per `assert os.getcwd() == HERE` — ein `-O`, eine Verknüpfung
oder ein Aufrufer ohne `chdir` hätten das aufgehoben. Es baut den Pfad jetzt aus dem eigenen
Verzeichnis (`os.path.join(HERE, *relative.split("/"))`), kann also gar nicht mehr außerhalb
landen. Zugleich liest und schreibt es mit `newline=""`: der Textmodus war die Ursache dafür, dass
`state.py` im Hauptrepo auf CRLF umgeschrieben wurde.

### N3 — Kenntnis für die Merge-Runde (TSK-0120)

`kernel/scopes.py` und D's Werkstatt-Werkzeug `tools/check_scope_overlap.py` stimmen in **Prädikat**
und **Regel** überein und unterscheiden sich in der **Eingabe**: D nimmt die Naht nur von der
Kommandozeile, der Kernel zusätzlich aus dem Itemfeld `seam_scope`. Ein Schnitt, der seine Naht am
Item deklariert, ist für D's Werkzeug daher unsichtbar — es meldet dasselbe Paar als Kollision, das
das Kernel-Verb als „seam only" führt. Das ist keine Abweichung im Urteil, sondern in dem, was
gelesen wird; welche der beiden Oberflächen bleibt, entscheidet die Merge-Runde.

### Läufe der Nacharbeit 2

| Lauf | Ergebnis |
|---|---|
| `tools/test_state test_backlog_types test_parallel_scopes` | **116 passed** |
| `tools/test_kernel test_report` | **246 passed** |
| `tools/test_repo_hygiene -k "hole or test_pointer"` | 4 passed |
| `python -m ruff check .` | grün |
| `python tools/validate.py` | „all structural checks passed" |
| Stempel | **2026.09.03-6** |

---

## 13. Abschluss nach dem PASS: Zeilenenden des Worktrees, und die zweite Restklasse von H148

### (1) Der Worktree trägt jetzt LF — wie `.gitattributes` es vorschreibt

**Was falsch war und woher.** `.gitattributes:10` sagt `* text=auto eol=lf` seit BUG-0025, und
jede Entsprechung im Hauptrepo ist LF. Mein Mutations-Rig las und schrieb anfangs im TEXTMODUS,
und der übersetzt unter Windows jedes `\n` beim Schreiben in `\r\n` — nicht nur die geänderte
Zeile, sondern die ganze Datei. Meine spätere Anweisung, „die Konvention dieses Checkouts" sei
CRLF, war damit falsch: es war die Nachwirkung meines eigenen Werkzeugs.

**Was das für die Lieferung bedeutete: nichts** — und das ist gemessen, nicht angenommen. `git
diff` normalisiert auf dem Weg nach draußen, der Patch war schon vorher reines LF, und der
Prüfer hat ihn gegen einen LF-Checkout angewendet. Vor und nach der Normierung ist er
**byte-identisch** (229 448 B, 0 × CRLF, sha256 `11417108719e…`).

**Was normalisiert wurde, gemessen:**

| | |
|---|---|
| geänderte/neue Dateien des Worktrees | 25 (24 im Patch + `project_memory/.audit/hook_events.jsonl`) |
| davon mit CRLF | **21** |
| entfernte Bytes | **50 564** (= Zahl der CRLF-Paare) |
| größte Einzeldatei | `tools/test_hooks.py` 1 009 367 → 992 188 B (17 179 CRLF; hatte zusätzlich 34 einzelne LF, war also gemischt) |
| kleinste | `team-kits/kernel/scopes.py` 18 766 → 18 419 B |
| unberührt geblieben | 4 Dateien, die schon LF trugen (drei `VERSION`, `kernel/sdk_approval.py`) |

**Binärdateien wurden NICHT angefasst, und das ist eine Eigenschaft und keine Endungsliste:**
entschieden wurde an den Bytes (dekodierbar als UTF-8 **und** kein `\x00`), weil eine PNG oder
eine woff2 zufällig `\r\n` enthalten kann. In diesem Baum tun das **2 071** Dateien — eine
Endungsliste hätte sie irgendwann erwischt und eine Schriftdatei zerstört.

**Die drei Nachmessungen, alle unverändert:**

| Messung | vorher | nachher |
|---|---|---|
| `git diff --stat` (ohne die Audit-Datei) | 24 files, 2859 insertions, 131 deletions | identisch |
| `kit_hash` dev / office / research | `37960b6d…` / `4f430983…` / `94ae9412…` | **identisch** (`kernel.hashing.kit_hash` normalisiert CRLF selbst, wie `.gitattributes` es im eigenen Kommentar behauptet — hier nachgemessen) |
| Spiegel | `gate_approval.py` 3×, `gate_git.py` 2× byte-identisch | identisch (neue Prüfsummen, weil die Bytes LF sind) |
| Stempel | 2026.09.03-6 | unverändert (`bump_kit_version.py`: „unchanged") |

Danach: `ruff` grün, `validate.py` grün, `test_parallel_scopes` + `test_state` 70 passed.
Kein geändertes File des Worktrees trägt noch CRLF (gemessen: „none").

**Der Patch nach der H148-Ergänzung:** 231 318 B, 0 × CRLF, sha256 `e3ab4ceac6b0…`,
24 Dateien / +2879 / −131.

### (2) H148 — die zweite Restklasse

`pair_seam` schneidet **Zeichenketten**, während `_matches` **Dateimengen** vergleicht. Seit
Nacharbeit 2 ist die Groß-/Kleinschreibung gefaltet, die Form-Differenz bleibt: `docs/`
(normalisiert zu `docs`) und `docs/**` sind demselben Prädikat dieselbe Menge und der Naht zwei
Angaben. Gemessen (`_round-scratch/TSK-0117/n4_seamspell.py`, `check-scopes` als Prozess):

| Naht der beiden Aufträge | Prädikat über `docs/x.md` | Urteil |
|---|---|---|
| beide `docs/**` | — | rc 0, `disjoint` |
| `docs/` vs `docs/**` | beide **True** | **rc 2**, gewöhnliche OVERLAP-Meldung |

**Kein Loch, sondern eine schlechtere Auskunft:** die Richtung ist fail-closed — die Naht zählt
nicht, das Paar bleibt eine Kollision, niemand bekommt eine Erlaubnis, die er nicht deklariert hat.
Was fehlt, ist der Satz: der Leser hört „ihr überlappt" und sucht eine Datei, die er aus einem
Scope nehmen soll, während dieselbe Naht zweimal verschieden geschrieben dasteht. Der Fix wäre, die
Naht als MENGE zu schneiden; er ist nicht gebaut, weil er dieselbe Abwägung trifft wie die erste
Restklasse — `team-kits/*/VERSION` deckt `team-kits/dev-team/VERSION` mengenmäßig ab, und ob das
eine gemeinsame Naht oder eine einseitig breitere ist, entscheidet keine Mengenrelation.
Eintrag und Übersichtszeile von `H148` tragen beides.
