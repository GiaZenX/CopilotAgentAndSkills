# Review der Harness-V2-Spezifikation — Report (2026-07-24)

**Gegenstand:** v2.0-Spezifikation „Harness V2 — Auditbericht & Spezifikation"
(konsolidiert Claude ↔ Codex, 2026-07-20) — Verifikation der Teil-I-Befunde gegen die
echten Repos, fachliche Bewertung von Teil II, Ableitung der Amendments zur **v2.1**
(`docs/HARNESS_V2_SPEC.md`).

**Methodik:** 3 Opus-Explore-Agenten (Harness / synaipse+portfolio /
BuyPlugGo+Sessions+installierte Kits) · 1 Opus-Plan-Agent (adversariale Gegenprüfung +
Amendment-Design) · eigene Stichproben (design.yaml:7975–8029, :9205–9229;
guard_agent_spawn.py vollständig) · 3 Fable-Prüfungen (Delta-Abdeckungsmatrix,
v2.1-Volltextvergleich, Schritt-1-Kopierprüfung per MD5).

**Gesamturteil:** Die V2-Architektur trägt (Kernel als einziger Schreiber, Lease-Dispatch,
Zwei-Phasen-Freigabe, ehrliche hard/audited-Matrix, fail-closed) und ist im eigenen Repo
geerdet — das funktionierende Gegenmuster `gate_proc_approved` existiert real. Teil I
enthielt jedoch **zwei materielle Faktenfehler** (unten A.1/1–2), Teil II **16
Präzisierungslücken** und **11 Blind Spots**; alle sind in v2.1 aufgelöst. Drei
Plattform-Spikes (S1–S3) sind Bedingung vor Phase-1-Code.

---

## 1. Verdikttabelle Teil I (v2.0-Behauptung → Prüfergebnis)

| # | Behauptung (v2.0) | Verdikt | Kern-Evidenz |
|---|---|---|---|
| I.1.1 | guard_agent_spawn prüft nur Keywords/Rolle/run_in_background, kein project_memory | ✅ (auch selbst gegengelesen) | guard_agent_spawn.py:48–87; null project_memory-Referenzen |
| I.1.2 | office gate_proc_approved blockt ohne APPROVED PROC + Hash | ✅ mit Nuance | gate_proc_approved.py:68–88; **Bootstrap-Ausnahme Z. 72** (kein approved PROC → Spawns passieren) — v2.0 unerwähnt |
| I.1.3 | Monolith-Bloat inkl. „~150 SUPERSEDED-Marker" | ✅ Größen exakt, ⚠️ Marker ~10× übertrieben | tasks 961 KiB/15.004 Z./264 TSK, design 991 KiB/9.695 Z., SR 490 KiB exakt; exakte SUPERSEDED-Phrase **0×**, `SUPERSEDED` 14×, „historical record" 3× (design.yaml:2468/:4545/:4805) |
| I.1.4 | „CPU,GPU,RAM,ROM bindend; Code verletzt aktiv" | ❌ **Kern falsch** | „ROM" existiert nirgends (Kanon :8014: STORAGE); „binding user ruling" kommt 7× vor (:7897/:7982/:7999/:8039/:8088/:8196/:8217 — u. a. Row-Slot-Order, Equal-Heights), KEINES davon ist die Kartenreihenfolge (:8014 trägt das Label „DEFAULT (toggle 'grid')"); der Code folgt :9216 (User-Entscheidung 2026-07-19), deren `supersedes:` (:9220) das alte CPU-zuerst-Grid explizit ablöst |
| I.1.5 | Memory-Bloat; Sessions 905/157/71 MB | ✅ mit Korrekturen | 904/155/69,5 MB gemessen; synaipse 369 Sessions (nicht ~260); agent-memory 159 Dateien, aber 0,96 MiB (nicht 1,4 MB); MEMORY.md-Cap nur Prosa (AGENTS.md:21), kein Hook (Grep leer) |
| I.1.6 | BuyPlugGo archive/Legacy/Guideline | ✅ | archive 6.126; 4-Website 3.525 + 5-Shopify 845 = 4.370; Guideline 54.378 B „Stand: 2026-07-19 (v1.13)"; **Ledger ist CSV**; PROC-Store heißt `process_definitions.yaml` |
| I.1.7 | 4 Nag-Pfade in session_status.py | ✅, real ~6 Blöcke | :163–380; zusätzlich Transkript-Handover (:328–351) + project_memory-Read-Reminder (:198–215); portfolio-Nag seit 07-18 offen bestätigt (kit_update_pending.state, Repo auf 2026.07.17-9) |
| I.1.8 | Lockstep = 6 Hooks + Dashboard-Generator | ⚠️ **unvollständig** | zusätzlich guard_yaml_valid.py:130 (harter progress.yaml-Branch), auto_dashboard.py:53, `gate_packaging_decision.py`↔architecture.yaml (:84–89), 4 Scaffold-/Init-Skripte, kit_checks.py, retro.py, Cross-Kit-Kopien, globale CLAUDE.md — **76 Dateien repo-weit**; generate_dashboard.py ist ausgeliefertes TEMPLATE (liegt in den Projekten), kein Hook |

Extern gequellte Anker der Tabelle wurden am 2026-07-24 zusätzlich selbst gegengeprüft:
design.yaml „historical record" exakt :2468/:4545/:4805 ✓; „binding user ruling" 7
Vorkommen wie oben ✓; :8012–8014 („DEFAULT (toggle 'grid')… CPU, GPU, RAM, STORAGE") und
:9216/:9220 (`supersedes:`) selbst gelesen ✓; Guideline-Kopf „Stand: 2026-07-19 (v1.13)"
exakt ✓.

## 2. Korrekturen, die in v2.1 eingearbeitet wurden (A.1)

1. **I.1.4 neu geschrieben:** Der Code verletzt keine bindende Vorgabe — er folgt der
   neuesten dokumentierten User-Entscheidung (:9216), die per `supersedes:` (:9220,
   selbst nachgelesen) das alte Layout ablöst. Offene Frage (synaipse-Folgearbeit,
   User-Entscheid): bewusste Umsortierung vs. Transkriptionsfehler, inkl. Label ROM vs.
   STORAGE. **Meta-Punkt:** Sogar das v2.0-Audit transkribierte den Invariantenwert falsch
   („ROM") — der beste Beweis für strukturierte INV-Items mit Test-Referenz.
2. **I.1.3:** SUPERSEDED-Zahl korrigiert (14 statt ~150); „4 widersprüchliche
   Reihenfolgen" → „vier Order-Stellen, drei davon zur abgelösten Revision gehörig".
3. **Terminologie:** PROC-Store `process_definitions.yaml` (16 PROCs, alle mit
   approved_hash; Status ACTIVE/APPROVED/PROPOSED/RETIRED); Ledger = CSV
   (ledger/2025.csv 66,8 KB + 2026.csv 115,4 KB); Projekt-`filing_plan.yaml` existiert
   aktiv (102 Z., von gate_filing genutzt), ist aber „Derived 1:1 from … v1.11" und hängt
   der v1.13-Prosa hinterher — das Lag beweist die falsche Ableitungsrichtung, die V2
   umkehrt.
4. **I.1.8:** Lockstep auf die vollständige Phase-0-Disposition (76 Dateien) umgestellt.
5. **Messwerte überall nachgezogen:** 904/155/69,5 MB; Snapshots 3,42/2,36 MiB; 369
   Sessions; agent-memory 0,96 MiB; ~6 session_status-Blöcke.
6. **II.14/2 neu gefasst:** erst :9216-Klärung durch den User, DANN ggf. Code-Fix +
   Regressionstest.
7. **I.1.2-Nuance verankert:** Bootstrap-Loch-Schließung in II.4 + Paritätsmatrix.

## 3. Weitere verifizierte Fakten (Auswahl mit Evidenz)

- **proc_hash.py bestätigt die Hash-Sorge wörtlich:** `yaml.safe_dump(sort_keys=True,
  allow_unicode=True)`, keine NFC-Normalisierung, kein Versionsfeld, gehasht nur der
  `steps`-Teilbaum (office templates/repo/scripts/proc_hash.py:25–28).
- **Dashboard-Generator arbeitet bereits offline-korrekt:** liest YAMLs zur
  Generierungszeit, bettet JSON-Blob ein (`generate_dashboard.py`, render() :356–372) —
  v2.0-II.7 war nur unpräzise formuliert.
- **Subagent-Attribution existiert:** Hook-Payloads tragen `agent_id` bei
  Subagent-Tool-Calls (guard_pm_scope.py:65) → Mechanik-Grundlage des Write-Scope-Gates.
- **AskUserQuestion-Hook-Präzedenz existiert:** guard_question_context (alle Kits).
- **Codex-Deckel mechanisch belegt:** `gen_provider_artifacts.py:55–57` mappt
  `Agent|Task → None` UND `AskUserQuestion → None` → spawn_veto + approval_provenance auf
  Codex konstruktionsbedingt `unverified`; Write-Scope (Edit|Write→apply_patch) mappt.
- **Budget-Realität:** Verfassungen 174–220 Zeilen (je nach Zählweise), dev-Lead-SKILL
  196–210 — alle über dem ≤150-Ziel; „Lead-Paket ≤25 KB" hält nur ohne Verfassung
  (≈16 KB, lädt aber immer mit).
- **Kein Locking-Primitiv im Repo** — der v2.1-Kernel-Lock ist Neubau und
  Garantie-Voraussetzung (Lease-Exklusivität, Index-Atomarität, Hand-Edit-Sicherheit).
- **Kein Versionsdrift** installierte Kits ↔ Harness-Repo (alle drei 2026.07.18-3, Hashes
  identisch); BuyPlugGo eingebettet auf 2026.07.17-8 (eine Version zurück, kein
  Live-Nag), portfolio auf 2026.07.17-9 MIT offenem Nag, synaipse sauber auf -3.
- **Designer heute ohne Freeze:** design_preview.html + design.yaml, einziges
  deterministisches Gate `ambition:` (gate_memory_complete.py:178) — die
  V2-Design-Promotion ist Neubau; ARC/WFR nutzen denselben Kernel-Pfad.
- **Architektur heute:** `project_memory/architecture.yaml`-Monolith (components,
  data_flow, `mermaid:`-Block, packaging); Template-Ruling „Prefer Mermaid over draw.io"
  wird in v2.1 per User-Entscheid bewusst umgekehrt (Paritätsmatrix).

## 4. Migrationsdaten (für II.10, an realen Beständen erhoben)

- **V1-Statusvokabulare:** TSK: DONE/IN_PROGRESS/VALIDATED/TODO (synaipse 260/3/1;
  portfolio DONE 162, TODO 9) · PRD: TESTED(8)/ACCEPTED/APPROVED (synaipse),
  DONE(10)/APPROVED/ACCEPTED/PROPOSED(3) (portfolio) · SR: **DRAFT(217)/DONE(5)/ACTIVE(4)**
  (synaipse), ACTIVE(42) (portfolio) — das SR-Vokabular ist KOMPLETT disjunkt zu V2 ·
  PROC: ACTIVE(8)/APPROVED(3)/PROPOSED(1)/RETIRED(4) (BuyPlugGo).
- **Felddivergenzen:** synaipse-SR trägt rationale+area (keine acceptance_criteria),
  portfolio-SR umgekehrt; synaipse-TSK trägt `git{committed,pushed,commit_hash}`,
  `qa_failures`, `created/started/completed`; synaipse-PRD zusätzlich `ui_surface`;
  beide PRDs `complete/branch/milestone/closed`. → v2.1: Kernel-Zeitstempel am TSK,
  Commit-Belege in Evidence, Rest nach `legacy_fields` (verlustfrei).
- **Mapping-Tabelle:** siehe v2.1 II.10 (TODO→READY, TESTED→DELIVERED, DONE→ACCEPTED,
  PROPOSED→DRAFT, SR DRAFT→PROPOSED, SR ACTIVE/DONE→ACCEPTED; unbekannt → Block +
  Decision-Item).

## 5. Die 16 Präzisierungen (B.2) und 11 Blind Spots (D) — Kurzindex

**B.2 (je in v2.1 als Spec-Satz aufgelöst):** 1 Approval-Marker `[APR-REQ:<id>]` +
Exakt-Match auf Text+Header+Optionen + Bündelung · 2 Write-Scope via agent_id →
lease-Bindung · 3 Dashboard-Generierungszeit-Modell · 4 Kernel-Lock + Max-Scan-IDs ·
5 Envelope-/session_brief-Schemas + Budget-Zählweise · 6 DONE/VALIDATED-Semantik ·
7 Auditor-„Routine" = lokaler Scheduled Task · 8 kit_state/generated nicht committen ·
9 FR/PROC-Definitionsglättung · 10 INV.check {kind,ref} + Existenzprüfung · 11
Masterplan-Heimat + globale CLAUDE.md-Umstellung · 12 Budget-Trigger-Matrix · 13 Latenz
als p95-Bench, kein Gate · 14 Restore-Befehl in jeder Blockmeldung · 15
Status-Mapping-Tabelle + legacy_fields · 16 TSK-Zeitstempel/Evidence-Commit.

**D (je mit v2.1-Anker + Testfall):** 1 Lock als Garantie-Abhängigkeit · 2
„Other"-Option → Token bindet an Options-Identität · 3 generated/ gitignore +
Branchkonvention `<typ>/<ITEM-ID>-<slug>` + ID-Eindeutigkeit bei Merge + deterministische
Archivpfade · 4 Hand-Edit-Bypass → Dirty-Flag + Hash-Abgleich Gate 4 · 5 MAX_PATH `\\?\`
+ Validator >240 · 6 bounded stdin · 7 Research-Schema-Fix (EXP +revision/approval_ref,
HYP raus aus Invalidierungstabelle, 3-Hop-Denormalisierung) · 8 Codex-Parität beweisbar ·
9 Kürzungs-Sequenz (Gates vor Kürzung) · 10 „kein STATE-Compute in PostToolUse"
(Formatierung/Dirty-Flag erlaubt) · 11 Legacy-Freeze erst NACH Lockstep-Release.

## 6. Phase-0-Spikes (Bedingung vor Phase-1-Code)

- **S1 Kernel-Lock:** O_EXCL-Lockdatei + PID/TTL + Stale-Break auf Windows+OneDrive
  verifizieren.
- **S2 AskUserQuestion-Protokoll:** Feuert PostToolUse mit strukturierten
  `toolUseResult.answers` inkl. Options-Identität? Entscheidet, ob Provenance auf Claude
  `hard` kann.
- **S3 agent_id-Spawn-Bindung:** Liefert PostToolUse(Agent) die Kind-Agent-ID?
  Entscheidet `state_write_protection: verified`.

## 7. Fable-Vollständigkeitsprüfungen (Abdeckungsnachweis)

1. **Delta-Abdeckungsmatrix** (Review-Plan vs. v2.0): jede Sektion/Tabelle/Feldliste/
   Testgruppe disponiert; 14 Gaps + 4 Widersprüche gefunden → alle geschlossen.
2. **v2.1-Volltextvergleich** (Teil B vs. v2.0): „treue, vollständige v2.1" — kein
   Tabellen-, Feld-, Test- oder Prinzipienverlust; I.3/II.10a bis auf drei sanktionierte
   Präzisierungen wortgleich; letzte 4 Fixes (WFR-Freeze/Schema, Archivpfade,
   Changelog, Messwert-Quellung) eingearbeitet.
3. **Schritt-1-Kopierprüfung:** `docs/HARNESS_V2_SPEC.md` byte-identisch zu Teil B
   (MD5-Beweis), einzige Abweichung = beabsichtigte Titelzeile. **PASS.**

## 8. Befunde NUR für diesen Report (bewusst nicht in der Spec)

- **portfolio-Zusatzmonolithe** (Kontext für Folgearbeit II.14/1; Messwerte, KiB/Zeilen):
  system_requirements 123/1.406 · review_reports 121,1/1.298 · decisions 102,2/1.266 ·
  test_reports 99,6/1.065 · design 92,1/1.037 · tasks 85/260 (165 TSK) ·
  acceptance_reports 61/563 · research_notes 55,4/561 · progress 55,2/97 ·
  review_findings 43,1/378 · product_requirements 31,7/510 · architecture 18,1/313 ·
  changelog 7,6/107 — die Phase-0-/Migrations-Disposition muss den VOLLEN Satz behandeln
  (V2-Heimaten: decisions→decisions/, Reports→evidence/, changelog→Git,
  research_notes→prüfen).
- **`.codex/agents/` (untracked, im Harness-Repo):** 2 Codex-TOML-Spiegel der
  Watcher-Agents (codex-watcher.toml 4.086 B, radar-watcher.toml 4.455 B).
  Housekeeping-Entscheid des Users offen: committen oder ignorieren. Nicht V2-kritisch.
- **Sessiondaten Top 5** (`~/.claude/projects/`): BuyPlugGo 904 MB (421 Dateien/183
  Sessions) · synaipse 155 MB (492/369) · AgentAndSkills 71,2 MB · portfolio 69,5 MB
  (293/189) · Forschungsideen-wAIve 66,4 MB. → Aufbewahrungsregel bleibt separater
  Auftrag (II.14/4).

## 9. Entscheidungsprotokoll

- **2026-07-24 (dieses Review):** (1) Wireframes verpflichtend bei JEDEM UI-Scope, auch
  small (small-Sonderweg: Orchestrator darf WFR selbst erstellen); (2) Analyse-Freigaben
  gebündelt (eine APR deckt mehrere gelistete Analyse-Tasks); (3) Spec kanonisch in
  `docs/HARNESS_V2_SPEC.md`; (4) Arbeitsmodus der Umsetzung: schrittweise, nach JEDEM
  Schritt eine Fable-Gegenprüfung.
- **Unverändert verbindlich:** alle I.3-Entscheide (2026-07-20) und alle
  II.10a-Betriebsregeln.

## 10. Nächster Schritt

Phase 0 gemäß v2.1 II.11/0 (read-only): Vollinventar + Verhaltens-Paritätsmatrix +
vollständige ~76-Dateien-Lockstep-Disposition + Spikes S1–S3 + Dispositionen
(architecture.yaml/packaging, masterplan.md, generated/-Git-Strategie) →
Dispositionsbericht (`docs/reviews/phase0-disposition.md`) → **Userbestätigung vor
Phase 1**.
