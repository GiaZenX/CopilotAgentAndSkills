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
| ⚓ README.md | anpassen | Zentrale Doku wird auf V2 umgeschrieben (PR/RQ-Per-Item, kein progress.yaml/dashboard_history, draw.io-ARC/WFR, kit_state.json). |
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
| ⚓ constitution/AGENTS.md | anpassen | Umstellung auf V2-Zustandsmodell + Kürzung ≤150 Zeilen — Kürzung erst NACH Ersatz-Gates (II.5/II.11). |
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
| agents/project-auditor.md | anpassen | + Auditor als widerrufbare Routine-Freigabe, Befunde → Evidence/BUG (II.10a). |
| ⚓ agents/project-manager.md | anpassen | + Startup-Gate/Monolith-Reads auf Per-Item + kit_state.json. |
| agents/quality-engineer.md | anpassen | + QA gegen AC/Invarianten, Belege als Evidence. |
| agents/research-engineer.md | anpassen | s. geteilte Begründung. |
| agents/software-architect.md | anpassen | + Mermaid→draw.io-ARC bewusst umgekehrt (II.6a). |

**team-kits/dev-team/hooks:**

| pfad | disposition | begründung |
|---|---|---|
| hooks/_audit.py | anpassen | Audit-JSONL-Helfer bleibt; + Log-Rotation ~1 MB außerhalb des Startkontexts (II.5). |
| hooks/_compat.py | anpassen | Provider-Adapter bleibt Kern; + agent_id-/Lease-Payloads und begrenztes stdin-Read (II.4). |
| hooks/_root.py | übernehmen | Cwd-fester Repo-Root-Resolver, provider-neutral. |
| ⚓ hooks/auto_dashboard.py | durch V2-Mechanik ersetzt | Stop-/PostToolUse-Regenerator entfällt: Index/Dashboard atomar im Kernel; Update-Nag → kit_state.json (II.4/II.7/II.8). |
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
| ⚓ skills/product-designer/SKILL.md | anpassen | + WFR/DSN-Pipeline statt design.yaml (II.6a). |
| ⚓ skills/project-auditor/SKILL.md | anpassen | + Routine-Freigabe/Evidence-Fingerprint (II.10a). |
| ⚓ skills/project-manager/SKILL.md | anpassen | + Lead-SKILL ≤150 Zeilen, Draft-Pickup auf PR/masterplan ohne progress. |
| ⚓ skills/quality-engineer/SKILL.md | anpassen | + Prüfung gegen AC/Invarianten, Evidence-Ausgabe. |
| ⚓ skills/research-engineer/SKILL.md | anpassen | s. geteilte Begründung. |
| ⚓ skills/software-architect/SKILL.md | anpassen | + draw.io-ARC statt Mermaid, architecture.yaml-Auflösung (II.6a). |

**team-kits/dev-team/templates/project_memory** (Monolith-Stores → typisierte
Per-Item-Templates, II.2):

| pfad | disposition | begründung |
|---|---|---|
| ⚓ templates/project_memory/README.md | anpassen | Struktur-Doku → typisierte Per-Item-Ablage. |
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
| ⚓ templates/project_memory/generate_dashboard.py | anpassen | Liest künftig generated/index.yaml + aktive Items; dashboard_history entfällt; Lockstep (II.7/II.11/2). |
| ⚓ templates/project_memory/masterplan.md | anpassen | → product/masterplan.md, eingefroren, ohne progress-Referenz (II.2/II.11/4). |
| ⚓ templates/project_memory/product_requirements.yaml | durch V2-Mechanik ersetzt | → product/active/PR-nnnn.yaml (legacy_ids: [PRD-xxxx]). |
| templates/project_memory/progress.dashboard.template.html | anpassen | Shell erhält V2-Sichten; keine committete History (II.7). |
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
| ⚓ templates/repo/scripts/kit_checks.py | anpassen | yaml-lint/file-budget/module-invariants/enforcement-diff bleiben; progress.yaml-Vertragsprüfung entfällt (Lockstep II.11/2). |
| templates/repo/scripts/quality.py | anpassen | Quality-Pipeline bleibt (Fast-Mode II.10a); + Latenz-Bench. |
| ⚓ templates/repo/scripts/retro.py | anpassen | Read-only-Retro bleibt; Datenquellen Per-Item statt progress/tasks; Auditor-Routine-Anbindung. |

**tools:**

| pfad | disposition | begründung |
|---|---|---|
| tools/bump_kit_version.py | übernehmen | Versions-/Content-Hash-Stempelung bleibt. |
| tools/eval/README.md | übernehmen | Eval-Muster (Szenarien + LLM-Judge) bleibt gültig. |
| ⚓ tools/eval/scenarios.yaml | anpassen | Work-Orders/read_first auf V2-Item-Typen. |
| ⚓ tools/test_e2e.py | anpassen | E2E-Pfade auf V2-Flow (Draft-PR→SR→TSK, Approval, Lock); Fixtures Per-Item. |
| ⚓ tools/test_hooks.py | anpassen | Hook-Tests auf V2/gate_dispatch/Kernel (II.12-Matrix); Fixtures Per-Item. |
| tools/validate.py | anpassen | Self-Check prüft künftig typisierte Item-Templates + Schemadateien (Envelope/session_brief/ARC/WFR). |

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
| project-auditor.md | anpassen | Auditor wird Routine (APR.kind:routine) statt Delivery-Station (II.1/II.10a). |
| ⚓ records-clerk.md | anpassen | Filing gegen filing_plan.yaml-Wahrheit; filing_log wird Scan-Index (II.9). |
| shop-curator.md | anpassen | Wie bookkeeper. |

**office-team/constitution + hooks:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ constitution/AGENTS.md | anpassen | ≤150 Zeilen NACH Ersatzgates, V2-Zustandsmodell, Monolith-Refs raus (II.5/II.10a/II.11). |
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
| skills/bookkeeper/SKILL.md | anpassen | ≤-Budgets, Result-Envelope-Flow; Craft bleibt (II.5). |
| skills/compliance-researcher/SKILL.md | anpassen | Wie bookkeeper. |
| skills/marketing-planner/SKILL.md | anpassen | Wie bookkeeper. |
| skills/office-developer/SKILL.md | anpassen | Wie bookkeeper. |
| ⚓ skills/office-manager/SKILL.md | anpassen | Lead-SKILL ≤150 Zeilen, V2-Flow, Monolith-Refs raus (II.5). |
| skills/product-editor/SKILL.md | anpassen | Wie bookkeeper. |
| ⚓ skills/project-auditor/SKILL.md | anpassen | Routine mit APR.kind:routine, Fingerprint-Dedup (II.10a). |
| ⚓ skills/records-clerk/SKILL.md | anpassen | Filing gegen filing_plan.yaml (II.9). |
| skills/shop-curator/SKILL.md | anpassen | Wie bookkeeper. |

**office-team/templates/project_memory:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ README.md | anpassen | Auf typisierte V2-Verzeichnisstruktur umschreiben (II.2). |
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
| .claude/claude-security-guidance.md | übernehmen | Sicherheitsleitfaden, kit-unabhängig. |
| ⚓ .gitignore | anpassen | + generated/**, kit_state.json, Kernel-Lock (II.2/II.8). |
| archive/README.txt | übernehmen | Deterministische Archivpfade passen zu V2. |
| ⚓ inbox/README.txt | anpassen | Monolith-/filing_log-Referenz aktualisieren. |
| outbox/README.txt | übernehmen | Neutraler Ordnerhinweis. |
| requirements-office.txt | übernehmen | Python-Deps der Office-Skripte. |
| scripts/einvoice_extract.py | übernehmen | Fachliches E-Invoice-Tool. |
| scripts/euer_report.py | übernehmen | EÜR-Report liest die Ledger-CSV (V2-konform). |
| scripts/ledger_add.py | anpassen | Validierender Edit-/Importpfad vor atomarer Speicherung statt append-only (II.9). |
| scripts/proc_hash.py | durch V2-Mechanik ersetzt | Verallgemeinertes Hash-Modul im State-Kernel (kanonisches JSON+NFC+Version, II.2/II.11/1). |
| scripts/process_doc.py | anpassen | Auf Per-Item-PROC-Dateien umstellen (II.9). |

**research-team/agents:**

| pfad | disposition | begründung |
|---|---|---|
| data-analyst.md | anpassen | Result-Envelope-Flow; Craft bleibt. |
| methodologist.md | anpassen | Wie data-analyst. |
| project-auditor.md | anpassen | Auditor-Routine (APR.kind:routine, II.1/II.10a). |
| ⚓ project-manager.md | anpassen | Lead auf V2: Draft-RQ/State-Kernel, Monolith-Refs raus (II.2/II.3). |
| report-writer.md | anpassen | Wie data-analyst. |
| research-engineer.md | anpassen | Wie data-analyst. |
| researcher.md | anpassen | Wie data-analyst. |
| reviewer.md | anpassen | Wie data-analyst. |

**research-team/constitution + hooks:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ constitution/AGENTS.md | anpassen | ≤150 Zeilen, V2-Zustandsmodell RQ/HYP/EXP (II.5/II.11). |
| hooks/_audit.py | übernehmen | Audit-Helfer bleibt. |
| hooks/_compat.py | übernehmen | Provider-Shim bleibt. |
| hooks/_root.py | übernehmen | Git-Root-Resolver bleibt. |
| ⚓ hooks/auto_dashboard.py | durch V2-Mechanik ersetzt | Kernel-Index atomar + optionaler STALE-Flag statt PostToolUse-Regen (II.4/II.7). |
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
| skills/methodologist/SKILL.md | anpassen | ≤-Budgets, V2-Flow. |
| ⚓ skills/project-auditor/SKILL.md | anpassen | Auditor-Routine (II.10a). |
| ⚓ skills/project-manager/SKILL.md | anpassen | Lead-SKILL ≤150 Zeilen, RQ-Flow (II.5). |
| skills/report-writer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. |
| skills/research-engineer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. |
| ⚓ skills/researcher/SKILL.md | anpassen | ≤-Budgets, V2-Flow, Monolith-Refs raus (II.5). |
| skills/reviewer/SKILL.md | anpassen | ≤-Budgets, V2-Flow. |

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
| ⚓ generate_dashboard.py | durch V2-Mechanik ersetzt | Zentraler Kernel-Generator aus generated/index.yaml (II.7). |
| hypotheses.yaml | durch V2-Mechanik ersetzt | → hypotheses/active/HYP-nnnn.yaml (II.2). |
| literature.yaml | übernehmen | Fachliche Literatursammlung. |
| ⚓ masterplan.md | anpassen | → product/masterplan.md ohne progress-Referenz (II.2/II.11/4). |
| methodology.yaml | übernehmen | Methodik-Referenz, keine Statusquelle. |
| progress.dashboard.template.html | durch V2-Mechanik ersetzt | V2-Dashboard-Sichten, keine committete History (II.7). |
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
| .claude/claude-security-guidance.md | übernehmen | Sicherheitsleitfaden, kit-unabhängig. |
| .github/workflows/ci.yml | anpassen | State-Validator + ID-Eindeutigkeit + Latenz-Bench statt Monolith-Checks (II.4/II.5). |
| .gitignore | anpassen | + generated/**, kit_state.json, Lock (II.2/II.8). |
| .pre-commit-config.yaml | anpassen | V2-State-Validator/quality aufrufen (II.4). |
| hours.md | übernehmen | FZulG-Stundenerfassung, fachlich. |
| requirements-dev.txt | übernehmen | Dev-Deps. |
| ruff.toml | übernehmen | Lint-Config. |
| scripts/kit_browser_checks.py | übernehmen | Browser-Smoke-Checks (Kit-Mechanik). |
| ⚓ scripts/kit_checks.py | anpassen | Selbsttests auf typisierte Struktur/State-Validator (II.11/2). |
| scripts/quality.py | anpassen | Fast-Mode/Quality-Gate-Definition (II.10a). |
| ⚓ scripts/retro.py | anpassen | Liest typisierte Items/Evidence statt progress/tasks (II.11/2). |

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
| 7 | Kein DONE/Merge ohne QA-PASS in Reports | dev/AGENTS:51-52; res/AGENTS:48-49; dev/pm-sk:105-108 | durch Gate ersetzt (→GS4 DONE→VALIDATED via Evidence; GS5) |
| 8 | Nur Produktfragen an User; Technik ans Team | dev/AGENTS:53; res/AGENTS:50; off/AGENTS:113-114 | behalten — **kein Gate (R2)** |
| 9 | Technische Frage an User = Defekt | dev/AGENTS:200-203; res/AGENTS:179-181 | behalten — **kein Gate (R2)** |
| 10 | Anti-Sycophancy: nie stumm zustimmen | dev/AGENTS:198; res/AGENTS:176-177; off/AGENTS:186 | behalten |
| 11 | Immer eine Option empfehlen | dev/AGENTS:199; res/AGENTS:178; dev/pm-sk:124 | behalten |
| 12 | Eigeninitiative 3 Stufen; nie eigenmächtig | dev/AGENTS:204-207; res/AGENTS:182-184 | behalten |
| 13 | Vor Vorschlag bestehende Items lesen; nie duplizieren | dev/AGENTS:54; res/AGENTS:52 | behalten (GS5 ID-Eindeutigkeit stützt) |
| 14 | Guidelines VOR Implementierung | dev/AGENTS:56; res/AGENTS:53-55; arch:59-62; method:35-43 | durch Gate ersetzt (→guard_guidelines; ggf. INV/SR) |
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
| 34 | Dashboard nur generiert | dev/AGENTS:141; res/AGENTS:133; off/AGENTS:168 | durch Gate ersetzt (→generated/** nicht committet, GS4) |
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
| 56 | Work-Order nennt APPROVED PROC (office) | off/AGENTS:36-37,100; off/om:50-51 | durch Gate ersetzt (→gate_proc_approved OHNE Bootstrap-Loch) |
| 57 | PROC-Edit entwertet Freigabe; re-hash bei User-OK | off/AGENTS:32-34; off/om:60 | durch Gate ersetzt (→Invalidierung PROC→DRAFT; Hash II.2) |
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
| 102 | high/critical Security = FAIL; DoD vollständig | qa:70-80; devops:24 | durch Gate ersetzt (→gate_pipeline; GS4/GS5) |
| 103 | perf-Regression >25% untersucht | qa:66,69 | behalten |
| 104 | Devs legen eigene TSKs an (TODO→…) | be:16-24; fe:17-42 | bewusst geändert (Kernel/Orchestrator legt Tasks VOR Spawn an; V2-Automat, II.2/II.3) |
| 105 | Mockup-as-Base; nie umfärben | fe:23-27; design:64-68 | behalten (min-keep #9) |
| 106 | Devs erfinden keine Dauerregeln; ändern nie SRs | be:25-30; fe:43-48 | durch Gate ersetzt (→GS3 forbidden_scope) |
| 107 | UI-Sequenz: kein neues UI-PRD vor Sichtung | dev/pm-sk:46-49 | behalten — **kein Gate (R12)** |
| 108 | Design-Ambition = User-Entscheid ZUERST | dev/pm-sk:57-70; design:104-109 | durch Gate ersetzt (→WFR-Pflicht; scope-APR blockiert, II.6a) |
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
