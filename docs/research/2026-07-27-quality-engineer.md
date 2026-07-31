# Rolle `project-manager` — Standardsabgleich (dev-team, research-team, office-team)

Gelesen: `docs/HARNESS_V2_SPEC.md` II.2/II.4/II.5/II.10a/II.11, `team-kits/dev-team/skills/project-manager/SKILL.md` (220 Z.), `team-kits/research-team/skills/project-manager/SKILL.md` (178 Z.), `team-kits/office-team/skills/office-manager/SKILL.md` (87 Z.), `team-kits/dev-team/constitution/AGENTS.md` (220 Z.), sowie zur Prüfung der Behauptungen `team-kits/kernel/{state,dispatch,report,backlog_types,cli}.py`.

---

## 1. Was die SKILL.md heute gut macht

**(a) Der Work-Order-Vertrag ist bereits der publizierte Stand der Technik — und er ist erzwungen.**
Zitat Schritt 6: *„The judgement is yours in four: `acceptance_refs` (the criteria this task is measured against), `required_inputs` (exact files/IDs — never 'read the tasks', name them), `allowed_scope`/`forbidden_scope`, and `design_ref`"*.
Das ist punktgenau Anthropics eigener Befund aus dem Multi-Agent-Research-System: *„Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."* Der Unterschied zum Blogpost: hier ist es kein Ratschlag, sondern `REQUIRED_FIELDS["TSK"]` + `TSK_PLAN_FIELDS` (eingefroren außerhalb `DRAFT`) + `gate_dispatch`. Und die Referenzen werden **aufgelöst**, nicht auf Nichtleere geprüft (`dispatch.py:280 ff.`, `_known_acceptance_ids_locked`) — `design_ref: TBD` fällt durch. Das ist besser als alles, was Jira/Azure DevOps anbieten.

**(b) Es existiert bereits ein echtes, mechanisches WIP-Limit — im Kanban-Sinn.**
Zitat: *„NEVER start a second user-visible PR while one is `DELIVERED` and not yet user-`ACCEPTED` … the state validator blocks the rest."* Das stimmt: `report.py:_check_ui_delivery_sequence` erzeugt ein `severity: error`-Finding, das `gate_memory_complete` in einen Merge-Block übersetzt. Das ist ein WIP=1 auf der user-sichtbaren Achse, mit `class: technical_enabler` als bewusstem Ventil. Der Kanban Guide verlangt „a definition of how WIP will be controlled" als Pflichtbestandteil der Definition of Workflow — dieser eine Punkt erfüllt ihn.

**(c) Der Test-Scoping-Ladder deckt sich mit DORAs Batch-Size-Befund**, und die entscheidende Klausel ist die richtige: *„partial tests are not merge evidence"* (II.10a) plus *„The full suite runs ONCE per slice END … the merge/push gate stays the untouchable guarantee."*

**(d) Handover-Ehrlichkeit = End-State-Evaluation.**
*„NEVER tell the user a PR is 'ready to test' while any `real_run` / documented first-run evidence is missing or was SKIPPED"* und der Bundle-Hash-Abgleich vor jedem „bitte durchklicken". Anthropic beschreibt exakt diesen Wechsel zu *end-state evaluation rather than turn-by-turn analysis*, und MAST-Kategorie 3 („Task Verification", 21,3 % aller beobachteten Fehlschläge, davon FM-3.2 *No or incomplete verification*) ist genau der Fehler, den diese Regel adressiert.

**(e) Der Retro-Absatz sagt, was er NICHT kann.**
*„And know what retro CANNOT tell you: the index is a snapshot, not a counter, so per-task retry COUNTS exist nowhere in V2 — if you need them, raise an FR."* Das ist die seltenste Qualität in solchen Dokumenten und der Grund, warum die Lücken unten überhaupt sauber benennbar sind.

**(f) Circuit-Breaker gegen MAST FM-1.3/FM-3.1.** Verfassung §14a: erster QA-FAIL setzt `escalation: true`, nach 3 Zyklen STOP; toter Spezialist → genau ein Retry. Das adressiert *Step repetition* und *Premature termination* — allerdings nur als Prosa (siehe G7).

**(g) Kontextführung folgt Cognitions Empfehlung.** *„After each PR merge, propose a FRESH session"* + Single-Writer-Kernel + *„Serialize agents that edit the same files"*. Cognition (Devin): *„Multi-agent systems work best today when writes stay single-threaded."*

---

## 2 + 3. Lücken gegen publizierte Standards — je mit GATE/SKILL-Verdikt

### G1 — Keine einzige Flow-Metrik ist definiert (Kanban Guide macht vier verpflichtend)

Ein `grep` über `team-kits/**` und `scripts/**` findet **null** Treffer für WIP, cycle time, throughput, work item age, lead time. Der [Kanban Guide (Mai 2025)](https://kanbanguides.org/the-kanban-guide/2025.5/) definiert vier Pflichtmetriken: WIP („number of work items started but not finished"), Throughput, **Work Item Age** („elapsed time between when a work item started and the current date"), Cycle Time.

Der harte Befund: **die Rohdaten liegen bereits im State.** `state.py:293` setzt `created` auf jedem Item, `dispatch.py:130/488/533` setzt `leased_at`/`started`/`completed` am TSK, `state.py:399` setzt `closed_at` beim Archivieren. Zwei Löcher verhindern die Nutzung:
1. **`transition()` schreibt keinen Zeitstempel** (`state.py:368-383` setzt nur `item["status"]`). PR-Cycle-Time (`APPROVED`→`DELIVERED`) ist damit nicht rekonstruierbar.
2. **Die Index-Zeile trägt `created` nicht** (`state.py:431-439`: id/type/title/status/revision/approval_ref/blocked_by). `retro.py` liest bewusst nur den Index — kann also Work Item Age prinzipiell nicht berechnen.

**Verdikt: GATE + SKILL, getrennt.**
- **GATE (Instrumentierung + Aging-Warnung):** `created` in die Index-Zeile; `status_history: [{to, at}]` append in `transition()`. Dann ein Validator-Check: *ein `PR`/`RQ` in `IN_DELIVERY` oder ein `TSK` in `LEASED`/`IN_PROGRESS`, dessen Alter das 85. Perzentil der archivierten Items desselben Typs überschreitet* → **`severity: warning`**, nicht `error`. **Wie es scheitert:** `harness validate` meldet `PR-0007: IN_DELIVERY seit 11 Tagen; 85. Perzentil der letzten 20 abgeschlossenen PRs = 3 Tage`. Warnung statt Block, weil eine Service Level Expectation eine Wahrscheinlichkeitsaussage ist — ein Block darauf wäre ein Scheingate.
- **SKILL:** die *Deutung* („aging ist ein Frühindikator, Cycle Time ein Nachlaufindikator") gehört in Prosa und darf nicht so klingen, als würde sie erzwungen.

### G2 — `priority` ist Pflichtfeld ohne Vokabular und ohne Leser

`REQUIRED_FIELDS["PR"]` verlangt `priority`; `_CLOSED_VOCABULARY` kennt nur `TSK.type`, `EVD.kind`, `EVD.result`. Kein Gate liest `priority`. Damit ist es Zeremonie — genau das, was der Kernel-Kommentar sonst vermeidet („Anything not listed here is free-form by intent").

**Verdikt: GATE (klein) — oder ehrlich streichen.** Geschlossenes Vokabular `must|should|could` (MoSCoW, DSDM) **nur dann**, wenn ein Gate es liest — z. B. der Aging-Check aus G1 wertet `must`-Items strenger. **Wie es scheitert:** `unknown PR priority 'hoch'. Remedy: use one of could, must, should`. Liest es niemand, ist die richtige Antwort: aus `REQUIRED_FIELDS` entfernen. WSJF/Cost of Delay empfehle ich **nicht** — die Zahlen wären in einem Ein-Personen-Projekt frei erfunden.

### G3 — Kein Batch-Size-Kriterium, obwohl das der eine DORA-Hebel ist, den KI verschärft

[DORA „Working in small batches"](https://dora.dev/capabilities/working-in-small-batches/): Batches sollen „in hours to a couple days" fertig sein; *„any batch of code that takes longer than a week to complete and check is too big"* — und DORA verweist dafür explizit auf [INVEST](https://xp123.com/invest-in-good-stories-and-smart-tasks/). Der [2024er DORA-Report](https://dora.dev/research/2024/dora-report/) misst: +25 % KI-Adoption → −1,5 % Throughput und −7,2 % Delivery-Stabilität; die benannte Ursache ist wachsende Batch-Größe ([Zusammenfassungen mit den Zahlen: RedMonk](https://redmonk.com/rstephens/2024/11/26/dora2024/), [DX](https://getdx.com/blog/2024-dora-report/) — die Prozentwerte stehen im PDF, nicht auf der Reportseite). Der [2025er Report](https://dora.dev/dora-report-2025/) bestätigt: KI ist ein *Verstärker*, die Instabilität bleibt.

Im Harness steuert `class: small|normal|large` **nur die Agentenkette**, ausdrücklich nicht die Größe („it reduces agent chains, never the persistence or approval duty"). Es gibt kein „zu groß".

**Verdikt: GATE — aber nur in der ehrlich messbaren Form.** „PR zu groß" ist vorab nicht messbar; **Alter** und **Diff-Umfang beim Merge** sind es. Konkret: `gate_git` warnt (nicht blockt), wenn der zu mergende Diff gegen `main` mehr als N geänderte Dateien/Zeilen umfasst, N aus `project_config.yaml`. **Wie es scheitert:** `merge of pr/PR-0012-checkout touches 84 files / 3.1k lines — DORA batch-size guidance is hours-to-days; consider splitting or record a Decision item`. Die *Entscheidung* zu schneiden bleibt SKILL (INVEST ist Urteil, kein Test).

### G4 — Evidence↔AC ist nur in **einer** Richtung maschinell geprüft

Vorwärts (Task → Kriterien) ist hart: `dispatch.py` löst `acceptance_refs` gegen die AC-IDs der `derives_from`-Kette auf und blockt bei Unbekannten. Rückwärts (Beleg → Kriterien) ist **Prosa**: SKILL Schritt 7 verlangt Evidence, *„whose summary names the acceptance criteria and invariants it covers"* — `REQUIRED_FIELDS["EVD"]` kennt aber nur `kind, related, result, summary, artifact_refs`. Ein `summary: "alles grün"` erfüllt das Feld und öffnet über `gate_git` den Merge.

Das ist die Asymmetrie, die MAST-Kategorie 3 vorhersagt (*No or incomplete verification*, [arXiv:2503.13657](https://arxiv.org/abs/2503.13657)), und sie steht im Widerspruch zum eigenen Versprechen der Verfassung §2.4. Der [Scrum Guide 2020](https://scrumguides.org/scrum-guide.html) macht die Definition of Done zum *Commitment* des Increments — ein Commitment, das nur in Freitext existiert, ist keins.

**Verdikt: GATE.** Neues Feld `EVD.covers: [<AC-id>, …]`, aufgelöst wie `acceptance_refs` heute. Merge-Gate: *jedes `acceptance_criteria`-Item des Root-PR ist von mindestens einer aktuellen `pass`-Evidence in `covers` genannt.* **Wie es scheitert:** `merge refused for PR-0012: acceptance criteria AC-3, AC-5 are covered by no passing evidence (newest test EVD-0044 covers AC-1, AC-2, AC-4)`. Zusatznutzen: es entwertet den Trick, eine Evidence für einen Nachbar-PR als Nachweis zu recyceln.

### G5 — Backlog-Hierarchie: die fehlende Achse ist nicht Epic, sondern *Area Path*

[Jira](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/) hat per Default drei Ebenen (Epic/Story/Subtask; mehr nur in Premium). [Azure DevOps Agile](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process) hat vier (Epic→Feature→User Story→Task) **plus zwei orthogonale Achsen**: [Area Path und Iteration Path](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/about-areas-iterations).

Der Harness hat PR→SR→TSK — strukturell Jira-Default. **Eine vierte Ebene verdient sich hier nichts:** `product/masterplan.md` spielt bereits „Initiative", und Iteration Path/Sprints haben in Agentenarbeit keinen Takt, den sie abbilden könnten (Kanban statt Scrum ist hier die richtige Wahl). **Was sich verdient, ist Area Path** — die Bereichsachse. Sie existiert im Harness implizit (`SR.affected_components`, `TSK.allowed_scope`, `testing_guidelines.yaml: coverage_areas`), aber nirgends als eine Achse.

Der konkrete Hebel: `dispatch.py:431` blockt bereits zwei gleichzeitige Dispatches **derselben Rolle** (`AmbiguousBinding`). **Zwei verschiedene Rollen mit überlappendem `allowed_scope` sind nicht geblockt** — und genau das ist der in der SKILL dokumentierte Vorfall: *„parallel fixers plus a temp-edit agent raced on one file in a real run (commit collision, repaired by luck)"*. Die Regel *„same-file work is sequential"* ist heute reine PM-Prosa.

**Verdikt: GATE.** `dispatch` verweigert eine Lease, wenn ein aktiver Lease einen Task mit überlappendem `allowed_scope` hält. **Wie es scheitert:** `TSK-0031 (devops-engineer, scope: src/api/**) overlaps the live lease of TSK-0029 (backend-developer, scope: src/**) — dispatch refused; run them sequentially or narrow the scope`. Kosten praktisch null: `allowed_scope` existiert, ist außerhalb `DRAFT` eingefroren und ist ohnehin schon der einzige Input von `gate_write_scope`.

### G6 — Der 3-Fail-Circuit-Breaker ist nicht zählbar

Verfassung §14a nennt „nach 3 gescheiterten QA-Zyklen: STOP", und die SKILL sagt selbst, dass es die Zahl nirgends gibt. `transition()` zählt `FAILED → READY` nicht.

**Verdikt: GATE, hängt an einer Ein-Zeilen-Datenlücke.** Kernel-gesetzter `retry_count` beim `FAILED → READY` (der Pfad verlangt ohnehin schon `approved_retry=True`). **Wie es scheitert:** `TSK-0018: 4th retry requested; §14a caps at 3 — stop and report to the user, or record a Decision item overriding the cap`. Ohne den Zähler ist §14a eine Regel, die nur so lange gilt, wie das Modell sich erinnert — d. h. MAST FM-1.5 (*Unaware of termination conditions*).

### G7 — `blocked_by` altert unsichtbar

`blocked_by` steht in der Index-Zeile, aber ohne `blocked_since`. Ein seit Wochen blockiertes Item ist genau Vacantis „aging WIP" ([Scrum.org zur Herkunft der Metrik](https://www.scrum.org/resources/blog/detecting-flow-issues-using-predictive-cycle-time-charts-origin-kanbanflow-work-item-aging-metric)).
**Verdikt: GATE (warning), Teil von G1** — `blocked_since` beim Setzen des Flags; Validator warnt ab Schwelle. **Wie es scheitert:** `TSK-0022 blocked_by TSK-0019 since 9 days — the blocker is CANCELLED`.

### G8 — Kein Metrik-Kommando, keine Flow-Sicht im Dashboard

`harness` kennt heute: `doctor, validate, generate-index, generate-session-brief, evidence, transition, archive, sweep-leases`. Kein `metrics`.
**Verdikt: GATE-nah (read-only Reporting) + SKILL.** Ein `harness metrics --since 30d`, das WIP, Throughput, Cycle-Time-Perzentile und die Aging-Liste ausgibt — read-only, wie `doctor`. Die **Interpretation** bleibt SKILL, mit einem ausdrücklichen Goodhart-Absatz (siehe §5).

---

## 4. Die drei Ergänzungen mit dem höchsten Hebel, in Reihenfolge

**1. `EVD.covers` + AC-Abdeckungsgate im Merge (G4).**
Warum zuerst: Es schließt die Lücke zwischen dem *zentralen Versprechen* des Harness („kein Merge ohne Beweis") und dem, was mechanisch geprüft wird. MAST beziffert die Verifikationskategorie mit 21,3 % aller Fehlschläge, und sie ist die einzige, gegen die ein Lead strukturell etwas ausrichten kann.
*Kosten:* ein Feld in `REQUIRED_FIELDS["EVD"]`, ein `--covers`-Flag an `harness evidence` (analog `--related`), eine Wiederverwendung von `_known_acceptance_ids_locked`, eine Prüfung in `gate_git`, ~4 Tests. **Migrationsrisiko:** bestehende EVD-Items sind unveränderlich (`IMMUTABLE_TYPES`) — `covers` muss deshalb bei `capture` optional starten und erst im Merge-Gate verlangt werden, sonst blockiert das Gate rückwirkend auf Altbestand. Das ist die einzige nicht-triviale Stelle.

**2. Scope-Overlap-Block im Dispatch (G5).**
Warum zweitens: billigste echte Absicherung im Katalog, ersetzt eine SKILL-Prosaregel eins zu eins durch ein Gate und schließt einen dokumentierten Realvorfall. Cognition und Anthropic stützen die Regel beide.
*Kosten:* ein Pfad-Präfix-Vergleich über die aktiven Leases in `dispatch.py`, kein neues Feld, keine Migration, ~3 Tests. Eine halbe Stunde Arbeit. **Nebenwirkung:** legitime Parallelarbeit mit weit gefasstem `allowed_scope` (`src/**`) wird künstlich serialisiert — die Fehlermeldung muss „narrow the scope" nennen, sonst erzieht das Gate zu breiteren Scopes statt zu engeren.

**3. Zeit in den Index + `status_history` + `harness metrics` + Aging-Warnung (G1/G6/G7).**
Warum drittens: Es blockt nichts, aber ohne es sind alle Flow-Aussagen — und `retro.py` in seiner heutigen Form — blind. Es ist die Voraussetzung dafür, dass Batch-Size (G3) und der Retry-Cap (G6) überhaupt messbar werden.
*Kosten:* 2 Zeilen in `_regenerate_index_locked`, 3 Zeilen in `transition()`, ein neues read-only CLI-Kommando (~150 Zeilen, Muster `doctor`), Erweiterung von `retro.py` und `generate_dashboard.py`. **Risiko:** `status_history` wächst im Item — das Budget „aktives Item ≤200 Zeilen/12 KB" (II.5) muss mitgedacht werden; ein Item mit 40 Transitionen ist ein Item, das anderswo falsch läuft, aber das Gate würde am falschen Ort feuern. Kappen bei den letzten N Einträgen, Rest liegt in Git.

---

## 5. Was **gegen** populäre Empfehlungen für diese Rolle spricht

**Gegen „DORA-Vier-Keys ins Dashboard".** dora.dev warnt selbst: *„Setting metrics as a goal"* ignoriert Goodharts Gesetz, und die Metriken sind *„meant to be applied at the application or service level"* — nicht für Teamvergleiche. In einem Ein-Personen-Projekt ohne Produktion sind Deployment Frequency, Change Failure Rate und Recovery Time schlicht nicht definiert (kein Deployment, keine Incidents, n zu klein). Übertragbar sind **Batch Size** und **Lead Time**, nicht die vier Keys als Scoreboard. Ein Dashboard mit vier DORA-Kacheln wäre Cargo-Kult. Ergänzend: DORA hat 2025 die vier Performance-Tiers durch sieben Team-Archetypen ersetzt — die „Elite/High/Medium/Low"-Einordnung, die man überall zitiert findet, ist nicht mehr der Stand.

**Gegen Story Points und Velocity.** Weder der Kanban Guide noch DORA messen Punkte; der Kanban Guide sagt ausdrücklich, Throughput sei *„the exact count of work items"*. Es gibt keine mir bekannte primäre Quelle, die Velocity Vorhersagekraft zuschreibt. Schätzung in diesen Harness einzubauen hieße, ein Pflichtfeld hinzuzufügen, das kein Gate lesen kann — genau der Fehler, den `priority` heute schon macht (G2).

**Gegen eine „Definition of Ready" als Checkliste.** [Scrum.org führt DoR in seiner Anti-Pattern-Taxonomie](https://www.scrum.org/resources/blog/scrum-anti-patterns-taxonomy): Phase-Gate, falsche Klarheit, weniger Gespräch. Wichtig für diesen Harness: `gate_dispatch` **ist** bereits ein DoR — aber ein legitimer, weil er *auflösbare Referenzen* prüft, nicht „genug Detail". Diese Grenze darf nicht verwischt werden. Ein Gate, das „acceptance_criteria sind klar genug" behauptet, wäre eine Geschmacksfrage in Gate-Kleidung. Die neun Qualitätsmerkmale aus [ISO/IEC/IEEE 29148](https://www.iso.org/standard/72089.html) (u. a. *unambiguous, singular, verifiable*) gehören deshalb in die **SKILL**, nicht in den Validator — mit einer Ausnahme, die tatsächlich mechanisch ist: *singular* lässt sich als „ein AC-Text enthält kein ' und ' / ' and ' auf oberster Ebene" annähern, und selbst das würde ich nur als Warnung führen.

**Gegen „METR beweist, dass Agenten langsamer machen".** Die viel zitierte RCT (16 Entwickler, 246 Tasks, 19 % langsamer bei 20 % gefühlter Beschleunigung, [METR 2025-07-10](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)) wird von METR selbst inzwischen als historisch markiert; im [Februar-2026-Update](https://metr.org/blog/2026-02-24-uplift-update/) hat METR das Studiendesign geändert, weil die Folgedaten durch Selektionseffekte nicht interpretierbar waren. Auf dieser Studie sollte keine Harness-Regel stehen. Was bleibt und robust ist, ist die *Wahrnehmungslücke* — und die stützt die bestehende Handover-Ehrlichkeitsregel, nicht eine Metrik.

**Gegen mehr Parallelität.** [Cognition rät generell davon ab](https://cognition.com/blog/dont-build-multi-agents) (*„just use a single-threaded linear agent"*); [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system) berichtet Erfolg mit Fan-out ausschließlich bei **lesender** Recherche und benennt „compounding errors" und unvorhersehbare Kopplung. Die bestehende Regel des Harness — Parallelität nur bei disjunkten Dateien, Kernel als einziger Schreiber — ist die durch beide Primärquellen gedeckte Mitte. Eine Empfehlung „mehr Agenten parallel für Tempo" wäre gegen die Quellenlage.

**Gegen eine Epic-Ebene über dem PR.** Jira braucht dafür Premium, Azure DevOps hat sie für Organisationsmaßstab. Bei einem Team und einem Nutzer erfüllt `product/masterplan.md` diese Funktion bereits — und es ist ausdrücklich ein eingefrorenes Discovery-Artefakt ohne Status, was genau richtig ist: eine Epic-Ebene mit eigenem Statusautomaten hätte einen zweiten Ort für Projektstatus geschaffen, den II.2 sonst konsequent vermeidet.

**Dünne Adoption, ehrlich ausgewiesen:** Das [Flow Framework](https://flowframework.org/) (Kersten; Flow Velocity/Time/Efficiency/Load/Distribution) ist konzeptuell attraktiv — vor allem *Flow Distribution* (Feature vs. Defect vs. Risk vs. Debt), was hier fast gratis wäre, weil PR/BUG/CR/`technical_enabler` die vier Kategorien bereits sind. Aber die Belege sind überwiegend Anbietermaterial (Planview), nicht unabhängige Forschung. Ich würde es als **SKILL**-Zeile im Retro-Absatz führen („schau dir das Verhältnis PR : BUG : CR über die letzten Zyklen an"), nicht als Metrik im Dashboard.

---

**Sources:**
- [The Kanban Guide, Mai 2025](https://kanbanguides.org/the-kanban-guide/2025.5/)
- [DORA — Four Keys](https://dora.dev/guides/dora-metrics-four-keys/)
- [DORA — Working in small batches](https://dora.dev/capabilities/working-in-small-batches/)
- [DORA 2024 State of DevOps Report](https://dora.dev/research/2024/dora-report/) · [RedMonk-Analyse mit den Zahlen](https://redmonk.com/rstephens/2024/11/26/dora2024/) · [DX-Zusammenfassung](https://getdx.com/blog/2024-dora-report/)
- [DORA 2025 State of AI-assisted Software Development](https://dora.dev/dora-report-2025/)
- [Why Do Multi-Agent LLM Systems Fail? (MAST, arXiv:2503.13657)](https://arxiv.org/abs/2503.13657) · [Volltext mit den 14 Failure Modes](https://arxiv.org/html/2503.13657v2)
- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Cognition — Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents)
- [METR — Impact of Early-2025 AI on Experienced OSS Developer Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) · [Design-Änderung 2026-02](https://metr.org/blog/2026-02-24-uplift-update/)
- [Bill Wake — INVEST in Good Stories, and SMART Tasks](https://xp123.com/invest-in-good-stories-and-smart-tasks/)
- [The 2020 Scrum Guide](https://scrumguides.org/scrum-guide.html) · [Scrum.org — Scrum Anti-Patterns Taxonomy (Definition of Ready)](https://www.scrum.org/resources/blog/scrum-anti-patterns-taxonomy)
- [Scrum.org — Herkunft der Work-Item-Aging-Metrik (Vacanti)](https://www.scrum.org/resources/blog/detecting-flow-issues-using-predictive-cycle-time-charts-origin-kanbanflow-work-item-aging-metric)
- [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html)
- [Azure Boards — Agile process](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process) · [Area/Iteration Paths](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/about-areas-iterations)
- [Atlassian — Configure the work type hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/)
- [Flow Framework](https://flowframework.org/)