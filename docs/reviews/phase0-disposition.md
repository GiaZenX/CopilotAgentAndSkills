# Phase 0 — Dispositionsbericht (Vollinventar + Paritätsmatrix + Spikes)

**Status: ZUR USERBESTÄTIGUNG — Phase 1 startet erst nach Freigabe dieses Berichts**
(gemäß `docs/HARNESS_V2_SPEC.md` II.11/0 und II.12 „Phase-0-Abnahme")

**Datum:** 2026-07-24 · **Methodik:** read-only; 2 Opus-Inventar-Agenten (Teil 1: Root/dev-team/
tools/CI/.claude/radar/.codex · Teil 2: office/research/team-kits-Root/user), 1
Opus-Paritätsmatrix-Agent (24+ Dateien, 116 Regeln), 1 Claude-Code-Doku-Agent (Spikes S2/S3),
1 eigener empirischer Spike-Lauf (S1, Python 3.13.0/win32). Fable-Gegenprüfung dieses
Berichts folgt als Check 3 (Arbeitsmodus 2026-07-24).

**Kurzfazit:** 276 Dateien disponiert (274 git-getrackt + 2 verwaltete untracked
Provider-TOMLs) — 92 übernehmen · 140 anpassen · 43 durch V2-Mechanik ersetzt · **1 bewusst
entfernen** (`guard_ledger_direct.py`, User-Entscheid I.3/1). Lockstep-Menge: **80 Dateien**
(⚓) statt der v2.1-Schätzung ~76 — Differenz erklärt (Abschnitt 2). Paritätsmatrix: 116
Regeln klassifiziert, alle 9 Minimum-Keep-Items gedeckt, **13 Paritätsrisiken R1–R13** mit
Behandlungsvorschlag (Abschnitt 4 — dein wichtigster Entscheidungsblock).
**Spikes — Stand nach dem Amendment 2026-07-24 (alle drei empirisch entschieden, §5):**
**S1 verified** (6/6 Messungen), **S2b NEGATIV entschieden** (Transkript-Forensik:
Options-Identität existiert auf Claude Code 2.1.219 nicht → ersetzt durch den
Mint-Code-Mechanismus; Capability-Wert = offener Definitionsentscheid), **S3 verified
Ende-zu-Ende** (headless-Lauf: SubagentStart.agent_id == Kind-PreToolUse.agent_id, und
`PostToolUse(Agent).tool_response.agentId` vorhanden).

---

## 1. Vollinventar (276 Dateien)

| Disposition | Teil 1 | Teil 2 | Summe |
|---|---|---|---|
| übernehmen | 25 | 67 | **92** |
| anpassen | 56 | 84 | **140** |
| durch V2-Mechanik ersetzt | 20 | 23 | **43** |
| bewusst entfernen | 0 | 1 | **1** |
| **Summe** | **101** | **175** | **276** |

Zählabgleich: `git ls-files` = 274; + `.codex/agents/*.toml` (2, untracked, aber
generator-verwaltet) = 276. Keine weiteren verwalteten Dateien außerhalb von git
identifiziert.

### 1.1 Disposition Teil 1 — Root · .claude · .github · radar · dev-team · tools · .codex

⚓ = greift hart auf einen Monolith-Dateinamen zu (product_requirements/tasks/
system_requirements/design/progress/filing_log/architecture.yaml) → Lockstep.

**Wurzel:**

| pfad | disposition | begründung |
|---|---|---|
| .gitattributes | übernehmen | EOL-/Binär-Normalisierung ist V2-neutral und bleibt unverändert gültig. |
| .gitignore | übernehmen | Harness-Repo-Ignore (Caches, .e2e-sandbox, scheduled_tasks); kein Monolith-Bezug. |
| ⚓ HARNESS_LOG.md | übernehmen | Reines append-only Änderungsprotokoll; Monolith-Namen nur historisch, keine Enforcement-Kopplung. |
| ⚓ README.md | anpassen | Zentrale Doku wird auf V2 umgeschrieben (PR/RQ-Per-Item, kein progress.yaml/dashboard_history, draw.io-ARC/WFR, kit_state.json). **Konkret gemeldet 2026-07-26 (Lockstep-Gruppe „Repo-Skripte“, fremde Zeile):** Z. 308–312 beschreiben den Generator noch in seiner V1-Form (`progress.dashboard.html`, liest die Requirement-/Task-/CR-Monolithen, archiviert nach `dashboard_history/`, „was hat sich seit dem letzten Lauf geändert“) — real ist es `project_memory/generated/dashboard.html` aus `generated/index.yaml` + aktiven Items, ohne History und ohne Since-last-run-Diff; Z. 395–398 nennen `coding_guidelines.yaml file_budget:` als Konfigort, den diese Runde für heimatlos erklärt hat (siehe Zeile 189). |
| install.ps1 | anpassen | Grundmechanik (Backup/Merge) bleibt; braucht V2-Preflight (greenfield/V2/V1/mixed + Version-Pinning, II.10a). |
| install.sh | anpassen | POSIX-Zwilling — dasselbe V2-Preflight/Pinning. |
| ruff.toml | übernehmen | Lint-Baseline des Harness selbst; V2-neutral. |

**.claude/agents (Harness-eigene Watcher):**

| pfad | disposition | begründung |
|---|---|---|
| .claude/agents/codex-watcher.md | übernehmen | Read-only Wochen-Radar (Codex-Provider); kein Projekt-State-Bezug. |
| .claude/agents/radar-watcher.md | übernehmen | Read-only Wochen-Radar (Claude/Anthropic); keine Monolith-Kopplung. |

**.github:**

| pfad | disposition | begründung |
|---|---|---|
| .github/workflows/ci.yml | anpassen | Gerüst (ruff + validate.py + pytest) bleibt; erweitert um State-Kernel-/Dispatch-/Lock-/Latenz-Tests der II.12-Matrix. |

**radar:**

| pfad | disposition | begründung |
|---|---|---|
| radar/2026-07-03.md | übernehmen | Datierter Radar-Bericht, historisch, keine Enforcement-Funktion. |
| radar/2026-07-06.md | übernehmen | Historischer Bericht. |
| radar/2026-07-15-claude.md | übernehmen | Historischer Bericht. |
| radar/2026-07-17-claude.md | übernehmen | Historischer Bericht. |
| radar/README.md | übernehmen | Beschreibt Watcher-Prozess/Report-Shape; V2-neutral. |
| radar/decided.md | übernehmen | Append-only Triage-Log der Radar-Items. |

**team-kits/dev-team — Kern:**

| pfad | disposition | begründung |
|---|---|---|
| team-kits/dev-team/VERSION | anpassen | Bleibt Versions-/Hash-Stempel, wird im V2-Release neu gebumpt (II.11/4). |
| ⚓ constitution/AGENTS.md | anpassen | Umstellung auf V2-Zustandsmodell + Kürzung ≤150 Zeilen — Kürzung erst NACH Ersatz-Gates (II.5/II.11). **Nachtrag 2026-07-26 (Lockstep-Gruppe „Verfassungen/Agents/Skills“, Opus-Gegenprüfung):** die Umstellung war sprachlich vollständig, behauptete aber sechs Mechanismen, die der laufende Code nicht hat. Jetzt ehrlich gemacht statt weiterbehauptet: (a) NEUER §0-Punkt „state directory is WRITE-LOCKED today“ — `gate_write_scope` sperrt JEDEN Tool-Write unter `project_memory/` (auch die Referenz-/Configdateien, für die es keine Ausnahme kennt), es gibt kein `harness`-Executable und kein `capture`/`approve`/Freeze-Kommando, ein direkter Kernel-Aufruf wird vom selben Gate abgelehnt ⇒ heute kann in KEINEM Kit ein Item oder `project_config.yaml` entstehen; der Satz gilt für alle `harness …`-Nennungen der Datei. (b) `gate_git`-Zeile: nennt jetzt, dass der Hook einen V1-`*report*.yaml` verlangt und damit JEDEN merge/push blockt (letzte „PRD“-Stelle des Pakets entfernt). (c) `guard_guidelines`-Zeile + §2.7 konditional („nur solange das Projekt die Datei führt“). (d) `gate_test_coverage`-Zeile nennt `testing_guidelines.yaml` als Quelle der EXTRA-Areas. (e) §2.4 „no PR **leaves** DELIVERED“ → „REACHES“ + Vokabular auf `review`+`test`+`acceptance` vereinheitlicht. (f) §6 „ist CLOSED“ → „closed through its status automaton“ (`CLOSED` ist in `AUTOMATA` kein Status; office/research formulierten es schon richtig). (g) §9 „`ARC`/`WFR` haben keinen Automaten“ → Definition „nur die Typen in `AUTOMATA` haben einen“. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** CLI-Shim (`harness`, inkl. `capture`/`approve`/Freeze) + eine `gate_write_scope`-Ausnahme oder ein Nicht-kanonisch-Pfad für die Referenzdateien; solange beides fehlt, ist V2 ohne begehbaren Schreibweg. **Nachtrag 2026-07-26 (Gegenprüfung 2):** (h) der §0-Punkt deckte nur TOOL-Writes und den direkten Kernel-Aufruf; gemessen verweigert derselbe Gate über den `_ENFORCEMENT_RX`-Zweig auch JEDE schreibfähige Shell-Pipeline, die `.claude` oder `team-kits` NENNT — also die `init_project_memory`/`scaffold_team`-Aufrufe, die das Startup-Gate (Schritt 1) und §11/der Kit-Update-Absatz anordnen (rc=2, „names the enforcement layer in a pipeline that can write“). §0 nennt sie jetzt und weist sie dem USER zu. (i) §2 Item 2 sagte „No role writes a state file with an editor **or a shell** … `gate_write_scope` refuses it“; gemessen schreibt ein SKRIPT (`python scripts/oops.py`) ungehindert nach `product/active/` (rc=0, Datei entsteht) — genau darauf beruhen `scripts/retro.py` und `scripts/generate_dashboard.py`. Die Zeile sagt jetzt „jede Shell-Pipeline, deren KOMMANDOZEILE den Pfad nennt“ und benennt die Skript-Indirektion als offene Lücke. (j) §10 `premise_rechecks` sagt jetzt, dass das Feld am **PR/CR** hängt (nicht am DEC — `report.py:522` liest es nur dort). (k) die Auditor-Routine-Zeile ehrlich gemacht (siehe Zeile 100). |
| presets.yaml | übernehmen | Preset→Rollen-Mechanik unverändert gültig. |
| settings/settings.json | anpassen | Hook-Verdrahtung erhält gate_dispatch/guard_memory_budget + AskUserQuestion-Approval-Pfad; Stop-/PostToolUse-Regeneratoren entfallen (II.4). |

**team-kits/dev-team/agents** (geteilte Begründung: Rollenkörper überleben, werden auf den
V2-Flow umgestellt — Result-Envelope ≤4 KB statt Monolith-YAML-Ownership):

| pfad | disposition | begründung |
|---|---|---|
| agents/backend-developer.md | anpassen | s. geteilte Begründung. |
| agents/devops-engineer.md | anpassen | s. geteilte Begründung. |
| agents/frontend-developer.md | anpassen | s. geteilte Begründung. |
| ⚓ agents/product-designer.md | anpassen | + schreibt künftig WFR/DSN-Revisionen statt design.yaml (II.6a). |
| agents/project-auditor.md | anpassen | + Auditor als widerrufbare Routine-Freigabe, Befunde → Evidence/BUG (II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:66` `ROOT_DISPATCH_KINDS = {scope, delivery}`, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. |
| ⚓ agents/project-manager.md | anpassen | + Startup-Gate/Monolith-Reads auf Per-Item + kit_state.json. **Nachtrag 2026-07-26:** Startup-Gate-Schritt 3 („Write preset + maps into `project_config.yaml`“) war unausführbar — jetzt „have the kernel write … (blocked today, report it)“; + Verweis auf den §0-Write-Lock vor dem ersten Capture. **Nachtrag 2026-07-26 (Gegenprüfung 2):** die `init_project_memory`/`scaffold_team`-Aufrufe dieser Datei werden von `gate_write_scope` verweigert (gemessen rc=2: „names the enforcement layer in a pipeline that can write“, weil `_ENFORCEMENT_RX` auch `team-kits` matcht). Die Stellen sagen das jetzt und geben die Zeile an den USER — sonst testet ein PM im ersten Schritt eines frischen Repos die Runde-1-Lehre „report it, never work around it“. Siehe den erweiterten §0-Punkt (Zeile 87). |
| agents/quality-engineer.md | anpassen | + QA gegen AC/Invarianten, Belege als Evidence. **Nachtrag 2026-07-26 (mitgezogen, nicht ⚓):** `description` und Body sagten weiter „enforce the **Definition of Done** … produce the review/test/acceptance **reports**“ — beide Stores sind gelöscht und der eigene, von derselben Datei preloadete SKILL sagt in Schritt 5 ausdrücklich das Gegenteil. Jetzt Evidence-Items + „done = jedes AC/`INV` hat einen GENANNTEN Beweis“. Der Zwilling `research-team/agents/reviewer.md` („Definition of Validity“, `validity_criteria.yaml` ist gelöscht) gleich mitgezogen. |
| agents/research-engineer.md | anpassen | s. geteilte Begründung. |
| agents/software-architect.md | anpassen | + Mermaid→draw.io-ARC bewusst umgekehrt (II.6a). |

**team-kits/dev-team/hooks:**

| pfad | disposition | begründung |
|---|---|---|
| hooks/_audit.py | anpassen | Audit-JSONL-Helfer bleibt; + Log-Rotation ~1 MB außerhalb des Startkontexts (II.5). |
| hooks/_compat.py | anpassen | Provider-Adapter bleibt Kern; + agent_id-/Lease-Payloads und begrenztes stdin-Read (II.4). |
| hooks/_root.py | übernehmen | Cwd-fester Repo-Root-Resolver, provider-neutral. |
| ⚓ hooks/auto_dashboard.py | durch V2-Mechanik ersetzt | Stop-/PostToolUse-Regenerator entfällt: Index/Dashboard atomar im Kernel; Update-Nag → kit_state.json (II.4/II.7/II.8). **Präzisierung 2026-07-26:** der INDEX ist atomar im Kernel, das DASHBOARD nicht — einziger Produzent bleibt `scripts/generate_dashboard.py`, aufgerufen über die Verfassungs-Checkliste (§3). Der Wegfall des Stop-Hooks ist richtig, die Begründung war zu weit gefasst; die research-Lage steht in Zeile 379. |
| hooks/format_on_write.py | übernehmen | Komfort-Formatter, fail-open — bleibt zulässig (II.4). |
| ⚓ hooks/gate_git.py | anpassen | Force-Push-Sperre bleibt; PRD-\d-Regex → Branch↔Item + typgerechter Status, QA-Beleg via Evidence (II.10). |
| ⚓ hooks/gate_memory_complete.py | anpassen | Trigger → product/active/PR-*.yaml; Template-Vollständigkeit wandert in den State-Validator (II.12-Lockstep). |
| ⚓ hooks/gate_packaging_decision.py | anpassen | architecture.yaml aufgelöst; packaging.method → gate-lesbares schlankes Architektur-Item, Hook im selben Lockstep (II.6a/II.11/2). |
| ⚓ hooks/gate_pipeline.py | anpassen | Quality-Gate bleibt (Fast-Mode II.10a); PRD-Root-Trigger → PR-Per-Item. |
| hooks/gate_subagent_output.py | anpassen | Prüft künftig das Result-Envelope-Schema (II.5) statt Prosa-Keys summary/verdict. |
| ⚓ hooks/gate_test_coverage.py | anpassen | Per-Area-Testfloor bleibt; PR-Root-Trigger + coverage_areas-Quelle wandert (testing_guidelines→INV/Config). |
| hooks/guard_agent_spawn.py | anpassen | Bleibt Gate-Schicht 1; + HARNESS_DISPATCH-Header-Bindung zur Lease (II.4). |
| hooks/guard_guidelines.py | anpassen | „Kein Code vor Guidelines" bleibt; Quelle wandert von coding_guidelines.yaml auf INV/Per-Item. |
| hooks/guard_harness_selfmod.py | anpassen | Selbstschutz bleibt fail-closed; Schutzliste + kit_state.json, Kernel-Lock, generated/. |
| ⚓ hooks/guard_no_adhoc.py | anpassen | Single-Source-Guard bleibt; Zielverweise auf Per-Item-Typen statt Monolithe. |
| hooks/guard_pm_scope.py | übernehmen | „Orchestrator schreibt keinen Produktcode" — Kern-Invariante; agent_id-Mechanik vorhanden. |
| hooks/guard_question_context.py | übernehmen | Blockt Fragen mit unsichtbarem Kontext; koexistiert neben dem neuen Approval-Provenance-Pfad. |
| hooks/guard_scratchpad_ref.py | übernehmen | Reproduzierbarkeits-Guard, provider-neutral. |
| ⚓ hooks/guard_yaml_valid.py | anpassen | YAML-Wohlgeformtheit bleibt Komfort; harter progress.yaml-Branch (Z. 130) entfällt, Schema → State-Validator. |
| hooks/notify_agent_events.py | übernehmen | Lifecycle-Audit-Log; im audited-Modus Pflichtprotokoll (II.8). |
| ⚓ hooks/session_status.py | anpassen | Wird Update-Zustandsautomat + session_brief-Verweis; alle ~6 injizierten Blöcke disponiert → kit_state.json/generated (II.8). |

**team-kits/dev-team/skills** (geteilte Begründung: Prozedur auf V2 umgeschrieben und
gekürzt — Kürzung erst nach Ersatz-Gates, Paritätsmatrix-belegt; jede Datei referenziert
Monolithe):

| pfad | disposition | begründung |
|---|---|---|
| ⚓ skills/backend-developer/SKILL.md | anpassen | s. geteilte Begründung. |
| ⚓ skills/devops-engineer/SKILL.md | anpassen | s. geteilte Begründung. |
| ⚓ skills/frontend-developer/SKILL.md | anpassen | s. geteilte Begründung. |
| ⚓ skills/product-designer/SKILL.md | anpassen | + WFR/DSN-Pipeline statt design.yaml (II.6a). **Nachtrag 2026-07-26:** die beschriebene Freeze-Pipeline (`staging.freeze_wireframe`/`freeze_design`) hat KEINEN Produktionsaufrufer — nur Tests. Die Datei sagt das jetzt und weist die Rolle an, den STAGED Pfad zu nennen statt eine eingefrorene Revision zu behaupten. |
| ⚓ skills/project-auditor/SKILL.md | anpassen | + Routine-Freigabe/Evidence-Fingerprint (II.10a). **Nachtrag 2026-07-26:** der Fingerprint war in der ersten Runde NICHT geliefert (nur die Prosa „do not re-report unchanged findings“). Jetzt in allen drei Auditor-SKILLs definiert: `fingerprint` = sha256 über Art + Ort + Behauptung eines Befunds, Dedupe/Merge gegen den Fingerprint statt gegen die Erinnerung an den Wortlaut. |
| ⚓ skills/project-manager/SKILL.md | anpassen | + Lead-SKILL ≤150 Zeilen, Draft-Pickup auf PR/masterplan ohne progress. **Teil-Nachtrag 2026-07-26 (Lockstep-Gruppe „Repo-Skripte“):** nur die drei Stellen umgestellt, die diese Runde falsch gemacht hätten — Schritt 8 (Dashboard ist KEIN Kernel-Output, es braucht den Generator-Aufruf; „progress.yaml status/log“ raus), der Retro-Absatz (Datenquellen jetzt Status-Mix/`blocked_by`/Gate-Blocks statt `qa_failures`/`REJECTED`, plus der ausdrückliche Hinweis, dass es für kumulative Retry-ZÄHLER keinen Ersatz gibt) und der Kit-Merge-Absatz (`progress.yaml log:` → Decision-Item, Formulierung wie in den Init-/Scaffold-Skripten). Der Rest der Datei (`bugs.yaml`, `changelog.yaml`, `review_reports`/`test_reports`/`acceptance_reports`, `coding_guidelines.yaml`, `feature_requests.yaml`, `progress.yaml` in Zeile 15/209 …) ist unangetastet und gehört dieser Zeile. **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** die Datei war in der Vorrunde auf 233 Zeilen GEWACHSEN (HEAD 210) und damit die einzige über der Interimsgrenze 220 — jetzt 220 durch Verschieben von Craft-Detail in die Rollen-SKILLs (Design-Pipeline-Stufen (a)/(b) zusammengelegt und auf Orchestrierung reduziert, Test-Scoping-Ladder und Handover-Freshness auf die Regel gekürzt, Mechanik bleibt im QA-/Designer-/Frontend-SKILL). ABGESTELLT: die falsche Behauptung „a UI scope without a wireframe **blocks the scope-APR**“ (Parität #108, als „durch Gate ersetzt“ klassifiziert) — kein Code kennt WFR/wireframe in `approvals.py`/`dispatch.py`/`report.py`; die Regel steht jetzt ausdrücklich als PROSA-Pflicht mit dem Zusatz, dass der PM ihr einziger Wächter ist. **Parität #108 ist damit von „durch Gate ersetzt“ auf „behalten (Prosa) — Gate offen“ zu korrigieren.** Ebenso ehrlich gemacht: Schritt 7 nennt jetzt, dass `gate_git` den Merge trotz Evidence ablehnt. Das 25-KB-Paketbudget bleibt überschritten (49 KB) — das ist Phase 3 (II.11/3), hier ausdrücklich nicht in Auftrag. **Nachtrag 2026-07-26 (Gegenprüfung 2):** zwei V1-Reste gegen §0/§2.2 bereinigt — „BOOKKEEPING — update your owned files“ → „capture/transition the items you own through the kernel“, und „gates may require newly added fields in existing filled YAMLs — **fill those small deltas**“ → die Deltas gehen durch den Kernel, heute schreibt sie niemand (§0), also melden. Zusätzlich der Kit-Update-Absatz: `scaffold_team`/`init_project_memory` werden von `gate_write_scope` verweigert (siehe Zeile 87), die Zeilen gehen an den User. |
| ⚓ skills/quality-engineer/SKILL.md | anpassen | + Prüfung gegen AC/Invarianten, Evidence-Ausgabe. **Nachtrag 2026-07-26:** Schritt 5 behauptete „ein `INV`, dessen Test nicht existiert, gilt als unverifiziert und **blockt den Merge**“ — `report.py` führt genau diese Prüfung im Docstring als AUFGESCHOBEN (Phase 2, B.2-10), gemessen null Findings. Da diese Prüfung der Ersatz für das gelöschte `definition_of_done.yaml` ist (Parität #102), wäre hier Verhalten still gestorben: jetzt als PRÜFPFLICHT der Rolle formuliert, mit dem ausdrücklichen Hinweis, dass kein Gate es sieht. Gleichlautend in `research/skills/{methodologist,reviewer}/SKILL.md`. Offen für den Validator: die INV-check-ref-Auflösung als Phase-2-Rest. **Nachtrag 2026-07-26 (Gegenprüfung 2):** die Rolle verlangte Evidence, deren `artifact_refs` auf Screenshots/Rohlogs zeigen, nannte aber NULL Ablageort — während `agents/quality-engineer.md` sagt „you write nothing into `project_memory/`“ (Designer, Architekt und alle drei Auditoren haben `staging/`). Jetzt ein „Files you WRITE“-Block mit `project_memory/staging/<your task-id>/` wie im Designer-SKILL; der Zwilling `research/skills/reviewer/SKILL.md` gleich mitgezogen (Zeile 366). Außerdem: die Anekdote „broke on a missing config.yaml“ nennt jetzt keinen Dateinamen mehr — der neue Rohtext-Scan in `test_instruction_files_…` liest sie sonst als Pfad. |
| ⚓ skills/research-engineer/SKILL.md | anpassen | s. geteilte Begründung. |
| ⚓ skills/software-architect/SKILL.md | anpassen | + draw.io-ARC statt Mermaid, architecture.yaml-Auflösung (II.6a). **Nachtrag 2026-07-26:** zwei unerfüllbare Zusagen entschärft — `freeze_architecture` hat nur Testaufrufer (Rolle nennt jetzt den staged Pfad), und „a project that wants the guard needs you to create it“ (`coding_guidelines.yaml`) ist durch `gate_write_scope` gesperrt; die Heimat des `file_budget`/`source_areas`-Knopfs bleibt offen (Zeilen 156/189). **Nachtrag 2026-07-26 (Gegenprüfung 2):** die Premise-Re-Check-Pflicht sagte „record the outcome in **that item's** `premise_rechecks`“, wobei das grammatisch nächste Antezedens „a decision“ war. `report.py:_check_premise_recheck` liest das Feld ausschließlich vom **PR/RQ/CR** (Z. 522), nie vom DEC — am DEC notiert erzeugt es eine Warnung, die nie verschwindet. Jetzt ausdrücklich das PR/CR bzw. RQ/CR, das die DEC NENNT. |

**team-kits/dev-team/templates/project_memory** (Monolith-Stores → typisierte
Per-Item-Templates, II.2):

| pfad | disposition | begründung |
|---|---|---|
| ⚓ templates/project_memory/README.md | anpassen | Struktur-Doku → typisierte Per-Item-Ablage. **Nachtrag 2026-07-26 (Gruppe „globale Entry-Files“, Gegenprüfung-Befund 13):** `design/active/` ist aus Skelett und Layout-Block ENTFERNT — kein Itemtyp zeigt dorthin (`ACTIVE_DIRS`: `WFR`→`design/wireframes`, `DSN`→`design/revisions`), kein Kernel-Code berührt es, und ein Write dorthin wird von `gate_write_scope` verweigert (rc=2); WIP liegt in `staging/<task-id>/`. **Offen (fremde Zeile):** Spec II.2 listet `design/active/` in ihrem Strukturblock (Z. 176) weiter mit auf — die Spec-Zeile ist damit die letzte Referenz auf ein Verzeichnis, das kein Kit mehr ausliefert. |
| templates/project_memory/acceptance_reports.yaml | durch V2-Mechanik ersetzt | → evidence/ (kind: acceptance). |
| ⚓ templates/project_memory/architecture.yaml | durch V2-Mechanik ersetzt | Aufgelöst in ARC-Items (.drawio.svg) + SRs; packaging → schlankes Architektur-Item (II.6a). |
| templates/project_memory/bugs.yaml | durch V2-Mechanik ersetzt | → bugs/active/BUG-nnnn.yaml. |
| templates/project_memory/change_requests.yaml | durch V2-Mechanik ersetzt | → changes/active/CR-nnnn.yaml. |
| templates/project_memory/changelog.yaml | durch V2-Mechanik ersetzt | Historie lebt in Git (II.2). |
| templates/project_memory/coding_guidelines.yaml | durch V2-Mechanik ersetzt | Harte Regeln → INV-Items; Config-Knöpfe (file_budget/source_areas) bekommen neue Heimat (II.6). |
| templates/project_memory/decisions.yaml | durch V2-Mechanik ersetzt | → decisions/active/ Decision-Items. |
| ⚓ templates/project_memory/definition_of_done.yaml | durch V2-Mechanik ersetzt | DoD → AC/Invarianten + State-Validator + Quality-Gate/Fast-Mode. |
| ⚓ templates/project_memory/design.yaml | durch V2-Mechanik ersetzt | → eingefrorene DSN-Revisionen + design_ref; harte Vorgaben als INV (II.6). |
| ⚓ templates/project_memory/feature_requests.yaml | durch V2-Mechanik ersetzt | → inbox/active/FR-nnnn.yaml. |
| ⚓ templates/project_memory/generate_dashboard.py | anpassen | Liest künftig generated/index.yaml + aktive Items; dashboard_history entfällt; Lockstep (II.7/II.11/2). **Nachtrag 2026-07-26:** verschoben nach `templates/repo/scripts/generate_dashboard.py` — `gate_write_scope` lehnt jede schreibfähige Kommandozeile ab, die das State-Verzeichnis nennt, also war der dokumentierte („non-skippable“) Aufruf für jeden Agenten mit exit 2 gesperrt, solange das Skript darin lag. Ausgabe bleibt `project_memory/generated/dashboard.html`. **Nachtrag 2026-07-26 (Migration, II.10a):** die Migration muss `project_memory/{generate_dashboard.py,progress.dashboard.template.html}` in BESTEHENDEN Projekten entfernen — `init_project_memory` löscht nichts und listet nur noch, was im Template steht, also bleibt der V1-Generator dort liegen, wird nicht mehr als `[kept]`/divergent gemeldet und liest gelöschte Monolithen. **Nachtrag 2026-07-26 (CLI-Einstieg, II.11/4):** Generator und `retro.py` nennen `harness generate-index` als Abhilfe, `kit_checks` nennt `harness doctor`; ein `harness`-Executable existiert nirgends (`prog="harness"` in `kernel/cli.py` ist nur Hilfetext, `python -m kernel.cli` scheitert an `ModuleNotFoundError`, und die funktionierenden Varianten nennen die Enforcement-Ebene und werden von `gate_write_scope` mit exit 2 abgelehnt). Beide Meldungen nennen jetzt zusätzlich den heute begehbaren Weg (jeder Kernel-State-Write schreibt den Index mit); die ~40 weiteren `harness …`-Nennungen in den Hooks gehören an die Gruppe, die den CLI-Shim baut. |
| ⚓ templates/project_memory/masterplan.md | anpassen | → product/masterplan.md, eingefroren, ohne progress-Referenz (II.2/II.11/4). |
| ⚓ templates/project_memory/product_requirements.yaml | durch V2-Mechanik ersetzt | → product/active/PR-nnnn.yaml (legacy_ids: [PRD-xxxx]). |
| templates/project_memory/progress.dashboard.template.html | anpassen | Shell erhält V2-Sichten; keine committete History (II.7). **Nachtrag 2026-07-26:** mit dem Generator nach `templates/repo/scripts/` verschoben (Generator und Shell sind eine Einheit; project_memory trägt nur State). |
| ⚓ templates/project_memory/progress.yaml | durch V2-Mechanik ersetzt | Stirbt als Source of Truth; Status aus Per-Items + generated/ (II.2). |
| templates/project_memory/project_config.yaml | anpassen | Bleibt Projektkonfig; Felder an V2 angepasst. |
| templates/project_memory/research_notes.yaml | durch V2-Mechanik ersetzt | Findings → evidence/ bzw. research-Kit. |
| ⚓ templates/project_memory/review_findings.yaml | durch V2-Mechanik ersetzt | Auditor-Läufe → je Evidence + sofort BUG/CR/TSK (II.10a). |
| templates/project_memory/review_reports.yaml | durch V2-Mechanik ersetzt | → evidence/ (kind: review). |
| ⚓ templates/project_memory/system_requirements.yaml | durch V2-Mechanik ersetzt | → system/active/SR-nnnn.yaml. |
| ⚓ templates/project_memory/tasks.yaml | durch V2-Mechanik ersetzt | → tasks/active/TSK-nnnn.yaml (Work Order). |
| templates/project_memory/test_reports.yaml | durch V2-Mechanik ersetzt | → evidence/ (kind: test). |
| ⚓ templates/project_memory/testing_guidelines.yaml | durch V2-Mechanik ersetzt | Test-Regeln → INV-Items + Config (coverage_areas/browser_smoke). |

**team-kits/dev-team/templates/repo:**

| pfad | disposition | begründung |
|---|---|---|
| templates/repo/.claude/claude-security-guidance.md | anpassen | Pfad-Scope auf V2-Struktur (generated/**, evidence/) umschreiben. |
| templates/repo/.github/workflows/ci.yml | übernehmen | Projekt-CI ruft scripts/quality.py — V2-neutral. |
| templates/repo/.gitignore | anpassen | + kit_state.json, generated/**, Kernel-Lock; dashboard_history/Nag-Marker entfallen (II.2/II.8). |
| templates/repo/.pre-commit-config.yaml | übernehmen | ruff + Quick-Secret-Check, V2-neutral. |
| templates/repo/requirements-dev.txt | übernehmen | Tooling-/Security-Deps der Pipeline. |
| templates/repo/ruff.toml | übernehmen | Projekt-Lint-Baseline. |
| templates/repo/scripts/kit_browser_checks.py | anpassen | Browser-Smoke bleibt; Konfig-Quelle testing_guidelines→INV/Config. |
| ⚓ templates/repo/scripts/kit_checks.py | anpassen | yaml-lint/file-budget/module-invariants/enforcement-diff bleiben; progress.yaml-Vertragsprüfung entfällt (Lockstep II.11/2). **Nachtrag 2026-07-26 — was hinter „bleiben“ steckt:** (a) `module_invariants` und `file_budget`/`source_areas` lesen ihre Knöpfe aus `_GUIDELINE_FILES`, und ein V2-dev-Projekt hat KEINE dieser Dateien mehr (coding_guidelines.yaml aufgelöst, Zeile 156) — die Architektur-Invariante ist damit **inert** (`if not rules: return`) und das Budget nicht mehr tunbar/exemptierbar; die Knöpfe brauchen die in Zeile 156 versprochene neue Heimat, `_knob_hint` sagt dem User bis dahin die Wahrheit. (b) `check_state_validity` ist NEU und ein harter `fail` im Merge-Pfad — verlangt hat ihn nur die research-Zeile 434, er ist spiegelbedingt auch in dev. (c) `archive/` ist aus dem rekursiven yaml-lint ausgenommen (eingefrorene Items, monoton wachsend, kalter CI-Read), Parse-Schritt auf `CSafeLoader`. (d) `harness doctor` als Abhilfe existiert noch nicht — siehe den CLI-Vermerk in Zeile 164. |
| templates/repo/scripts/quality.py | anpassen | Quality-Pipeline bleibt (Fast-Mode II.10a); + Latenz-Bench. **OFFEN (2026-07-26, von der Lockstep-Gruppe gemeldet):** `_declared_source_areas()` ist ein ZWEITER Leser des `source_areas:`-Knopfs mit eigener Extraktion, eigenem Regex-Fallback und einer eigenen Kopie der Guidelines-Dateinamen (`kit_checks._GUIDELINE_FILES`). Nur der Docstring wurde entschärft (er behauptete „the same parser“); die Zusammenführung gehört in diese Zeile. |
| ⚓ templates/repo/scripts/retro.py | anpassen | Read-only-Retro bleibt; Datenquellen Per-Item statt progress/tasks; Auditor-Routine-Anbindung. **OFFEN (2026-07-26):** Datenquellen sind umgestellt; die Auditor-Routine-Anbindung (II.10a: Evidence pro Lauf, Wochen-ID + Lease, `APR.kind: routine`) ist NICHT gebaut — es existiert weder ein Produzent für Audit-Evidence noch ein APR-`kind`-Feld, retro könnte nur eine erfundene Form lesen. Gehört an die Gruppe, die II.10a baut. |

**tools:**

| pfad | disposition | begründung |
|---|---|---|
| tools/bump_kit_version.py | übernehmen | Versions-/Content-Hash-Stempelung bleibt. |
| tools/eval/README.md | übernehmen | Eval-Muster (Szenarien + LLM-Judge) bleibt gültig. |
| ⚓ tools/eval/scenarios.yaml | anpassen | Work-Orders/read_first auf V2-Item-Typen. **Nachtrag 2026-07-27:** umgestellt — und die Datei liest NICHTS (kein Runner, kein CI-Schritt), sie wird von Hand ausgeführt. Damit hing die Umstellung an keiner Prüfung: die HEAD-Fassung `read_first: [product_requirements.yaml PRD-0001]` blieb grün, weil der Lockstep-Sweep den PFAD beurteilt und ein nackter Monolithname keiner ist. Jetzt prüft `test_the_eval_scenarios_name_only_state_files_a_v2_project_has` sie mit demselben Vokabular-Aufruf wie die Entry-Gates (Union der drei Kits, nur `ANY`-Ausnahmen); mit der HEAD-Zeile rot gemessen. |
| ⚓ tools/test_e2e.py | anpassen | E2E-Pfade auf V2-Flow (Draft-PR→SR→TSK, Approval, Lock); Fixtures Per-Item. **Nachtrag 2026-07-27:** die Fixtures waren umgestellt, die KETTE fehlte — die Zeile war zur Hälfte offen und im Bericht der Lockstep-Gruppe als „ja“ abgehakt. Jetzt gebaut: `test_e2e_the_draft_to_dispatch_chain_runs_through_the_shipped_hooks` (Draft-PR → Freigabe durch den ausgelieferten `_gate.py`-Launcher → SR → TSK → Lease → Spawn, plus Rollen-Mismatch als Gegenrichtung) und `test_e2e_a_lock_held_by_a_foreign_process_makes_the_gate_wait_not_skip` (II.12 v2.1: „zweiter Prozess wartet/blockt“, als Laufzeit gemessen — 2,10 s Wartezeit gegen 2,0 s Haltedauer; ohne Lock 0,32 s = rot). Nicht enthalten und weiter offen: der volle II.12-E2E pro Kit (QA → Abnahme → Archiv, FR-Triage, Session-Rekonstruktion). |
| ⚓ tools/test_hooks.py | anpassen | Hook-Tests auf V2/gate_dispatch/Kernel (II.12-Matrix); Fixtures Per-Item. **Nachtrag 2026-07-26 (Gegenprüfung 2):** `test_instruction_files_name_only_state_files_a_v2_project_has` hielt seine eigene Zusage („a plain typo in a path a role is told to read“) nicht: es las nur Backtick-Spans, verankerte den Dateinamen an `$` und prüfte ausschließlich den BASENAME. Gemessen grün bei drei echten Regressionen (Monolithpfad ohne Backticks, Backtick-Span mit Nachtext, Verzeichnis-Tippfehler in einem Item-Pfad). Jetzt drei Behauptungen statt einer — Dateiname im ROHTEXT, Verzeichnis-Existenz gegen Template-Baum ∪ `ACTIVE_DIRS` (+ `STATE_DIRS_NOT_SHIPPED` mit Begründung), und die ÜBEREINSTIMMUNG Typ↔Verzeichnis in beiden Prosaformen, womit die §6-Tabellen gegen die Konstante gepinnt sind. Acht Mutationen in Sandkopien geprüft: Baseline grün, alle acht rot. Neu: `test_no_instruction_file_names_a_hook_its_own_kit_does_not_ship` (Gegenrichtung zu `test_every_hook_documented_in_its_constitution`; „Hook“ ist definiert als „ein Modul, das irgendein Kit ausliefert“, damit der Rubrik-Schlüssel `gate_health` nicht mitzählt). **Nachtrag 2026-07-27 (Teilumsetzung, ehrlich fortgeschrieben):** die Fixtures sind per-Item und der Lockstep-Beweis liegt hier; „Hook-Tests auf V2/gate_dispatch/Kernel (II.12-Matrix)“ ist es NICHT im Sinne einer Matrix-Rückverfolgung. Die Abdeckung liegt verteilt in `tools/test_hooks_v2.py` (Dispatch-Lebenszyklus, Approval-Protokoll, Lock/Audit), `tools/test_approvals_dispatch.py`, `tools/test_kernel.py`, `tools/test_state.py`; II.12 ist Fließtext, keine parsebare Tabelle, also existiert kein Test, der Matrixzeile gegen Testnamen abgleicht. Offene Hälfte (Rest an die Gruppe, die II.10a/II.12 abnimmt): Auditor-Routine-Tests, Codex-Pfad `audited`, Latenz-Bench, Research-E2E RQ→HYP→EXP. Ausserdem gehört `tools/test_hooks_v2.py` sinngemäss unter diese Zeile — es fehlt im Inventar. **Nachtrag 2026-07-27 (Prüfrunde 3, Status statt Fortschreibung):** die Zeile ist damit **HALB ERFÜLLT und bleibt OFFEN** — Fixtures/Per-Item ja, II.12-Matrix-Rückverfolgung nein. Die Fortschreibung oben beschreibt, was statt der Anordnung getan wurde; sie ersetzt sie nicht. Was in dieser Runde dazukam: der Vollständigkeitsbeweis liest jetzt auch Python-`#`-Kommentare (`tokenize`) und faltet Pfadkompositionen nach der Frage „was tut der Aufruf mit seinen Argumenten“ statt nach einer Liste von Schreibweisen (`Path(...)`, `.joinpath`, `+`); `item_file` ist erweiterungsblind und greift dort, wo ein Item-HOME beansprucht wird (`design/wireframes/DSN-0001.html` vorher grün); ein `Join-Path`-Kopf, der mit `-` beginnt, ist ein Parametername und wird nicht gefaltet. |
| tools/conftest.py | anpassen | Fehlte im Inventar (nachgetragen 2026-07-27). Trägt den `known_hole`-Marker und das V1-Inventar: `V1_MONOLITHS` (die elf Speicher, die dieser Lockstep verschoben hat) und NEU `V1_ROOT_STORES_NOT_YET_MIGRATED` (`coding_guidelines.yaml`, `testing_guidelines.yaml`, `process_definitions.yaml`, `*report*.yaml` — dieselbe Definition, aber ausgeliefertem Code noch gekoppelt; Zeilen 115/159/176/249/338/507/556). Ohne die zweite Liste behauptete der Beweis Vollständigkeit gegenüber einer Aufzählung, die gegen ihre eigene Definition unvollständig war. |
| ⚓ tools/test_hooks_v2.py | anpassen | Fehlte im Inventar (nachgetragen 2026-07-27); zweitgrößte Datei des Repos. V2-Verhalten: Dispatch-Lebenszyklus, Approval-Protokoll, Lock/Audit, doctor/Capability-Matrix, office-PII. Fixtures Per-Item. **Nachtrag 2026-07-27:** `test_the_ui_inventory_snapshot_rule_is_shipped` prüfte mit einem ±300-Zeichen-Fenster auf ein blosses `CR`-Token und wurde in der Verfassung von der Glossarzeile drei Zeilen darüber allein erfüllt — die UI-Pflicht liess sich durch „visible UI elements may be removed freely“ ersetzen, ohne dass der Test rot wurde. Jetzt wird die REGEL gesucht (ein Satz, der Entfernen/Ersetzen an ein CR bindet) im selben Markdown-Block wie die Snapshot-Nennung; vier Mutationen rot, Nachbarblock-Kontrolle grün. |
| tools/test_kernel.py · tools/test_state.py · tools/test_schemas.py · tools/test_report.py · tools/test_backlog_types.py · tools/test_approvals_dispatch.py · tools/test_staging_cli.py | übernehmen | Fehlten im Inventar (nachgetragen 2026-07-27). V2-eigene Testmodule — sie sind mit dem State-Kernel entstanden und beschreiben V2-Mechanik, es gibt an ihnen nichts umzustellen. |
| tools/gen_known_holes.py | übernehmen | Fehlte im Inventar (nachgetragen 2026-07-27). Erzeugt `kernel/known_holes.json` + Digest aus pytests eigener Marker-Sammlung; V2-Mechanik, unverändert gültig. |
| tools/probes/** | übernehmen | Fehlten im Inventar (nachgetragen 2026-07-27). Manuelle Sonden für Hook-/Settings-Verhalten des Providers, kit- und zustandsunabhängig. |
| tools/validate.py | anpassen | Self-Check prüft künftig typisierte Item-Templates + Schemadateien (Envelope/session_brief/ARC/WFR). **Nachtrag 2026-07-26 (Gegenprüfung 2):** der §-Referenz-Check (Z. 282–301) prüfte `hooks/*.py`, `skills/*/SKILL.md`, `agents/*.md` — nicht die Verfassung selbst, obwohl sie sich häufiger auf sich selbst beruft als jede andere Datei; und ein `§2.7`-artiger Sub-Verweis wurde per `continue` GANZ übersprungen, sodass `§99.1` durchfiel. Beides behoben (Verfassung im Glob, Sub-Verweis prüft den Elternabschnitt); mit je einer Mutation (`§77` und `§77.3`) rot gesehen, danach wieder grün. |

**.codex/agents (untracked, generator-verwaltet):**

| pfad | disposition | begründung |
|---|---|---|
| .codex/agents/codex-watcher.toml | anpassen | Generierte Codex-Spiegelung; wird beim V2-Scaffold via gen_provider_artifacts.py neu erzeugt (nie manuell). |
| .codex/agents/radar-watcher.toml | anpassen | Wie oben — regenerierte Provider-Artefaktausgabe. |

### 1.2 Disposition Teil 2 — team-kits-Root · office-team · research-team · user

**team-kits/ (Root):**

| pfad | disposition | begründung |
|---|---|---|
| gen_provider_artifacts.py | anpassen | Provider-Parität muss neue Gates (gate_dispatch/guard_memory_budget) + Enforcement-Matrix abbilden (II.11/4). |
| ⚓ init_project_memory.ps1 | anpassen | Kopiert künftig die typisierte V2-Struktur statt der Monolith-YAMLs (II.2/II.11/4). |
| ⚓ init_project_memory.sh | anpassen | POSIX-Zwilling desselben Init-Skripts. |
| model_tiers.yaml | übernehmen | Providerneutrale Modelltiers, zustandsunabhängig. |
| preset_config.py | übernehmen | Strikter Preset-Parser bleibt gültig. |
| registry.yaml | anpassen | Routing-Mechanik bleibt; V1-Beschreibungstexte („PRD→SRD→Task", „append-only ledger") auf V2. |
| ⚓ scaffold_team.ps1 | anpassen | V2-Struktur, neue Hooks, kit_state.json, .gitignore generated/, .vscode draw.io (II.6a/II.8/II.11). |
| ⚓ scaffold_team.sh | anpassen | POSIX-Zwilling desselben Scaffold-Skripts. |

**office-team/agents:**

| pfad | disposition | begründung |
|---|---|---|
| bookkeeper.md | anpassen | Craft bleibt; Flow/Budgets auf V2 (Result-Envelope, Write-Scope, II.4/II.5). |
| compliance-researcher.md | anpassen | Wie bookkeeper. |
| marketing-planner.md | anpassen | Wie bookkeeper. |
| office-developer.md | anpassen | Wie bookkeeper. |
| office-manager.md | anpassen | Lead auf V2: Draft-PR/State-Kernel/APR-Protokoll, ≤-Budgets (II.1/II.2). |
| product-editor.md | anpassen | Wie bookkeeper. |
| project-auditor.md | anpassen | Auditor wird Routine (APR.kind:routine) statt Delivery-Station (II.1/II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:66` `ROOT_DISPATCH_KINDS = {scope, delivery}`, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. |
| ⚓ records-clerk.md | anpassen | Filing gegen filing_plan.yaml-Wahrheit; filing_log wird Scan-Index (II.9). |
| shop-curator.md | anpassen | Wie bookkeeper. |

**office-team/constitution + hooks:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ constitution/AGENTS.md | anpassen | ≤150 Zeilen NACH Ersatzgates, V2-Zustandsmodell, Monolith-Refs raus (II.5/II.10a/II.11). **Konkret gemeldet 2026-07-26:** Zeilen 70/83/137 beschreiben `filing_log.yaml` im Präsens, als existiere die Datei. Sie wird von nichts erzeugt und von keinem Gate gelesen (`filing_plan.yaml` ist die Wahrheit); `scripts/pii_scan.py`, `inbox/README.txt` und `templates/project_memory/README.md` sagen das inzwischen im Konjunktiv. **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** vier Behauptungen ohne Code ehrlich gemacht — (a) NEUER §0-Write-Lock-Punkt (wie dev/research; nennt zusätzlich, dass §4 Phasen 1–4 damit unausführbar sind und dass `gate_filing`s eigene Remedy „have the records-clerk propose filing_plan.yaml rules“ gesperrt ist); der in dieser Runde neu eingefügte Satz „die master-data files … sind configuration and reference data, **not items**“ behauptete eine Ausnahme, die `gate_write_scope._assert_state_write_allowed` nicht kennt. (b) §1: `gate_proc_approved` „hard-blocks“ → der Hook liest den gelöschten V1-Monolithen `process_definitions.yaml` und exit(0) bei Abwesenheit, blockt also NICHTS (das V2-Bootstrap-Loch aus II.4 ist permanent offen); dieselbe Datei erklärte drei Zeilen höher, dass genau dieser Monolith keinen Nachfolger hat. (c) §1/§4/Phase 4: `scripts/proc_hash.py` und `scripts/process_doc.py` crashen an derselben gelöschten Datei, und KEIN ausgeliefertes Kommando berechnet `approved_hash`, den `report.py:226` bei APPROVED/ACTIVE-PROC als **error** verlangt ⇒ ein office-Projekt kann keinen gültigen freigegebenen PROC bekommen und laut §1 keinen Spezialisten spawnen. (d) §2.4 Verfahrensdoku-Renderer als kaputt benannt. **Blockierend für den Schritt:** `gate_proc_approved` + `proc_hash.py`/`process_doc.py` auf `procedures/active/PROC-*.yaml` bzw. den Kernel-Hash umstellen (Hooks-/Skript-Gruppe; Zeilen 249/312/313). **Nachtrag 2026-07-26 (Gegenprüfung 2):** (e) die vier in Runde 1 neu eingefügten `(§8)`-Verweise (Z. 25/44/75/114) zeigten auf einen Abschnitt, der die zitierte Regel NICHT enthielt — §8 sagte nur „the enforcement layer itself is off-limits“, nie „ein fehlzündendes Gate ist ein Infrastruktur-Defekt, den du meldest statt umgehst“ (dev/research haben sie als §2 Item 10). §8 trägt den Satz jetzt, im Wortlaut von dev §2.10. (f) §0 nennt zusätzlich die Shell-Hälfte des Gates (`init_project_memory`/`scaffold_team`, siehe Zeile 87). (g) §2 Item 1 nannte `guard_no_adhoc` — einen Hook, den dieses Kit NICHT ausliefert (Vorbestand seit HEAD); die Zeile sagt jetzt, dass die Regel hier Policy ist, und `test_no_instruction_file_names_a_hook_its_own_kit_does_not_ship` hält die Richtung Verfassung→Hook ab jetzt fest. (h) die Auditor-Routine-Zeile ehrlich gemacht (siehe Zeile 236). |
| hooks/_audit.py | übernehmen | Audit-Log-Helfer bleibt. |
| hooks/_compat.py | übernehmen | Provider-Payload-Shim weiterhin nötig. |
| hooks/_root.py | übernehmen | Git-Root-Resolver bleibt. |
| ⚓ hooks/gate_filing.py | anpassen | Liest KÜNFTIG filing_plan.yaml als einzige Wahrheit (heute: PostToolUse auf filing_log.yaml; II.9). |
| hooks/gate_proc_approved.py | anpassen | Bleibt Dispatch-Gate-Basis; Bootstrap-Loch schließen, PROC per-item (II.4/II.9). |
| hooks/gate_subagent_output.py | anpassen | Result-Envelope-≤4-KB-Schema erzwingen (II.5). |
| hooks/guard_agent_spawn.py | anpassen | Gate-Schicht 1 + neues Dispatch-Lease-Gate (II.4). |
| hooks/guard_fs_tripwire.py | übernehmen | FS-Tripwire-Schutz bleibt fail-closed gültig. |
| hooks/guard_harness_selfmod.py | übernehmen | Harness-Selbstschutz unverändert nötig. |
| **hooks/guard_ledger_direct.py** | **bewusst entfernen** | Append-only-Ledger abgeschafft (User-Entscheid I.3/1; II.9 nennt die Löschung explizit) — Edits erlaubt, validierungspflichtig via gate_ledger_valid. |
| hooks/guard_question_context.py | anpassen | + Marker-Freigabeprotokoll auf AskUserQuestion (II.2). |
| hooks/guard_scratchpad_ref.py | übernehmen | Bleibt gültig. |
| ⚓ hooks/guard_yaml_valid.py | anpassen | Harten progress.yaml-Branch entfernen; typisierte Items/State-Validator (II.11/2). |
| hooks/notify_agent_events.py | übernehmen | Komfort-Benachrichtigung (fail-open). |
| ⚓ hooks/session_status.py | anpassen | Update-Zustandsautomat, ~6 Blöcke → kit_state.json + session_brief (II.8). |

**office-team presets/settings/skills:**

| pfad | disposition | begründung |
|---|---|---|
| presets.yaml | übernehmen | Preset→Rollen-Mapping bleibt. |
| settings/settings.json | anpassen | Neue Gates rein, guard_ledger_direct raus (II.11/2). |
| office-team/VERSION | anpassen | V2-Bump (II.11/4). |
| skills/bookkeeper/SKILL.md | anpassen | ≤-Budgets, Result-Envelope-Flow; Craft bleibt (II.5). **BEKANNTE MID-LOCKSTEP-LÜCKE, gemeldet 2026-07-26 (Gegenprüfung 2), gilt für alle „Wie bookkeeper“-Zeilen (269/270/271/273/276):** das office-Kit hat derzeit ZWEI Ausgabekontrakte. `records-clerk`, `project-auditor` und `office-manager` sind auf das Result-Envelope umgestellt; diese sechs tragen weiter den V1-Block (`summary`/`proc`/`booked`/…). `dispatch.py:522` validiert `result_envelope` mit `strict: true`, `gate_subagent_output` verlangt nur `summary:` — die sechs fallen also erst durch, wenn ein Ergebnis wirklich übernommen wird. Dispositionskonform (kein ⚓, späterer Schritt), aber NICHT erledigt. |
| skills/compliance-researcher/SKILL.md | anpassen | Wie bookkeeper. |
| skills/marketing-planner/SKILL.md | anpassen | Wie bookkeeper. |
| skills/office-developer/SKILL.md | anpassen | Wie bookkeeper. |
| ⚓ skills/office-manager/SKILL.md | anpassen | Lead-SKILL ≤150 Zeilen, V2-Flow, Monolith-Refs raus (II.5). **Nachtrag 2026-07-26 (Gegenprüfung 2):** die `init_project_memory`/`scaffold_team`-Aufrufe dieser Datei werden von `gate_write_scope` verweigert (gemessen rc=2: „names the enforcement layer in a pipeline that can write“, weil `_ENFORCEMENT_RX` auch `team-kits` matcht). Die Stellen sagen das jetzt und geben die Zeile an den USER — sonst testet ein PM im ersten Schritt eines frischen Repos die Runde-1-Lehre „report it, never work around it“. Siehe den erweiterten §0-Punkt (Zeile 87). |
| skills/product-editor/SKILL.md | anpassen | Wie bookkeeper. |
| ⚓ skills/project-auditor/SKILL.md | anpassen | Routine mit APR.kind:routine, Fingerprint-Dedup (II.10a). **Nachtrag 2026-07-26:** der Fingerprint fehlte (siehe Zeile 142) und ist jetzt in allen drei Auditor-SKILLs definiert. |
| ⚓ skills/records-clerk/SKILL.md | anpassen | Filing gegen filing_plan.yaml (II.9). **Nachtrag 2026-07-26:** das Cutover-Ritual protokollierte den „nothing lands here anymore“-Beschluss weiter „in progress.yaml“ — jetzt Decision-Item unter `decisions/active/` (Formulierung wie in den Init-/Scaffold-Skripten). **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** der Output-Block war noch das V1-Format (`summary/proc/filed/unclear/parked_for_deletion/plan_changes_proposed`) statt des Result-Envelopes, obwohl alle anderen konvertierten Spezialisten-SKILLs umgestellt wurden — jetzt Envelope (der PROC steckt im `product_requirement` des Tasks). Ebenso in `skills/office-manager/SKILL.md` die letzte „logged skip“-Formulierung → Decision-Item. |
| skills/shop-curator/SKILL.md | anpassen | Wie bookkeeper. |

**office-team/templates/project_memory:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ README.md | anpassen | Auf typisierte V2-Verzeichnisstruktur umschreiben (II.2). **Nachtrag 2026-07-26 (Gruppe „globale Entry-Files“, Gegenprüfung-Befund 2/3):** `product/active/` + die PR-Zeile sind ENTFERNT (führende Ebene ist `PROC`); das ist die bewusst gewählte Hälfte der Alternative „Office-Wurzeltyp wiederherstellen ODER die dokumentierte Wurzel entfernen“, passend zu `ROOT_TYPE_BY_KIT` ohne `office-team`. Dasselbe totes-Verzeichnis-Muster im research-Kit mitentfernt (`research-team/templates/project_memory/product/active/`, von keiner Datei genannt). Festgehalten von `test_kit_names_a_root_item_exactly_when_the_kernel_gives_it_one`. |
| business_profile.yaml | übernehmen | Onboarding-Config, keine Statusquelle. |
| changelog.yaml | durch V2-Mechanik ersetzt | Git-Historie (II.2). |
| compliance_register.yaml | anpassen | Register bleibt fachlich; Ablage folgt typisierter Struktur. |
| content_guidelines.yaml | übernehmen | Craft-Guideline, kein Zustand. |
| ⚓ filing_log.yaml | durch V2-Mechanik ersetzt | Regenerierbarer Scan-Index (II.9). |
| filing_plan.yaml | anpassen | Wird EINZIGE maschinenlesbare Wahrheit mit Regel-Feldern (II.9). |
| marketing_plan.yaml | übernehmen | Fachliches Planungsartefakt. |
| master_data.yaml | übernehmen | Stammdaten-Config. |
| masterplan.md | anpassen | → product/masterplan.md, eingefrorenes Discovery-Artefakt (II.2). |
| process_definitions.yaml | durch V2-Mechanik ersetzt | → procedures/active/PROC-nnnn.yaml Per-Item (II.2/II.9). |
| product_catalog.yaml | übernehmen | Shop-Katalogdaten. |
| ⚓ progress.yaml | durch V2-Mechanik ersetzt | → generated/session_brief.yaml + index.yaml (II.2). |
| project_config.yaml | anpassen | providers/preset/repo_mode + kit_state-Bezug (II.8/II.10a). |
| ⚓ review_findings.yaml | durch V2-Mechanik ersetzt | Befunde → BUG/CR/TSK + Evidence pro Lauf (II.10a). |

**office-team/templates/repo:**

| pfad | disposition | begründung |
|---|---|---|
| .claude/claude-security-guidance.md | übernehmen | Sicherheitsleitfaden, kit-unabhängig. **OFFEN (2026-07-26, gemeldet statt eigenmächtig geändert):** die office-Kopie nennt in ihrer Scope-Liste weiter „filing plan/log … progress“ — `progress.yaml` ist gelöscht und `filing_log.yaml` wird von nichts erzeugt. Die Zeile steht auf „übernehmen“, deshalb unverändert; der Halbsatz gehört in derselben Runde wie die office-Verfassung korrigiert (siehe Zeile 244). |
| ⚓ .gitignore | anpassen | + generated/**, kit_state.json, Kernel-Lock (II.2/II.8). **Nachtrag 2026-07-26:** der `filing_log.yaml`-Eintrag bleibt, aber ohne Zweckbehauptung („bleiben für die Gates auf Platte“ war falsch — kein Gate liest ihn, nichts erzeugt ihn); er ist jetzt ausdrücklich defensiv formuliert. **Nachtrag 2026-07-27:** die Lockstep-Runde hatte die Zeile trotzdem GELÖSCHT — der Vollständigkeits-Sweep las das Ignore-Muster als übrig gebliebenen Zeiger. Wiederhergestellt. Der Sweep unterscheidet jetzt: ein `.gitignore`-Muster ist ein VERBOT, kein Verweis (es öffnet die Datei nicht und schickt niemanden hin), nur eine Wiedereinschluss-Zeile `!pfad` wird beurteilt. Gehalten wird die Zeile ab jetzt maschinell, per Wirkung statt per Zeichenkette: `test_the_office_gitignore_keeps_name_bearing_state_out_of_git` misst mit `git check-ignore` in einem Wegwerf-Repo (Gegenrichtung inklusive: `project_config.yaml` und `ledger/` bleiben getrackt). |
| archive/README.txt | übernehmen | Deterministische Archivpfade passen zu V2. |
| ⚓ inbox/README.txt | anpassen | Monolith-/filing_log-Referenz aktualisieren. |
| outbox/README.txt | übernehmen | Neutraler Ordnerhinweis. |
| requirements-office.txt | übernehmen | Python-Deps der Office-Skripte. |
| scripts/einvoice_extract.py | übernehmen | Fachliches E-Invoice-Tool. |
| scripts/euer_report.py | übernehmen | EÜR-Report liest die Ledger-CSV (V2-konform). |
| scripts/ledger_add.py | anpassen | Validierender Edit-/Importpfad vor atomarer Speicherung statt append-only (II.9). |
| scripts/pii_scan.py | anpassen | filing_log-Referenz aktualisieren: `filing_plan.yaml` ist die Wahrheit, `filing_log.yaml` wäre ein regenerierter Scan-Index (II.9) — Zeile 2026-07-26 nachgetragen, die Datei fehlte im Inventar. **Nachtrag 2026-07-27:** die Umsetzung hat die Ausnahme von EINER Datei auf den Baum `project_memory/generated/` ausgeweitet — bewusst, weil `generated/` definiert ist als „was der Kernel neu baut“ und `index.yaml`/`session_brief.yaml` genauso Item-Titel tragen; eine Aufzählung der drei Rollups veraltet mit dem nächsten. Angeordnet war die Ausweitung nicht, sie steht hier deshalb ausdrücklich. Der Kommentar dazu behauptete „they are gitignored, so the scan never meets one anyway“ — falsch an der einzigen Stelle, an der es gemessen wird (die Test-Fixture liefert keine `.gitignore` aus, die Ausnahme ist dort tragend); korrigiert. **Prüfrunde 3, 2026-07-27:** dieser Nachtrag ist von der ausführenden Runde geschrieben worden und lizenziert damit ihre eigene Abweichung — er ist eine OFFENLEGUNG, keine Anordnung. Sachlich unstrittig (kein Codefehler, Hausregel 1 spricht für den Baum statt der drei Namen), aber die Ausweitung von einer Datei auf `project_memory/generated/` gehört bei der Abnahme ausdrücklich bestätigt. |
| scripts/proc_hash.py | durch V2-Mechanik ersetzt | Verallgemeinertes Hash-Modul im State-Kernel (kanonisches JSON+NFC+Version, II.2/II.11/1). |
| scripts/process_doc.py | anpassen | Auf Per-Item-PROC-Dateien umstellen (II.9). |

**research-team/agents:**

| pfad | disposition | begründung |
|---|---|---|
| data-analyst.md | anpassen | Result-Envelope-Flow; Craft bleibt. |
| methodologist.md | anpassen | Wie data-analyst. |
| project-auditor.md | anpassen | Auditor-Routine (APR.kind:routine, II.1/II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:66` `ROOT_DISPATCH_KINDS = {scope, delivery}`, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. |
| ⚓ project-manager.md | anpassen | Lead auf V2: Draft-RQ/State-Kernel, Monolith-Refs raus (II.2/II.3). **Nachtrag 2026-07-26 (Gegenprüfung 2):** die `init_project_memory`/`scaffold_team`-Aufrufe dieser Datei werden von `gate_write_scope` verweigert (gemessen rc=2: „names the enforcement layer in a pipeline that can write“, weil `_ENFORCEMENT_RX` auch `team-kits` matcht). Die Stellen sagen das jetzt und geben die Zeile an den USER — sonst testet ein PM im ersten Schritt eines frischen Repos die Runde-1-Lehre „report it, never work around it“. Siehe den erweiterten §0-Punkt (Zeile 87). |
| report-writer.md | anpassen | Wie data-analyst. |
| research-engineer.md | anpassen | Wie data-analyst. |
| researcher.md | anpassen | Wie data-analyst. |
| reviewer.md | anpassen | Wie data-analyst. |

**research-team/constitution + hooks:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ constitution/AGENTS.md | anpassen | ≤150 Zeilen, V2-Zustandsmodell RQ/HYP/EXP (II.5/II.11). **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** (a) NEUER §0-Write-Lock-Punkt wie dev — der in der Vorrunde eingefügte Satz „the reference files named in §6 are **material, not items**“ behauptete eine `gate_write_scope`-Ausnahme, die es nicht gibt; er gilt jetzt ausdrücklich auch für die gerenderten `reports/` (Report-Writer). (b) `gate_git`-Zeile ehrlich (blockt derzeit jeden merge/push). (c) §2.4 „no RQ **leaves** DELIVERED“ → „REACHES“. (d) §2.3 sagte „**no dashboard generator ships any more**“ und ENTSCHIED damit den in Zeile 379 offenen Punkt — jetzt nur noch die messbare Tatsache („this kit ships no dashboard generator“) ohne Beschluss; der Entscheid steht weiter aus (Zeile 379). **Nachtrag 2026-07-26 (Gegenprüfung 2):** (e) §0 nennt zusätzlich die Shell-Hälfte des Gates (`init_project_memory`/`scaffold_team`, siehe Zeile 87). (f) §10 `premise_rechecks` sagt jetzt, dass das Feld am **RQ/CR** hängt, nicht am DEC. (g) die Auditor-Routine-Zeile ehrlich gemacht (siehe Zeile 321). |
| hooks/_audit.py | übernehmen | Audit-Helfer bleibt. |
| hooks/_compat.py | übernehmen | Provider-Shim bleibt. |
| hooks/_root.py | übernehmen | Git-Root-Resolver bleibt. |
| ⚓ hooks/auto_dashboard.py | durch V2-Mechanik ersetzt | Kernel-Index atomar + optionaler STALE-Flag statt PostToolUse-Regen (II.4/II.7). **Präzisierung 2026-07-26:** gilt für den Index; ein Dashboard gibt es in research derzeit gar nicht — siehe den OFFEN-Vermerk in Zeile 379. |
| hooks/format_on_write.py | übernehmen | Komfort-Formatter (fail-open). |
| hooks/gate_git.py | anpassen | Branch↔Item + typgerechter Status statt PRD-\d (II.10). |
| ⚓* hooks/gate_memory_complete.py | anpassen | State-Validator/typisierte Items (II.4 Schicht 5). ⚓* = koppelt über den masterplan-Check (:162–164) an masterplan.md — kein Monolith-Namens-Match, aber von Spec II.11/0(a) ausdrücklich als Lockstep-Mitglied benannt. |
| hooks/gate_pipeline.py | anpassen | Fast-Mode/Quality-Gate-Definition (II.10a). |
| hooks/gate_subagent_output.py | anpassen | Envelope-≤4-KB-Schema (II.5). |
| hooks/guard_agent_spawn.py | anpassen | + Dispatch-Lease-Gate (II.4). |
| hooks/guard_harness_selfmod.py | übernehmen | Selbstschutz bleibt. |
| ⚓ hooks/guard_no_adhoc.py | anpassen | Auf typisierte TSK-Items statt tasks.yaml (II.2/II.11/2). |
| hooks/guard_pm_scope.py | anpassen | Auf Write-Scope-Gate/Kernel (II.4 Schicht 3). |
| hooks/guard_question_context.py | anpassen | + Marker-Freigabeprotokoll (II.2). |
| hooks/guard_scratchpad_ref.py | übernehmen | Bleibt gültig. |
| ⚓ hooks/guard_yaml_valid.py | anpassen | progress.yaml-Branch entfernen (II.11/2). |
| hooks/notify_agent_events.py | übernehmen | Komfort-Hook. |
| ⚓ hooks/session_status.py | anpassen | Update-Zustandsautomat (II.8). |

**research-team presets/settings/skills:**

| pfad | disposition | begründung |
|---|---|---|
| research-team/VERSION | anpassen | V2-Bump. |
| presets.yaml | übernehmen | Preset→Rollen-Mapping bleibt. |
| settings/settings.json | anpassen | Neue Gate-Registrierungen (II.11/2). |
| ⚓ skills/data-analyst/SKILL.md | anpassen | ≤-Budgets, V2-Flow, Monolith-Refs raus (II.5). |
| skills/methodologist/SKILL.md | anpassen | ≤-Budgets, V2-Flow. **Nachtrag 2026-07-26 (Gegenprüfung 2):** die Premise-Re-Check-Pflicht sagte „record the outcome in **that item's** `premise_rechecks`“, wobei das grammatisch nächste Antezedens „a decision“ war. `report.py:_check_premise_recheck` liest das Feld ausschließlich vom **PR/RQ/CR** (Z. 522), nie vom DEC — am DEC notiert erzeugt es eine Warnung, die nie verschwindet. Jetzt ausdrücklich das PR/CR bzw. RQ/CR, das die DEC NENNT. |
| ⚓ skills/project-auditor/SKILL.md | anpassen | Auditor-Routine (II.10a). **Nachtrag 2026-07-26:** Fingerprint nachgeliefert (siehe Zeile 142). |
| ⚓ skills/project-manager/SKILL.md | anpassen | Lead-SKILL ≤150 Zeilen, RQ-Flow (II.5). **Teil-Nachtrag 2026-07-26 (Lockstep-Gruppe „Repo-Skripte“):** nur der Retro-Absatz (Datenquellen + „Index ist eine Momentaufnahme, kein Zähler“) und die `progress.yaml log:`-Phrase im Kit-Merge-Absatz umgestellt — Spiegel der dev-Änderung, damit dieselbe Anweisung nicht in zwei Kits verschieden lautet. Alles andere (`research_questions.yaml`, `progress.yaml` Zeile 13/60/135, `experiment_designs.yaml`, `changelog.yaml`, die Report-Monolithe) gehört dieser Zeile. **Nachtrag 2026-07-26 (Gegenprüfung 2):** zwei V1-Reste gegen §0/§2.2 bereinigt — „BOOKKEEPING — update your owned files“ → „capture/transition the items you own through the kernel“, und „gates may require newly added fields in existing filled YAMLs — **fill those small deltas**“ → die Deltas gehen durch den Kernel, heute schreibt sie niemand (§0), also melden. Zusätzlich der Kit-Update-Absatz: `scaffold_team`/`init_project_memory` werden von `gate_write_scope` verweigert (siehe Zeile 87), die Zeilen gehen an den User. |
| skills/report-writer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. **Nachtrag 2026-07-26 (Gegenprüfung 2):** Runde 1 hatte den Write-Lock nur in `agents/report-writer.md` nachgetragen; das SKILL — die operative Anweisung, die dieselbe Agent-Datei preloadet — verlangte weiter uneingeschränkt `project_memory/reports/EXP-*.tex` usw. und enthielt KEIN einziges `staging`-Vorkommen, die Rolle hatte also nirgends einen legalen Ausgabeort (gemessen: `Write project_memory/reports/EXP-0001.html` → rc=2). Jetzt ein „Where your renders go“-Block, `staging/<task-id>/` als Ziel unter den FINALEN Dateinamen, und `reports/` benannt als der Ort, an den der Kernel promotet, sobald der Weg existiert. |
| skills/research-engineer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. |
| ⚓ skills/researcher/SKILL.md | anpassen | ≤-Budgets, V2-Flow, Monolith-Refs raus (II.5). |
| skills/reviewer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. **Nachtrag 2026-07-26 (Gegenprüfung 2):** wie das dev-QA-SKILL (Zeile 144) hatte die Rolle keinen legalen Ort für Rohlogs, obwohl ihre Evidence `artifact_refs` tragen soll — jetzt `project_memory/staging/<your task-id>/`. |

**research-team/templates/project_memory:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ README.md | anpassen | Typisierte V2-Struktur RQ/HYP/EXP (II.2). |
| acceptance_reports.yaml | durch V2-Mechanik ersetzt | → Evidence-Dateien (II.2). |
| changelog.yaml | durch V2-Mechanik ersetzt | Git-Historie (II.2). |
| decisions.yaml | durch V2-Mechanik ersetzt | → decisions/active/ Decision-Items (II.2). |
| experiment_designs.yaml | durch V2-Mechanik ersetzt | → experiments/active/EXP-nnnn.yaml (II.2). |
| findings.yaml | durch V2-Mechanik ersetzt | → Evidence/results (II.2). |
| fzulg_documentation.yaml | übernehmen | Fachlicher FZulG-Dokutrack, kein Statusmonolith. |
| ⚓ generate_dashboard.py | durch V2-Mechanik ersetzt | Zentraler Kernel-Generator aus generated/index.yaml (II.7). **OFFEN (2026-07-26):** dieses Ersatzstück EXISTIERT NICHT — `team-kits/kernel/**` enthält keinen Dashboard-Code und keinen `dashboard.html`-Produzenten (der einzige Produzent ist `templates/repo/scripts/generate_dashboard.py` im dev-Kit). Stand nach dem Lockstep: dev hat einen Generator, research hat **kein Dashboard** (`research-team/templates/project_memory/README.md` listet konsequent nur `index.yaml, session_brief.yaml`). Zu entscheiden: den dev-Generator spiegeln (dann greift der abgeleitete Mirror-Pin in `test_shared_kit_files_identical` automatisch) ODER II.7 für research ausdrücklich als „kein Dashboard“ beschließen. Gilt gleichlautend für Zeile 384 und für die „Index/Dashboard atomar im Kernel“-Begründungen in Zeile 113 (dev) und 336 (research). **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** die research-Verfassung hatte Variante 2 als Faktum gesetzt („no dashboard generator ships any more“) — zurückgenommen auf die bloße Tatsachenaussage; **der Entscheid ist weiter OFFEN und gehört dem User**, nicht einer Instruktionsdatei. |
| hypotheses.yaml | durch V2-Mechanik ersetzt | → hypotheses/active/HYP-nnnn.yaml (II.2). |
| literature.yaml | übernehmen | Fachliche Literatursammlung. |
| ⚓ masterplan.md | anpassen | → product/masterplan.md ohne progress-Referenz (II.2/II.11/4). |
| methodology.yaml | übernehmen | Methodik-Referenz, keine Statusquelle. |
| progress.dashboard.template.html | durch V2-Mechanik ersetzt | V2-Dashboard-Sichten, keine committete History (II.7). **OFFEN (2026-07-26):** Shell und Generator sind eine Einheit — siehe den OFFEN-Vermerk in Zeile 379; ohne Kernel-Generator hat research auch keine Shell. |
| ⚓ progress.yaml | durch V2-Mechanik ersetzt | → generated/session_brief.yaml (II.2). |
| project_config.yaml | anpassen | providers/preset/repo_mode (II.8/II.10a). |
| protocol_amendments.yaml | durch V2-Mechanik ersetzt | Änderungen bestätigter Revisionen → CR-Items (II.2). |
| reports/assets/auto-render.min.js | übernehmen | Report-Rendering-Asset. |
| reports/assets/fonts/KaTeX_AMS-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Caligraphic-Bold.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Caligraphic-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Fraktur-Bold.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Fraktur-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Main-Bold.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Main-BoldItalic.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Main-Italic.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Main-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Math-BoldItalic.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Math-Italic.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_SansSerif-Bold.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_SansSerif-Italic.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_SansSerif-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Script-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Size1-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Size2-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Size3-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Size4-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/fonts/KaTeX_Typewriter-Regular.woff2 | übernehmen | KaTeX-Font-Asset. |
| reports/assets/katex.min.css | übernehmen | KaTeX-Rendering-Asset. |
| reports/assets/katex.min.js | übernehmen | KaTeX-Rendering-Asset. |
| reports/experiment_report.template.html | übernehmen | Report-Template (Evidence-Ausgabe) bleibt. |
| reports/scientific_report.template.tex | übernehmen | LaTeX-Report-Template bleibt. |
| research_guidelines.yaml | übernehmen | Craft-Guideline. |
| research_questions.yaml | durch V2-Mechanik ersetzt | → research/active/RQ-nnnn.yaml (II.2). |
| results.yaml | durch V2-Mechanik ersetzt | → Evidence/EXP (II.2). |
| ⚓ review_findings.yaml | durch V2-Mechanik ersetzt | Befunde → BUG/CR/TSK+Evidence (II.10a). |
| review_reports.yaml | durch V2-Mechanik ersetzt | → Evidence-Dateien (II.2). |
| ⚓ tasks.yaml | durch V2-Mechanik ersetzt | → tasks/active/TSK-nnnn.yaml (II.2). |
| validation_reports.yaml | durch V2-Mechanik ersetzt | → Evidence (II.2). |
| validity_criteria.yaml | anpassen | → INV-Items mit check-Testreferenz (II.2/II.6). |

**research-team/templates/repo:**

| pfad | disposition | begründung |
|---|---|---|
| .claude/claude-security-guidance.md | übernehmen | Sicherheitsleitfaden, kit-unabhängig. **Nachtrag 2026-07-26 (Abweichung von „übernehmen“, begründet):** mitgezogen, weil der Pfad-Scope kit-neutral ist und die Datei `dashboard_history/**` nannte, das nicht mehr existiert — ein „übernehmen“ hätte einen toten Pfad ausgeliefert. Die Datei stand in KEINER Mirror-Menge (weder `validate.MIRROR_DEV_RESEARCH` noch `test_shared_kit_files_identical`), obwohl beide Kopien immer identisch waren; sie ist jetzt in `MIRROR_DEV_RESEARCH` aufgenommen, damit die Identität ab der nächsten Runde geprüft ist. Die office-Kopie ist inhaltlich eine andere Datei (Dokumenten-Workspace) und bleibt aus jeder Mirror-Menge. |
| .github/workflows/ci.yml | anpassen | State-Validator + ID-Eindeutigkeit + Latenz-Bench statt Monolith-Checks (II.4/II.5). |
| .gitignore | anpassen | + generated/**, kit_state.json, Lock (II.2/II.8). |
| .pre-commit-config.yaml | anpassen | V2-State-Validator/quality aufrufen (II.4). |
| hours.md | übernehmen | FZulG-Stundenerfassung, fachlich. |
| requirements-dev.txt | übernehmen | Dev-Deps. |
| ruff.toml | übernehmen | Lint-Config. |
| scripts/kit_browser_checks.py | übernehmen | Browser-Smoke-Checks (Kit-Mechanik). |
| ⚓ scripts/kit_checks.py | anpassen | Selbsttests auf typisierte Struktur/State-Validator (II.11/2). **Erledigt 2026-07-26:** `check_state_validity` ruft `report.validate_state` über die Hook-Bridge, spiegelidentisch in dev. |
| scripts/quality.py | anpassen | Fast-Mode/Quality-Gate-Definition (II.10a). |
| ⚓ scripts/retro.py | anpassen | Liest typisierte Items/Evidence statt progress/tasks (II.11/2). Spiegel von dev; die dort notierte offene Auditor-Routine-Anbindung gilt hier gleich. |

**user/:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ claude/CLAUDE.md | anpassen | Globale Entry-Gate auf V2-Flow (Details Abschnitt 6.2). |
| claude/settings.json | übernehmen | Globale User-Defaults, kit-unabhängig. |
| claude/statusline.py | übernehmen | Lokale Statusline, unverändert. |
| ⚓ codex/AGENTS.md | anpassen | Codex-Entry-Gate auf V2-Flow (Details Abschnitt 6.2). |
| codex_global_config.py | übernehmen | Opt-in Codex-Secret-Shield, kit-unabhängig. |
| merge_settings.py | übernehmen | Settings-Merge-Helfer, kit-unabhängig. |

---

## 2. Lockstep-Disposition (80 ⚓-Dateien)

**Messwert vs. Schätzung:** Die v2.1 nennt „~76" (Grep über 6 Monolith-Namen). Phase 0 misst
mit der ERWEITERTEN 7-Namen-Liste (v2.1 fügt `architecture.yaml` hinzu, wegen
`gate_packaging_decision`) 79 Grep-Treffer: 41 in Teil 1 + 38 in Teil 2 — **plus 1
Nicht-Grep-Mitglied**: `research/hooks/gate_memory_complete.py`, das über seinen
masterplan-Check (:162–164) an masterplan.md koppelt und von Spec II.11/0(a) ausdrücklich
als Lockstep-Mitglied benannt ist (Fable-Check-3-Fund) → **80 Dateien gesamt**. Davon sind
2 rein historisch/dokumentarisch (HARNESS_LOG.md: übernehmen; README.md: Doku-Anpassung) —
die verbleibenden **78** sind enforcement- oder inhaltlich gekoppelt und Bestandteil des
EINEN atomaren Release (II.11/2): kein Teilrelease entfernt einen Monolithen, solange
irgendein Gate/Skript/Template ihn erwartet.

**Teil 1 (41):** HARNESS_LOG.md · README.md · dev/constitution/AGENTS.md ·
dev/agents/{product-designer, project-manager}.md · dev/hooks/{auto_dashboard, gate_git,
gate_memory_complete, gate_packaging_decision, gate_pipeline, gate_test_coverage,
guard_no_adhoc, guard_yaml_valid, session_status}.py · dev/skills/{backend-developer,
devops-engineer, frontend-developer, product-designer, project-auditor, project-manager,
quality-engineer, research-engineer, software-architect}/SKILL.md ·
dev/templates/project_memory/{README.md, architecture.yaml, definition_of_done.yaml,
design.yaml, feature_requests.yaml, generate_dashboard.py, masterplan.md,
product_requirements.yaml, progress.yaml, review_findings.yaml, system_requirements.yaml,
tasks.yaml, testing_guidelines.yaml} · dev/templates/repo/scripts/{kit_checks, retro}.py ·
tools/{eval/scenarios.yaml, test_e2e.py, test_hooks.py}

**Teil 2 (39):** team-kits-Root: init_project_memory.{ps1,sh} · scaffold_team.{ps1,sh} ·
office: agents/records-clerk.md · constitution/AGENTS.md · hooks/{gate_filing,
guard_yaml_valid, session_status}.py · skills/{office-manager, project-auditor,
records-clerk}/SKILL.md · templates/project_memory/{README.md, filing_log.yaml,
progress.yaml, review_findings.yaml} · templates/repo/{.gitignore, inbox/README.txt} ·
research: agents/project-manager.md · constitution/AGENTS.md · hooks/{auto_dashboard,
gate_memory_complete (⚓* masterplan-Check :162–164), guard_no_adhoc, guard_yaml_valid,
session_status}.py · skills/{data-analyst,
project-auditor, project-manager, researcher}/SKILL.md · templates/project_memory/{README.md,
generate_dashboard.py, masterplan.md, progress.yaml, review_findings.yaml, tasks.yaml} ·
templates/repo/scripts/{kit_checks, retro}.py · user/{claude/CLAUDE.md, codex/AGENTS.md}

---

## 3. Verhaltens-Paritätsmatrix (116 Regeln)

Quellen-Kürzel: `dev/off/res` = Kit · `AGENTS` = constitution/AGENTS.md · `pm`/`om` =
Lead-agents-Datei · `pm-sk`/`om-sk` = Lead-SKILL · Spezialisten: `arch, be, fe, qa, design,
audit, re, devops` (dev) · `clerk, book, editor, curator, compl, mkt, odev, audit` (off) ·
`method, rschr, analyst, review, writer, audit, re` (res).
v2.1-Gate-Kürzel: GS1 Spawn-Form · GS2 gate_dispatch · GS3 Write-Scope · GS4
State-Validator · GS5 CI/Merge · APR2 Zwei-Phasen-Freigabeprotokoll.

| # | Regel (Kurzform) | Quelle(n) | Klassifikation |
|---|---|---|---|
| 1 | Deutsch zum User, Code/Artefakte Englisch | dev/AGENTS:4; off/AGENTS:4-6; res/AGENTS:4; dev/pm:15; off/om:14-15; res/pm:15 | behalten (min-keep) |
| 2 | Dokumentinhalt bleibt Originalsprache | off/AGENTS:6; off/om:15 | behalten |
| 3 | Orchestrator schreibt keinen Produktcode | dev/AGENTS:57; dev/pm:19; res/AGENTS:56; res/pm:20; off/om:20-22 | durch Gate ersetzt (→GS3; heute guard_pm_scope) |
| 4 | Kein Spawn ohne freigegebenen Task / Userfreigabe | dev/AGENTS:39; off/AGENTS:36-37; dev/pm-sk:81-88 | durch Gate ersetzt (→GS2 + analysis-APR) |
| 5 | „Ein Writer pro Datei" (PM pflegt project_memory) | dev/AGENTS:48,122-133; off/AGENTS:82,156-169; res/AGENTS:45,117-129 | bewusst geändert (Kernel wird einziger Schreiber; Rollen liefern Envelopes, II.1) |
| 6 | Single Source of Truth; keine Ad-hoc-Dateien | dev/AGENTS:44-47; off/AGENTS:47-50; res/AGENTS:42-44 | durch Gate ersetzt (→GS3+GS4) |
| 7 | Kein DONE/Merge ohne QA-PASS in Reports | dev/AGENTS:51-52; res/AGENTS:48-49; dev/pm-sk:105-108 | durch Gate ersetzt (→GS4 DONE→VALIDATED via Evidence; GS5) — **korrigiert 2026-07-26:** GS5 ist NICHT wirksam; `gate_git` verlangt weiter einen V1-`project_memory/*report*.yaml` und blockt daher JEDEN merge/push, ohne dass Evidence ihn lösen kann (Dispositionszeile 115/338 offen). Bis dahin: Prosa-Pflicht, ehrlich in den Verfassungszeilen benannt |
| 8 | Nur Produktfragen an User; Technik ans Team | dev/AGENTS:53; res/AGENTS:50; off/AGENTS:113-114 | behalten — **kein Gate (R2)** |
| 9 | Technische Frage an User = Defekt | dev/AGENTS:200-203; res/AGENTS:179-181 | behalten — **kein Gate (R2)** |
| 10 | Anti-Sycophancy: nie stumm zustimmen | dev/AGENTS:198; res/AGENTS:176-177; off/AGENTS:186 | behalten |
| 11 | Immer eine Option empfehlen | dev/AGENTS:199; res/AGENTS:178; dev/pm-sk:124 | behalten |
| 12 | Eigeninitiative 3 Stufen; nie eigenmächtig | dev/AGENTS:204-207; res/AGENTS:182-184 | behalten |
| 13 | Vor Vorschlag bestehende Items lesen; nie duplizieren | dev/AGENTS:54; res/AGENTS:52 | behalten (GS5 ID-Eindeutigkeit stützt) |
| 14 | Guidelines VOR Implementierung | dev/AGENTS:56; res/AGENTS:53-55; arch:59-62; method:35-43 | durch Gate ersetzt (→guard_guidelines; ggf. INV/SR) — **korrigiert 2026-07-26:** `guard_guidelines` ist KONDITIONAL (ohne `coding_guidelines.yaml` exit 0) und V2 liefert kein Template dafür; die Datei kann derzeit auch von niemandem angelegt werden (`gate_write_scope`). Im Default-V2-Projekt also **behalten (Prosa)** bis die Heimat des Knopfes entschieden ist (Zeilen 156/189) |
| 15 | Nur installierte Rolle; kein Generic/zweiter PM; explizites run_in_background | dev/AGENTS:38-40; off/AGENTS:38-41; res/AGENTS:35-38 | durch Gate ersetzt (→GS1+GS2) |
| 16 | Nach Parallelarbeit alle Ergebnisse abwarten | dev/AGENTS:40; res/AGENTS:38 | behalten |
| 17 | Gleiche Dateien serialisieren | dev/pm-sk:90-93 | durch Gate ersetzt (→GS3 + Kernel-Lock) |
| 18 | Pflicht-Work-Order-Template | dev/pm-sk:85-88; res/pm-sk:36-37; off/om-sk:37-39 | durch Gate ersetzt (→GS2; TSK-Pflichtfelder) |
| 19 | Output-Contract (summary/verdict) sonst Block | dev/AGENTS:68; off/AGENTS:99; res/AGENTS:68 | durch Gate ersetzt (→Envelope-Schema/submit-result) |
| 20 | Claims gegen Artefakte verifizieren | dev/pm:67; off/om-sk:40 | behalten |
| 21 | Startup-Gate: kein Spawn vor bestätigtem Preset | dev/AGENTS:24-25; off/AGENTS:21-22; res/AGENTS:24 | behalten (II.10a Erster Projektstart) |
| 22 | Draft-Pickup: nie Discovery bei Null | dev/AGENTS:22-23; res/AGENTS:22-23 | behalten (masterplan eingefroren) |
| 23 | Masterplan kritisch prüfen | dev/pm-sk:18-27; res/pm:43 | behalten — **kein Gate (R13)** |
| 24 | Änderung an APPROVED nur via CR+Freigabe | dev/AGENTS:100-102,144-150; res/AGENTS:96-97 | durch Gate ersetzt (→Freigabe-Invalidierung, II.2) |
| 25 | Sichtbares UI-Element entfernen = IMMER CR | dev/AGENTS:146-148; fe:40; qa:33; design:93 | durch Test ersetzt — **nicht in II.12 (R5)** |
| 26 | BUG → Regressionstest (rot vor Fix) | dev/AGENTS:149-150; qa:81-83 | durch Gate+Test ersetzt (BUG VERIFIED via Evidence) |
| 27 | Branch pro PRD/RQ (`feat/PRD-…`) | dev/AGENTS:154; res/AGENTS:137 | bewusst geändert (V2 `<typ>/<ITEM-ID>-<slug>`, II.10) |
| 28 | Conventional Commits pro Task | dev/AGENTS:154; res/AGENTS:137; off/AGENTS:196 | behalten |
| 29 | Push nur nach expliziter Userfreigabe | dev/AGENTS:156; res/AGENTS:138; off/AGENTS:198 | behalten — **kein Consent-Gate (R1)** |
| 30 | Nie force-push | dev/AGENTS:156; devops:49 | durch Gate ersetzt (→gate_git, GS5) |
| 31 | Nie auf dirty Worktree arbeiten | dev/AGENTS:156; res/AGENTS:139; dev/pm:72 | behalten (Migration gated; Normalfall **R11**) |
| 32 | End-of-Phase: YAML→Dashboard→Commit | dev/AGENTS:49-50; res/AGENTS:46-47 | bewusst geändert (Index atomar im Kernel, II.2/II.7) |
| 33 | progress.yaml ONE-Line + append-only log | dev/pm-sk:118-123; off/om-sk:45; res/pm-sk:60-61 | bewusst entfernt (progress.yaml entfällt → session_brief, II.2/II.5) |
| 34 | Dashboard nur generiert | dev/AGENTS:141; res/AGENTS:133; off/AGENTS:168 | durch Gate ersetzt — **präzisiert 2026-07-26 (Gegenprüfung 2):** der Mechanismus ist nicht „nicht committet“, sondern `gate_write_scope`: der einzige Produzent schreibt nach `project_memory/generated/`, und dorthin ist JEDER Tool-Write gesperrt (gemessen). Der dev-Satz „`progress.dashboard.html` is generated only, **never hand-edited**“ ist mit §6a restlos gestrichen (nur die Vollständigkeits-Regel derselben Passage wurde nach §6 gerettet); office/research behalten je eine Textfassung („generated/ is kernel output, never hand-edited“). |
| 35 | Pflicht-YAML-Vollständigkeit bei Abnahme | dev/AGENTS:139-140; res/AGENTS:131-132 | durch Gate ersetzt (→gate_memory_complete-Nachfolger; GS4) |
| 36 | Kein Projektstatus in Agent-Memory | dev/AGENTS:18-21; off/AGENTS:17-20; res/AGENTS:19-21 | durch Gate ersetzt (→guard_memory_budget + GS4) |
| 37 | MEMORY.md INDEX ≤40 Zeilen | dev/AGENTS:21; off/AGENTS:20; res/AGENTS:21 | durch Gate ersetzt (→guard_memory_budget; II.12) |
| 38 | Enforcement-Layer tabu (Settings/Hooks) | dev/AGENTS:84-87; res/AGENTS:81-83; off/AGENTS:189-192 | behalten (→guard_harness_selfmod, II.4) |
| 39 | Fehlblockende Guard = Defekt melden, nie umgehen | dev/AGENTS:86-87; dev/pm-sk:162-170 | behalten |
| 40 | Fragen von Prosa eingeleitet; Ask-Loops begrenzt | dev/AGENTS:91-92; off/AGENTS:112-114 | behalten |
| 41 | Fragen selbst-enthaltend, nie „oben" | dev/pm-sk:34-40; off/om-sk:24-28; res/pm-sk:23-27 | durch Gate ersetzt (→guard_question_context; APR2) |
| 42 | Presets mechanisch; Upgrade=OK→Scaffold→Restart | dev/AGENTS:170-172; res/AGENTS:153-154 | behalten |
| 43 | Modell-Eskalationsleiter user-gated | dev/AGENTS:173-179; res/AGENTS:155-160 | behalten |
| 44 | Codex-TOMLs read-only; nur Full-Scaffold | dev/AGENTS:180-184; off/AGENTS:177-180 | behalten |
| 45 | Nach 3 QA-Fails: STOP + Optionen | dev/AGENTS:212-214; res/AGENTS:189-191 | behalten |
| 46 | Toter Spezialist: 1 Retry, dann eskalieren | dev/AGENTS:213-214 | behalten (Lease-Timeout→READY gated) |
| 47 | Tech-Debt geflaggt, nie still refactoren | dev/AGENTS:188; res/AGENTS:168-169; arch:66 | behalten |
| 48 | Flags/Findings verpuffen nicht (TSK oder Skip-Log) | dev/AGENTS:190-194; res/AGENTS:170-172 | durch Gate ersetzt (→Auditor-Routine, II.10a) |
| 49 | File-Budget harte Grenze | dev/AGENTS:75,192-193; audit:26 | durch Gate ersetzt (→gate_pipeline / `scripts/kit_checks.py` + GS4) — **korrigiert 2026-07-25:** guard_memory_budget deckt NUR agent-memory, nicht das Quelldatei-Budget |
| 50 | Auditor täglich/PM-getriggert | dev/AGENTS:194; res/AGENTS:172 | bewusst geändert (wöchentlich+ereignisbasiert, APR routine, II.10a) |
| 51 | Auditor read-only; ein Lauf=ein review_findings-Eintrag | dev/audit:34-36; off/audit:34-36; res/audit:34-36 | bewusst geändert (read-only via APR-Scope+GS3; Evidence statt review_findings, II.10a) |
| 52 | Artefakte sofort aktuell; derives_from-Impact prüfen | dev/AGENTS:218-219; res/AGENTS:195 | durch Gate ersetzt (→GS4 Referenzgraph/Invalidierung) |
| 53 | Kit-Update pending-file-Contract; nie Scaffold-Wiederholung | dev/AGENTS:219-221; dev/pm-sk:172-190; res/pm-sk:72-90 | bewusst geändert (kit_state.json ersetzt restlos, II.8) |
| 54 | Session mit Versionswechsel: nicht delegieren, EIN Restart | dev/AGENTS:220; dev/pm-sk:176-179 | durch Gate ersetzt (→kit_state.json + /hooks-Trust, II.8) |
| 55 | Onboarding: read-only zuerst, User bestätigt | dev/pm-sk:147-152; res/pm-sk:104-109 | behalten (II.10a) |
| 56 | Work-Order nennt APPROVED PROC (office) | off/AGENTS:36-37,100; off/om:50-51 | durch Gate ersetzt (→gate_proc_approved OHNE Bootstrap-Loch) — **korrigiert 2026-07-26:** das Loch ist NICHT geschlossen; der Hook liest den gelöschten V1-Monolithen und exit(0) bei Abwesenheit, blockt also in jedem V2-Projekt nichts. Bis zur Umstellung **behalten (Prosa)**, so auch in Verfassung/Agent/SKILL formuliert |
| 57 | PROC-Edit entwertet Freigabe; re-hash bei User-OK | off/AGENTS:32-34; off/om:60 | durch Gate ersetzt (→Invalidierung PROC→DRAFT; Hash II.2) — **teilweise, korrigiert 2026-07-26:** die Invalidierung greift (Kernel hasht `steps`+`roles`), das RE-HASH nicht: `proc_hash.py` crasht am gelöschten Monolithen und der Kernel liefert kein Hash-Kommando, während `report.py` `approved_hash` bei APPROVED/ACTIVE als error verlangt |
| 58 | `processes:` muss Mapping bleiben | off/AGENTS:42-43 | bewusst geändert (PROC Per-Item; Monolith entfällt, II.9) |
| 59 | NICHTS wird gesendet; Outbound nur DRAFT in outbox/ | off/AGENTS:52-55; off/om:23-25; curator:23-24 | behalten — Codex nur Policy → **Teil-Enforcement (R4)** |
| 60 | Live-Shop-Mutation braucht PROC + Bestätigung | off/AGENTS:143; curator:24 | behalten |
| 61 | Ledger append-only + guard_ledger_direct | off/AGENTS:56-61; book:23-28 | bewusst geändert (I.3: Append-only ABGESCHAFFT; Guard GELÖSCHT; gate_ledger_valid) |
| 62 | Ledger-Zeilenvalidierung | off/AGENTS:58-59; book:23 | durch Gate ersetzt (→gate_ledger_valid, II.9/II.12) |
| 63 | Reports generiert, nie handgeschrieben | off/AGENTS:63-65; book:31-33 | behalten |
| 64 | Filing verifiziert; gate_filing blockt | off/AGENTS:66-68; clerk:22-24 | durch Gate ersetzt (→gate_filing; filing_log→Scan-Index) |
| 65 | fs_tripwire: nie Delete/Move auf inbox/archive | off/AGENTS:68-69; clerk:20-24 | durch Gate ersetzt (→guard_fs_tripwire/Integrity-Guard) |
| 66 | Unklassifizierbare Datei: unberührt + User fragen | clerk:26 | durch Test ersetzt (II.12 vorhanden) |
| 67 | filing_plan = einzige Maschinen-Wahrheit | clerk:16-20 | bewusst geändert (Ableitungsrichtung umgedreht, II.9) |
| 68 | Clerk löscht nie; Quarantäne; sha256-Dubletten | clerk:35-42 | behalten |
| 69 | Kein Steuer-/Rechtsrat; Disclaimer bleiben | off/AGENTS:70-73; book:9; compl:9,27 | behalten |
| 70 | Privacy-Honesty (kein DPA-Versprechen) | off/AGENTS:74-77 | behalten |
| 71 | Datenminimierung: Personennamen nur im Ledger | off/AGENTS:77-81; clerk:38-40 | behalten — **kein Gate (R3; 140-Namen-Vorfall)** |
| 72 | inbox/archive/outbox NICHT getrackt (GDPR) | off/AGENTS:196-198 | behalten (→Scaffold-.gitignore) |
| 73 | office-developer: nur konsumieren, nie mutieren | off/AGENTS:149-151; odev:16-20 | durch Gate ersetzt (→GS3 allowed_scope) |
| 74 | office-developer deterministisch+self-verify | odev:22-31 | behalten |
| 75 | product-editor einziger Produkttext-Writer | off/AGENTS:139; editor:22-26 | behalten (→GS3) |
| 76 | bookkeeper: UNCLEAR statt erfinden | book:17-27 | behalten |
| 77 | compliance: kein Eintrag ohne Quelle | compl:19-27 | behalten |
| 78 | marketing: keine Credentials; nichts posten | mkt:16-25 | behalten |
| 79 | shop-curator v1 read-only; Claims mit Quelle | curator:16-25 | behalten |
| 80 | Research-Guidelines (Repro/Seeds/kein p-Hacking) | res/AGENTS:53-55; rschr:16-19 | durch Gate ersetzt (→INV/gate_pipeline) — behavioral **R9** |
| 81 | Scientific Honesty | res/AGENTS:176-177; analyst:22-23 | behalten — **kein Gate (R9)** |
| 82 | Reproduzierbarkeit zuerst; Ausreißer nie still droppen | rschr:16-20; analyst:15-18 | durch Gate ersetzt (→Reviewer-Repro; gate_pipeline) |
| 83 | Report-Writer ändert nie Daten/Schlüsse | writer:11-12,44 | behalten |
| 84 | Report pro EXP sofort nach PASS; sonst incomplete | res/AGENTS:214-220; review:29-30 | behalten — **kein Gate (R7)** |
| 85 | FZulG-Regeln (Stunden, DOIs, ≤7 Jahre) | res/AGENTS:198-211; method:30-34 | behalten (Domänenregel) |
| 86 | Reviewer reproduziert; rote Pipeline/PII = FAIL | review:18-27 | durch Gate ersetzt (→gate_pipeline; GS5) |
| 87 | premise_invalidation_triggers-Re-Check | dev/AGENTS:167; arch:52-58; method:24-29 | behalten — **kein Gate (R8)** |
| 88 | research-engineer: Provenance/Checksums, nie fabrizieren | res/re:22-30 | durch Gate ersetzt + behalten |
| 89 | Architect hält Mermaid-Diagramm aktuell | arch:20-21 | bewusst geändert (→.drawio.svg-ARC; Mermaid nur ephemer, II.6a) |
| 90 | packaging.method Pflicht; Gate blockt TODO | arch:42-48; dev/AGENTS:78 | durch Gate ersetzt (→gate_packaging_decision auf Architektur-Item) |
| 91 | Richtige Domänen-Toolchain, nie aus Gedächtnis | arch:24-40; method:38-42 | behalten — **kein Gate** |
| 92 | Stacks deklariert; ohne Checks = FAIL | arch:40-41; devops:17 | durch Gate ersetzt (→gate_pipeline stacks) |
| 93 | Load-Test-Weglassen = explizite ADR-Zeile; STRIDE | arch:57-65 | behalten |
| 94 | testing_guidelines je Stack Pflicht; Coverage | qa:35-44; dev/AGENTS:76 | durch Gate ersetzt (→gate_test_coverage-Nachfolger) |
| 95 | Design-Fidelity: Build MUSS design matchen | qa:16-34; fe:23-41; design:88-102 | behalten (min-keep #9; →design_ref-Gate II.6a) |
| 96 | A11y-Audit (WCAG AA) = FAIL wenn fehlend | qa:26-29; design:81 | behalten |
| 97 | Consistency gemessen; UI-Inventar-Snapshot | qa:30-34; fe:38-41 | durch Test ersetzt — **nicht in II.12 (R5)** |
| 98 | Staged Testing; Vollsuite 1× pro Verdikt | qa:46-66; be:20-23; dev/pm-sk:98-104 | durch Gate ersetzt (→Fast Mode, II.10a) |
| 99 | real_run ist Testobjekt; SKIPPED ≠ PASS | qa:58-64; dev/pm-sk:109-117 | durch Test ersetzt (II.5 Regressionstests) |
| 100 | Delivery-Freshness: served Hash == Build | qa:64-66; fe:35-37 | behalten — **kein Gate/Test (R6)** |
| 101 | jsdom-grün ≠ Browser-grün | fe:29-31 | behalten |
| 102 | high/critical Security = FAIL; DoD vollständig | qa:70-80; devops:24 | durch Gate ersetzt (→gate_pipeline; GS4/GS5) — **korrigiert 2026-07-26:** die DoD-Hälfte trägt nicht. Der Ersatz für `definition_of_done.yaml` war „AC + `INV` mit existierendem Test“, und die INV-check-Existenzprüfung ist in `report.py` ausdrücklich AUFGESCHOBEN (Phase 2, B.2-10; gemessen null Findings). Jetzt als **Prüfpflicht der QA/Reviewer-Rolle** formuliert; Validator-Regel = offener Phase-2-Rest |
| 103 | perf-Regression >25% untersucht | qa:66,69 | behalten |
| 104 | Devs legen eigene TSKs an (TODO→…) | be:16-24; fe:17-42 | bewusst geändert (Kernel/Orchestrator legt Tasks VOR Spawn an; V2-Automat, II.2/II.3) |
| 105 | Mockup-as-Base; nie umfärben | fe:23-27; design:64-68 | behalten (min-keep #9) |
| 106 | Devs erfinden keine Dauerregeln; ändern nie SRs | be:25-30; fe:43-48 | durch Gate ersetzt (→GS3 forbidden_scope) |
| 107 | UI-Sequenz: kein neues UI-PRD vor Sichtung | dev/pm-sk:46-49 | behalten — **kein Gate (R12)** |
| 108 | Design-Ambition = User-Entscheid ZUERST | dev/pm-sk:57-70; design:104-109 | ~~durch Gate ersetzt~~ → **behalten (Prosa), korrigiert 2026-07-26:** es gibt kein Gate. `approvals.py`/`dispatch.py`/`report.py` kennen `WFR`/`wireframe` nirgends, und die II.6a-Freeze-Funktionen (`freeze_wireframe`/`freeze_design`/`freeze_architecture`) haben KEINEN Produktionsaufrufer (nur `tools/test_staging_cli.py`) und kein CLI-Subkommando. Das ist die Regel des synaipse-Vorfalls: sie steht jetzt ausdrücklich als Prosa-Pflicht mit dem PM als einzigem Wächter im Lead-SKILL. **Nachzubauen:** Freeze-Subkommandos + eine Validator-/Approval-Regel „UI-Scope ohne WFR blockt den scope-APR“ |
| 109 | Designer-Qualitätslatte non-negotiable | design:13-33 | behalten |
| 110 | Self-contained design_preview + per-view Mockups | design:52-68 | behalten (→DSN, II.6a) |
| 111 | Designer spricht nie direkt mit User | design:59,118 | behalten |
| 112 | DevOps pusht/deployt nie eigeninitiativ | devops:49-50; res/re:31 | behalten (→gate_git) — Consent-Teil **R1** |
| 113 | Fremde Docker-Projekte tabu | devops:46-48 | behalten — **kein Gate (R10)** |
| 114 | Compose-Projektname gepinnt | devops:40-45 | behalten (kit_checks warnt) |
| 115 | Partielle Läufe NIE Merge-Evidence | devops:56-58; qa:51 | durch Gate ersetzt (→Fast Mode, II.10a/II.12) |
| 116 | Pipeline bei Projektstart (Format→…→SCA) | devops:15-33; res/re:15-19 | durch Gate ersetzt (→gate_pipeline, GS5) |

**Minimum-Keep-Cross-Check (II.10a):** Alle 9 Items sind gedeckt — #1 behalten · #3→GS3 ·
#4→GS2 · #24 Invalidierung · #29 behalten (aber R1!) · #31 behalten (R11) · #8 behalten
(R2) · #7/#26→GS4/GS5 · #95/#105/#110 behalten+design_ref. ✓

---

## 4. Paritätsrisiken R1–R13 — Behandlungsvorschlag (DEIN Entscheidungsblock)

Regeln, die heute NUR Prosa sind und in v2.1 noch keinen Gate/Test haben. Ohne Behandlung
stürbe jede beim ≤150-Zeilen-Rückbau still — das verletzt die Sequenzregel „Gates vor
Kürzung" (II.5/II.11). Vorschlag je Risiko:

| R | Regel | Vorschlag | Kategorie |
|---|---|---|---|
| R1 | Push nur nach expliziter Userfreigabe (min-keep!) | **Phase-1-Gate:** gate_git-Erweiterung — `git push` nur mit gültigem, per Approval-Protokoll geprägtem Push-Token (**gleiche Mint-Code-Mechanik wie APR** — Amendment 2026-07-24, Options-Identität existiert plattformseitig nicht); + II.12-Test | Gate NEU |
| R2 | Entscheidungsgrenze Produkt/Technik | Prosa-Rest im schlanken Kern (nicht mechanisierbar) | behalten (Prosa) |
| R3 | Datenminimierung (140-Namen-Vorfall) | **Phase-1-CI-Check:** PII-Scan getrackter Dateien gegen Namensliste aus master_data.yaml (warn→block); .gitignore-Zwang für Manifeste bleibt | Test NEU |
| R4 | „Nichts senden" auf Codex nur Policy | Ehrlich in Capability-Matrix dokumentieren (audited); outbox-Only bleibt Prosa | dokumentierte Lücke |
| R5 | UI-Inventar-Snapshot / Element-Entfernung=CR | **II.12-Testfall nachtragen** (Ein-Zeiler; Snapshot-Assertion existiert als Muster in testing_guidelines) | Test NEU |
| R6 | Delivery-Freshness (served==Build-Hash) | **Phase-1-Check** in kit_browser_checks (Hash-Vergleich) + II.12-Ein-Zeiler | Test NEU |
| R7 | EXP ohne Report = incomplete | **Validator-Regel:** EXP→ANALYZED verlangt Report-Evidence | Gate NEU (klein) |
| R8 | premise_invalidation_triggers-Re-Check | **Validator-Flag:** Decision mit Triggern + neuer PR/CR ohne Re-Check-Vermerk → Warnung | Gate NEU (klein) |
| R9 | Scientific Honesty / kein p-Hacking | Prosa-Rest (behavioral; gate_pipeline deckt nur Repro/PII) | behalten (Prosa) |
| R10 | Fremde Docker-Projekte tabu | Optionaler Bash-Guard (deny docker stop/rm außerhalb Projekt-Compose) — Phase-1-Kandidat, sonst Prosa-Rest | optional Gate |
| R11 | Dirty-Worktree im Normalbetrieb | gate_git-Warnung bei risikoreichen Ops auf dirty tree — Phase-1-Kandidat, sonst Prosa-Rest | optional Gate |
| R12 | UI-Sequenzregel (4-Slices-Vorfall) | **Validator-Regel:** kein zweites UI-PR IN_DELIVERY, solange eines DELIVERED-nicht-ACCEPTED | Gate NEU (klein) |
| R13 | Masterplan kritisch prüfen | Prosa-Rest im schlanken Kern | behalten (Prosa) |

Empfehlung: R1, R3, R5, R6, R7, R8, R12 als feste Phase-1-Ergänzungen (Gates/Tests);
R10, R11 optional; R2, R9, R13 bewusst als Prosa-Rest; R4 als dokumentierte
Capability-Lücke. **Die „Prosa-Rest"-Regeln zählen ins ≤150-Zeilen-Budget des schlanken
Kerns — sie sind der bewusst behaltene Bestand.**

**USER-ENTSCHEID 2026-07-24: „Maximal härten"** — R10 und R11 werden FESTE Gates (nicht
optional); für R2/R9/R13 werden zusätzlich Warn-Heuristiken versucht (R2:
Technik-Vokabular-Warnung in Userfragen via guard_question_context; R9: Report-Lint auf
Overstatement-/Cherry-Picking-Marker; R13: Masterplan-Freigabefrage verlangt ein explizites
Kritik-/Risiken-Feld) — Heuristiken sind Warnungen, nie fail-closed (Fehlalarm-Risiko);
fällt eine Heuristik in der Praxis durch, bleibt die Regel Prosa-Rest. R4 bleibt
dokumentierte Capability-Lücke. Umsetzung: Gates/Tests in Phase 2 (Hooks), Heuristiken als
Phase-2-Experimente.

---

## 5. Spikes S1–S3 (Verdikte)

| Spike | Verdikt | Kern |
|---|---|---|
| **S1 Kernel-Lock** | **verified** (empirisch, 2026-07-24, Python 3.13.0/win32, lokales NTFS) | `O_CREAT\|O_EXCL` atomar (2. Acquire → FileExistsError); `os.replace` über existierendes Ziel OK; Stale-Break OK; Extended-Length-Pfad (`\\?\`) Write + replace bei 406 Zeichen OK. Fußnoten: OneDrive-Repos behalten die „Sync pausieren"-Auflage (II.13); Stale-Break-Implementierung muss PID/mtime VOR dem Delete re-checken (zwei Wartende dürfen keinen frischen Lock löschen). |
| **S2 AskUserQuestion-Provenance** | **ENTSCHIEDEN 2026-07-24 (empirisch): (a) verified, (c) verified, (b) NEGATIV für Claude Code 2.1.219** — Options-Identität existiert in DIESER Plattformversion nicht (Rohbelege: `evidence/2026-07-24-spike-payloads.md`; bei künftigen Versionen mit `tools/probes/` nachprüfen) | **Methode: Transkript-Forensik dieser Session** (keine Userprobe nötig — es lagen bereits echte Klick- UND Freitextantworten vor). Befund: `toolUseResult = {"answers": {Fragetext: Antwort-STRING}, "questions": [Echo]}`. Die geklickten Labels („Maximal härten", „Freigeben — Phase 1 starten") und eine vom User GETIPPTE Freitextantwort („Idee war: ein codex watcher …") stehen in **exakt derselben Struktur** — kein Options-Index, keine ID, kein Other-Flag. Konsequenz: v2.0-Forderung „Token bindet an Options-Identität" ist **nicht implementierbar**; ersetzt durch den **Mint-Code** (Label `Freigeben [7f3a2c]`, Entropie nur in der Option) — beiläufiger Freitext prägt nie. Capability-Wert = User-Entscheid (streng `unverified`→audited vs. amendiert `verified` mit Restrisiko). |
| **S3 agent_id-Bindung** | **verified — Ende-zu-Ende empirisch, BEIDE Bindungspunkte** (Claude Code 2.1.219; Rohbelege: `evidence/2026-07-24-spike-payloads.md`) | **Methode: headless `claude -p`-Lauf** im Probe-Repo (Hooks feuerten ohne Trust-Problem, Claude Code 2.1.219). Messung: `SubagentStart.agent_id = aa40f492c60fd0f31` → Kind-`PreToolUse(Write).agent_id = aa40f492c60fd0f31` (identisch) → `SubagentStop` gleiche ID; zusätzlich trägt `PostToolUse(Agent).tool_response` strukturiert `agentId` + `agentType` + `status` (in v2.1 als „undokumentiert" geführt — jetzt belegt, zusätzlich aus 9 Agent-Results dieser Session bestätigt). Parent-Hook hat `agent_id: null` = Hauptagent — exakt die Write-Scope-Semantik. → **`state_write_protection: verified` erreichbar**; die Lease darf an SubagentStart ODER an das Agent-Result gebunden werden. |

**Konsequenz Capability-Matrix (Stand 2026-07-24 NACH den Spikes):** Claude — `spawn_veto`
**verified** (PreToolUse Agent|Task produktiv belegt), `state_write_protection`
**verified** (S3 empirisch, s. o.), `approval_provenance` **offen zur Definition**: Der
Mint-Code-Mechanismus ist implementiert und schließt versehentliche Freigaben aus; die
v2.0-Forderung nach Options-Identität ist plattformseitig unerfüllbar. Streng gelesen bleibt
der Wert `unverified` → Gesamtmodus `audited`; nach amendierter Definition („wortgleiches,
entropietragendes Label aus dem Kernel-Set") wäre er `verified` mit dokumentiertem
Restrisiko (User tippt den Code bewusst ab). `hook_trust` = /hooks-Mechanik (II.8).
Codex — `spawn_veto` + `approval_provenance` konstruktionsbedingt unverified
(audited-Deckel beweisbar), `state_write_protection` erreichbar.

---

## 6. Einzeldispositionen

### 6.1 architecture.yaml / packaging
Monolith wird aufgelöst (II.6a): Diagramme → ARC-`.drawio.svg`-Items; components/data_flow
→ SRs bzw. schlankes Architektur-Item; **packaging.method** → Pflichtfeld am schlanken
Architektur-Item (+ Decision); `gate_packaging_decision.py` (harter Leser :84–89) wird IM
SELBEN atomaren Lockstep-Release umgestellt. Bestätigt durch die ⚓-Messung (beide Dateien
in der 79er-Liste).

### 6.2 masterplan.md + globale Entry-Gates (zeilengenau erhoben)
`product/masterplan.md` = eingefrorenes Discovery-Artefakt ohne Statusrolle. Nötige
V2-Änderungen:
- **user/claude/CLAUDE.md:** Z. 74 masterplan-Pfad+Framing · Z. 75 „DRAFT
  product_requirements.yaml PRD (PROPOSED)" → Draft-PR (`product/active/PR-0001.yaml`,
  DRAFT) UND „summary in progress.yaml" → entfällt (session_brief) · Z. 70–72 Init kopiert
  typisierte Struktur statt ~20 Monolith-Templates · Z. 94–97 „PRD"/Session-Start-Briefing
  → PR/session_brief · Z. 102–104 Free-mode-Aufzählung auf V2.
- **user/codex/AGENTS.md:** Z. 202–206 „PRD-xxxx in product_requirements.yaml (PROPOSED,
  complete:false)" → Draft-PR/RQ Per-Item (Status DRAFT, `complete` entfällt) ·
  Z. 210–212 progress.yaml-Status + append-only log: → entfällt (session_brief; Append-only
  per I.3 abgeschafft) · Z. 198–199 masterplan-Pfad · Z. 207–209/220 PROC-Bezug auf
  Per-Item · Z. 269 Free-mode-Aufzählung.

### 6.3 generated/-Git-Strategie
`generated/**`, `kit_state.json`, Kernel-Lock: NICHT committet (Scaffold-.gitignore),
vollständig regenerierbar; verhindert Merge-Konflikte generierter Artefakte (v2.1 II.2/II.8
— bestätigt, keine Abweichung nötig).

### 6.4 .codex/agents (Housekeeping — ENTSCHIEDEN 2026-07-24)
2 generator-verwaltete TOMLs. **User-Klärung:** Sie sind FUNKTIONALE Provider-Spiegel —
ein Codex- und ein Claude-Watcher, damit unabhängig vom genutzten Abo beide Watcher laufen.
**Disposition: committen/tracken** (wie die `.claude/agents/*.md`-Zwillinge); Schreibweg
bleibt ausschließlich der Generator (`gen_provider_artifacts.py`); der Commit erfolgt beim
nächsten vom User beauftragten Commit.

---

## 7. Freigabepunkte — **BESTÄTIGT 2026-07-24** (Punkt 2: „Maximal härten"; Punkt 4:
committen als funktionale Provider-Spiegel)

1. **Dispositionen bestätigen** (Abschnitt 1; insbesondere die 43 „ersetzt" und die 1
   Löschung guard_ledger_direct).
2. **R1–R13-Behandlung bestätigen** (Abschnitt 4 — Empfehlung: 7 feste
   Phase-1-Gates/Tests, 2 optionale, 3 Prosa-Rest, 1 dokumentierte Lücke).
3. **S3-Mechanik-Präzisierung bestätigen** (Lease-Bindung am SubagentStart statt
   PostToolUse(Agent) — kommt als kleine II.4-Präzisierung in die Spec, gleiche Garantie).
4. **.codex/-Housekeeping** (6.4: ignorieren empfohlen).
5. Kenntnisnahme: Lockstep = 80 (statt ~76; inkl. research gate_memory_complete via
   masterplan-Kopplung). **Erledigt seit dem Amendment 2026-07-24 (§5):** S2b und S3 sind
   empirisch entschieden — offen bleibt allein der Definitionsentscheid, ob
   `approval_provenance` mit Mint-Code als `verified` (mit dokumentiertem Restrisiko) oder
   streng als `unverified` (→ audited) geführt wird.

## 8. Nächster Schritt

**Erledigt (2026-07-24):** Phase 1 ist vollständig implementiert (State-Kernel + Schemas,
II.11/1) und die beiden Plattform-Spikes sind empirisch entschieden (§5) — die geplanten
10-Minuten-Userproben entfielen dadurch. **Nächster Schritt: Phase 2** (Hook-Schicht,
II.11/2) in frischer Session; jede Phase besteht ihre II.12-Abnahmetests UND eine
unabhängige Gegenprüfung (Arbeitsmodus 2026-07-24; Prüfmodell ab Phase 2: Opus 5).
