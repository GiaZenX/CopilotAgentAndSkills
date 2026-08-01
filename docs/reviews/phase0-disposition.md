# Phase 0 — Dispositionsbericht (Vollinventar + Paritätsmatrix + Spikes)

**Status: ZUR USERBESTÄTIGUNG — Phase 1 startet erst nach Freigabe dieses Berichts**
(gemäß `docs/HARNESS_V2_SPEC.md` II.11/0 und II.12 „Phase-0-Abnahme")

**Datum:** 2026-07-24 · **Methodik:** read-only; 2 Opus-Inventar-Agenten (Teil 1: Root/dev-team/
tools/CI/.claude/radar/.codex · Teil 2: office/research/team-kits-Root/user), 1
Opus-Paritätsmatrix-Agent (24+ Dateien, 116 Regeln), 1 Claude-Code-Doku-Agent (Spikes S2/S3),
1 eigener empirischer Spike-Lauf (S1, Python 3.13.0/win32). Fable-Gegenprüfung dieses
Berichts folgt als Check 3 (Arbeitsmodus 2026-07-24).

**Kurzfazit:** 284 Dateien disponiert — 96 übernehmen · 144 anpassen · 43 durch V2-Mechanik
ersetzt · **1 bewusst
entfernen** (`guard_ledger_direct.py`, User-Entscheid I.3/1). Lockstep-Menge: **82 Dateien**
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

## 1. Vollinventar (284 Dateien)

| Disposition | Teil 1 | Teil 2 | Summe |
|---|---|---|---|
| übernehmen | 29 | 67 | **96** |
| anpassen | 58 | 86 | **144** |
| durch V2-Mechanik ersetzt | 20 | 23 | **43** |
| bewusst entfernen | 0 | 1 | **1** |
| **Summe** | **107** | **177** | **284** |

**Diese Zahlen werden GEZÄHLT, nicht gepflegt.** `tools/test_disposition.py` liest die Zeilen
der beiden Inventartabellen und vergleicht jede Zelle oben und jede Zahl im Kurzfazit damit;
eine nachgetragene Zeile ohne Summenkorrektur ist ab jetzt ein Testfehler. Genau das war
nötig: die Aufstellung stand bis 2026-07-31 auf 92/140/43/1 über 101+175=276, während die
Tabellen 95/144/43/1 über 106+177=283 tragen — vier Zahlen, alle vier zu klein, weil zehn
später nachgetragene Zeilen nie eingerechnet wurden und nichts das sagen konnte. Der erste
Anlauf der Ableitung zählte selbst falsch (280/141/80): sein Zeilenleser trennte an JEDEM `|`
und verlor damit lautlos die drei Zeilen, deren Text Hook-Matcher und Shell-Metazeichen zitiert
— eine unvollständige Zählung, die wie eine gepflegte aussieht. `_cells` trennt jetzt nur an
den Pipes ausserhalb von Code-Spans und ohne Backslash, und
`test_a_row_whose_description_contains_a_pipe_is_counted` ist der Boden dafür.

Die ursprüngliche Erhebung (2026-07-24) verglich diese Menge mit `git ls-files` = 274 plus den
zwei generator-verwalteten `.codex/agents/*.toml`. Dieser Abgleich ist historisch: die seither
nachgetragenen Zeilen sind nicht neu erhoben worden, und der Test oben prüft die Tabelle gegen
sich selbst, nicht gegen den Arbeitsbaum.

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
| ⚓ constitution/AGENTS.md | anpassen | Umstellung auf V2-Zustandsmodell + Kürzung ≤150 Zeilen — Kürzung erst NACH Ersatz-Gates (II.5/II.11). **Nachtrag 2026-07-26 (Lockstep-Gruppe „Verfassungen/Agents/Skills“, Opus-Gegenprüfung):** die Umstellung war sprachlich vollständig, behauptete aber sechs Mechanismen, die der laufende Code nicht hat. Jetzt ehrlich gemacht statt weiterbehauptet: (a) NEUER §0-Punkt „state directory is WRITE-LOCKED today“ — `gate_write_scope` sperrt JEDEN Tool-Write unter `project_memory/` (auch die Referenz-/Configdateien, für die es keine Ausnahme kennt), es gibt kein `harness`-Executable und kein `capture`/`approve`/Freeze-Kommando, ein direkter Kernel-Aufruf wird vom selben Gate abgelehnt ⇒ heute kann in KEINEM Kit ein Item oder `project_config.yaml` entstehen; der Satz gilt für alle `python scripts/harness.py …`-Nennungen der Datei. (b) `gate_git`-Zeile: nennt jetzt, dass der Hook einen V1-`*report*.yaml` verlangt und damit JEDEN merge/push blockt (letzte „PRD“-Stelle des Pakets entfernt). (c) `guard_guidelines`-Zeile + §2.7 konditional („nur solange das Projekt die Datei führt“). (d) `gate_test_coverage`-Zeile nennt `testing_guidelines.yaml` als Quelle der EXTRA-Areas. (e) §2.4 „no PR **leaves** DELIVERED“ → „REACHES“ + Vokabular auf `review`+`test`+`acceptance` vereinheitlicht. (f) §6 „ist CLOSED“ → „closed through its status automaton“ (`CLOSED` ist in `AUTOMATA` kein Status; office/research formulierten es schon richtig). (g) §9 „`ARC`/`WFR` haben keinen Automaten“ → Definition „nur die Typen in `AUTOMATA` haben einen“. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** CLI-Shim (`harness`, inkl. `capture`/`approve`/Freeze) + eine `gate_write_scope`-Ausnahme oder ein Nicht-kanonisch-Pfad für die Referenzdateien; solange beides fehlt, ist V2 ohne begehbaren Schreibweg. **Nachtrag 2026-07-26 (Gegenprüfung 2):** (h) der §0-Punkt deckte nur TOOL-Writes und den direkten Kernel-Aufruf; gemessen verweigert derselbe Gate über den `_ENFORCEMENT_RX`-Zweig auch JEDE schreibfähige Shell-Pipeline, die `.claude` oder `team-kits` NENNT — also die `init_project_memory`/`scaffold_team`-Aufrufe, die das Startup-Gate (Schritt 1) und §11/der Kit-Update-Absatz anordnen (rc=2, „names the enforcement layer in a pipeline that can write“). §0 nennt sie jetzt und weist sie dem USER zu. (i) §2 Item 2 sagte „No role writes a state file with an editor **or a shell** … `gate_write_scope` refuses it“; gemessen schreibt ein SKRIPT (`python scripts/oops.py`) ungehindert nach `product/active/` (rc=0, Datei entsteht) — genau darauf beruhen `scripts/retro.py` und `scripts/generate_dashboard.py`. Die Zeile sagt jetzt „jede Shell-Pipeline, deren KOMMANDOZEILE den Pfad nennt“ und benennt die Skript-Indirektion als offene Lücke. (j) §10 `premise_rechecks` sagt jetzt, dass das Feld am **PR/CR** hängt (nicht am DEC — `report.py:_check_premise_recheck` liest es nur dort). (k) die Auditor-Routine-Zeile ehrlich gemacht (siehe Zeile `agents/project-auditor.md`). **Nachtrag 2026-07-29 (Einstiegspunkt-Runde):** der `harness`-Einstieg IST jetzt installiert. Die Kits liefern `templates/repo/scripts/harness.py`, beide Scaffold-Skripte behandeln ihn KIT-OWNED (immer überschrieben, wie `scripts/kit_checks.py`), und die eine sanktionierte Schreibweise ist `python scripts/harness.py <cmd>` — in bash und PowerShell identisch, und beide Shells werden von denselben acht PreToolUse-Hooks gegatet. Der Shim liegt unter `scripts/`, weil `gate_write_scope` jede schreibfähige Pipeline ablehnt, deren KOMMANDOZEILE `.claude`/`.codex`/das Zustandsverzeichnis nennt (gemessen: `python -B .claude/kernel/cli.py doctor` → „names the enforcement layer"); er löst die Zustandswurzel selbst auf und weist ein `--root` in argv mit eigener Meldung ab (die Entscheidung trifft der ausgelieferte Parser über eine Sentinel-Default, deckt also auch `--r`/`--ro`/`--roo`). `sys.dont_write_bytecode = True` steht vor jedem Kernel-Import, gemessen 0 `.pyc` im gehashten Bündel nach `doctor`. Der §0-Punkt heisst deshalb nicht mehr „WRITE-LOCKED", sondern nennt den Einstieg UND die Lücke. **Nachtrag 2026-07-31 (Kommando-Runde):** vier der fünf sind jetzt auf der Oberfläche — `capture` (Item-Felder als JSON-Objekt auf STDIN; JSON, weil die Felder in Freigabe-Hashes eingehen und YAML 1.1 `no` zu false umtypt, und STDIN, weil `gate_write_scope` jede schreibfähige Kommandozeile ablehnt, die das Zustandsverzeichnis NENNT), `create-task`, `dispatch` (Lease + `HARNESS_DISPATCH`-Header — ohne dieses Kommando konnte in einem echten Projekt überhaupt keine Lease entstehen, also verweigerte `gate_dispatch` JEDEN Spawn) und `submit-result`. `approve` ist GETEILT statt fehlend: `request-approval <kind> <ITEM-ID>` schreibt den Pending-Request und gibt die kernelgenerierte Frage aus (Phase 1), geprägt wird nur durch die ANTWORT des Users — ohne dieses Kommando hatte `create_pending_request` keinen Aufrufer im ausgelieferten Baum, also konnte kein Wurzel-Item aus DRAFT (Befund der Gegenprüfung 2026-07-31). Nicht auf der Oberfläche bleibt `migrate --dry-run` (es gibt kein `kernel/migrate.py`). Ohne eigenen Schreiber bleiben `project_config.yaml`, `product/masterplan.md` und die ARC/WFR/DSN-Einfrierung (II.6a). Gemessen an einem von den Installern gebauten Projekt: alle vier Kommandozeilen passieren jede registrierte `Bash|PowerShell`-PreToolUse-Hürde und laufen dann durch. |
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
| agents/project-auditor.md | anpassen | + Auditor als widerrufbare Routine-Freigabe, Befunde → Evidence/BUG (II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:ROOT_DISPATCH_KINDS` = {scope, delivery}, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. **Nachtrag 2026-07-31 (Blocker-Runde): erledigt.** Der Kernel hat die Route — `dispatch.py:_covering_routine_apr`, als DRITTER Weg neben Root- und Analysis-Route und ausdrücklich NICHT durch Aufnahme von `routine` in `approvals.py:ROOT_DISPATCH_KINDS`: die Route bindet, was Spec II.2 bindet, sonst wäre sie ein Blankoscheck. Geprüft werden (a) die Freigabe selbst über `approvals.py:assert_apr_in_force` (widerrufen, Provenienz über die konsumierte Anfrage, fremdes Item, Ablauf — pro Dispatch neu, also auch zwischen Lease und Spawn), (b) die ROLLE aus dem geprägten Manifest gegen `TSK.assigned_role`, (c) READ-ONLY über `dispatch.py:_claims_writable_scope`: ein Task mit `allowed_scope` wird auf dieser Route abgelehnt, womit eine Routinefreigabe nie Implementierungsarbeit legitimiert. `approvals.py:ROUTINE_MANIFEST_FIELDS` macht Rolle/Scope/Trigger/Takt beim Anlegen der Anfrage zur Pflicht — eine Routine, die nichts bindet, wird dem User gar nicht erst zur Unterschrift vorgelegt. Gemessen vorher/nachher mit gültigem, unabgelaufenem, nicht widerrufenem routine-APR am Wurzel-Item und Audit-`TSK` READY: `create_lease` REFUSED → ALLOWED und `gate_dispatch` als echter PreToolUse-Prozess rc 0; abgelaufen, widerrufen, falsche Rolle, schreibender Scope und „ohne jede Freigabe“ bleiben verweigert, Scope-, Delivery- und Analysis-Route unverändert erlaubt. Die Rollentexte (`agents/project-auditor.md` + `skills/project-auditor/SKILL.md`, alle drei Kits) sagen jetzt beides. **Nicht geschlossen, benannt:** Trigger und Takt liegen im gehashten Manifest, aber kein Gate liest sie (die von II.10a geforderten `last_completed`/`next_due` haben keinen Produzenten), der Read-only-Scope des Manifests hat kein Lese-Gate, und KEIN Kommando der ausgelieferten Oberfläche erzeugt eine ablaufende Freigabe — `request-approval` bietet nur die item-abgeleiteten Arten, was `analysis` genauso trifft wie `routine`. Und: eine am Wurzel-Item geprägte Routine ZIEHT dessen `approval_ref` auf sich (der Mint schreibt das Feld für jede item-gebundene Freigabe), womit die Delivery-Route — die genau dieses eine Feld liest — für Implementierungs-Tasks unter dieser Wurzel bis zur erneuten Scope-Freigabe verweigert; gemessen und in `test_approvals_dispatch.py:test_minting_a_routine_on_a_live_root_takes_its_approval_ref` festgehalten. Die Interaktion ist älter als diese Route (eine item-gebundene `analysis` tut dasselbe), aber diese Route lädt sie erstmals ein. Nicht durch Aufweiten der Delivery-Route repariert: welche APR die trägt, ist eine daneben geschriebene Entscheidung und war in dieser Runde ausdrücklich unverändert zu halten. **Nachtrag 2026-07-31 (Gegenprüfung der Blocker-Runde):** vier Korrekturen. (a) READ-ONLY ist ein PLAN-Check, kein Sandkasten — gemessen an einem gebundenen Auditor mit leerem `allowed_scope` gegen alle acht registrierten `Bash`-Gates: `echo pwned > src/x.py`, `rm -rf src`, `git commit -am wip` je rc 0, während derselbe Pfad über `Write` rc 2 gibt (Sanity: eine Shell-Schreibung in den kanonischen State blockt weiterhin). Ursache: `gate_write_scope.handle_shell` löst den gebundenen Task nie auf und liest weder `allowed_scope` noch `forbidden_scope` — Regel 2 der Tabelle im eigenen Docstring existiert auf dem Shell-Pfad nicht, vorbestehend und für JEDEN gebundenen Spezialisten. Der Shell-Pfad wird in dieser Runde NICHT gebaut (eigenes Paket, eigene Gegenprüfung); stattdessen sagen alle vier ausgelieferten Stellen jetzt, was gebaut ist, und die Lücke ist als `known_hole` auf `state_write_protection.shell` festgenagelt — `doctor` führt die Capability dadurch `unverified`. (b) Die Rolle wird aus der GEPRÄGTEN Anfrage gelesen, nie aus der APR-Datei; `consumed_request` vergleicht `subject_manifest` nicht, ein dort ergänzter Schlüssel hätte also jede Rolle gedeckt — jetzt gepinnt. (c) Der `approval_ref`-Diebstahl ist ein ERNEUERUNGS-, kein Reihenfolgeproblem: `routine` ist zeitlich geboxt und wiederkehrend, also wandert das Feld bei JEDER Erneuerung; ein Validator-WARN (`report.py:_check_dispatch_approval_presented`) meldet ab sofort „Wurzel präsentiert eine nicht-dispatchende Freigabe, während eine gültige scope/delivery-Freigabe im Store liegt“. Dieser Check las den Approvals-Store zuerst INNERHALB der Item-Schleife erneut — O(Items × Freigaben) auf einem Pfad, den `gate_memory_complete` bei jedem Bash-Aufruf fährt, und die wöchentlich neu geprägte Routine lässt genau diese Form wachsen. Gemessen bei 300 Items und 700 Freigabedateien: 300 betroffene Items 35,5 s → 5,8 s nach einem einzigen Durchlauf in `{Item-ID: [Freigabe, …]}`, bei identischen Warnungszahlen (1/5/20/50/300). (d) Eine UNGÜLTIGE scope/delivery-APR am Root machte die Task-Routen unerreichbar — gemessen: widerrufene Scope-Freigabe, gültige Routine, Audit-Dispatch NEIN, also genau in der Lage, für die der Auditor da ist. Die Root-Route fällt jetzt durch statt zu raisen — aber NUR für einen Task ohne schreibenden Scope. **Korrektur 2026-07-31 (dieselbe Gegenprüfung, zweite Runde):** der erste Wurf fiel bedingungslos durch und begründete das mit „beide Task-Routen prüfen ihre eigene Bindung vollständig“. Das gilt für die Routine-Route und NICHT für die Analysis-Route: `dispatch.py:_covering_analysis_apr` bindet einen GELISTETEN Task und sonst nichts — keine Rolle, keinen Scope. Gemessen mit einer analysis-APR, die einen Implementierungs-Task listet: Wurzel widerrufen → Dispatch ERLAUBT, Wurzel out-of-band editiert (Revision unverändert, also greift auch der `root_revision`-Check nicht) → ERLAUBT. Damit hob das Durchfallen genau die zwei Stolperdrähte auf, für die `assert_apr_in_force` existiert, und der Widerruf ist der schlimmere Fall, weil der User die Freigabe bewusst zurückgezogen hat. Die Regel lautet jetzt: **eine Wurzel, deren Freigabe nichts mehr gewährt, darf noch GELESEN, nie mehr BESCHRIEBEN werden** — durchgefallen wird nur bei `not _claims_writable_scope(task)`, sonst bekommt der Task die Root-Verweigerung wörtlich. Gemessen nachher: schreibender Task unter widerrufener/editierter/fehlender Wurzel-APR → verweigert mit dem jeweiligen Root-Grund; Audit unter denselben drei → erlaubt. Zusätzlich lag `read_apr` ausserhalb des `try`, weshalb ausgerechnet der Grund „APR-Datei fehlt“ als `ApprovalError` durchschlug („das Harness ist kaputt, ruf den Doctor“) und die Routine-Route für diesen einen Grund verschlossen blieb — jetzt `dispatch.py:_read_root_apr`. Zusätzlich rendert die Freigabefrage jetzt JEDEN Schlüssel des gehashten Manifests sortiert — Rolle, Scope, Trigger, Takt UND das Ablaufdatum als UTC-Datum (als Epoch-Zahl ist es das Feld, das ein Mensch am wenigsten beurteilen kann, und bei einer zeitlich geboxten stehenden Spawn-Erlaubnis das wichtigste); der User unterschrieb vorher eine Rolle und eine Laufzeit, die er nie sah. Der Fragetext enthält dadurch aufruferkontrollierten Text: geschmuggelter `[APR-REQ:…]`-Marker macht die Frage mehrdeutig und prägt NICHT (fail-closed, gepinnt) — eine Rolle kann damit allerdings ihre eigene Freigabe unmintbar machen (Selbst-DoS), benannt statt geschlossen. |
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
| ⚓ hooks/gate_git.py | anpassen | Force-Push-Sperre bleibt; PRD-\d-Regex → Branch↔Item + typgerechter Status, QA-Beleg via Evidence (II.10). **Nachtrag 2026-07-27 (Gruppe „gate_git auf Evidence-Items"):** ERLEDIGT, jetzt in beiden Hälften. (a) QA-Beleg via Evidence: siehe Zeile 512. (b) Branch↔Item: das Ziel ist JEDES Wurzel-Item, das die git-Invocation NENNT — nicht das erste im Rohtext (damit wurde `git merge -m "see PR-0002" feat/PR-0001-x` als PR-0002 beurteilt, der Audit-Fehlakzept in einem Flag wiederhergestellt, gemessen in Prüfrunde 7). Das Gate WÄHLT nicht, es verlangt alle: eine bloss erwähnte ID fügt eine Bedingung hinzu und ersetzt nie eine. Was nicht zur Invocation gehört, entfernt Shell-Syntax vorher (`_compat.git_argument_text`: Wrapper auspacken, Zeilenfortsetzungen zusammenziehen, `#`-Kommentare raus, Segmente an `&&`/`|`/`;`); der Branch wird nur gelesen, wenn das Kommando nichts nennt. (c) **Typgerechter Status:** aus `AUTOMATA[typ]` abgeleitet statt im Hook aufgezählt — Initialstatus (`DRAFT`: nichts hat diese Arbeit freigegeben) und jeder TERMINALSTATUS AUSSER dem Kettenende (`REJECTED`/`SUPERSEDED`: das Projekt hat die Arbeit verworfen) blocken den Merge; das Kettenende selbst (`ACCEPTED`) ist der geglückte Abschluss und bleibt offen. Tests: `test_gate_git_judges_the_merged_items_status_against_its_own_automaton` (6 Statuswerte), `…requires_every_item_the_command_names`, `…reads_the_branch_only_when_the_command_names_nothing`. **Nachtrag 2026-07-27 (Prüfrunde 9 eingearbeitet):** die Ziel-Bestimmung liest jetzt einen eigenen Text. Ein gequoteter Span ist NUR für die Frage „ruft diese Zeile git auf“ Prosa; für die Frage „welche Items nennt die Invocation“ ist er das Argument selbst — der prosa-bereinigte Text löschte deshalb genau das Ref, um das es geht, und `git merge "feat/PR-0002-x"` hob Evidence- UND Status-Bindung auf (gemessen im gescaffoldeten Projekt). `_compat.git_argument_text` entfernt die Quote-ZEICHEN, behält den Inhalt, neutralisiert darin Shell-Syntax und schneidet den `#`-Kommentar in DEMSELBEN Durchlauf (sonst zerschneidet ein `#` in einer Commit-Message die Zeile vor dem echten Ref). Ein zur Laufzeit gebautes Ref (`git merge "$B"`) ist unlesbar statt „nennt nichts“ und weitet die Suche auf die ganze Zeile aus. Zweitens zieht `_compat` die Zeilenfortsetzung `\`+Newline vorher zusammen: ohne das schaltete `git \<newline> merge …` JEDES git-Gate ab, Force-Push-Sperre eingeschlossen (vorbestehend, nicht von dieser Gruppe eingeführt). Tests: `…binds_a_quoted_ref_exactly_like_a_bare_one`, `…still_drops_a_hash_that_only_looks_like_a_comment`, `…widens_to_the_whole_line_when_the_ref_is_a_shell_variable`, `…sees_a_command_split_over_a_line_continuation`. **Nachtrag 2026-07-28 (Prüfrunden 11+12, Gruppe „die beiden Shell-Parsing-Umgehungen“):** die ANWENDBARKEIT aller git-Gates ist jetzt eine Definition in `_compat.git_invocations` statt einer Schreibweisenliste, und die Definition hat DREI Hälften — die dritte kam in Prüfrunde 12 dazu, weil die Umstellung eine Klasse verloren hatte, die der alte Schreibweisen-Leser noch hielt. (a) WELCHES WORT DAS VERB IST: das Subkommando, also das erste Token nach `git`, das weder eine git-eigene Option noch deren Wert ist. Optionen, die ihren Wert als eigenes Token nehmen, sind vollständig aufgezählt UND durch einen Ambiguitätszweig abgesichert — eine Option, die dieser Leser nicht kennt, macht das Folgetoken mehrdeutig, und dann zählen BEIDE Lesarten (`git --attr-source HEAD push --force` las sein Verb sonst als `head` und wurde von allen acht Hooks durchgelassen, gemessen). Ein Verb, das die Shell erst zur Laufzeit baut (`git $V`, `git $(echo push)`), ist UNRESOLVED und beantwortet jede Frage mit ja (`GitInvocation.runs`). (b) WELCHES `git` EIN KOMMANDO IST: ein `git`, das ein Shell-WORT beendet — nicht eines, das an einer bestimmten Stelle des Segments steht. Die Positionsregel der Vorrunde war derselbe Defekt ein Wort weiter: `sudo "git" push --force origin main` (ebenso `env`, `nohup`, `command`, `timeout`) war auf allen acht Hooks ALLOW. Dazu: das Escape-Zeichen ist eine Eigenschaft der SHELL, PowerShell escaped mit Backtick, und da der Text nicht sagt, welche Shell ihn ausführt, liefert der Leser JEDE Lesart und die Gates antworten über alle (`git push --for`ce` hob sonst die Force-Push-Sperre auf). `$'…'` ist Quoting, nicht Expansion. Ein gequoteter Payload hinter `| sh` ist Code wie bei `sh -c`/`eval`; mehrstufige Pipes und Heredocs sind als bekannte Restlücke benannt. `gate_shell_hygiene` wurde als achtes Bash-Gate mit umgestellt (es hatte beide Originaldefekte noch: `git reset --ha\<newline>rd HEAD~1` blockte kein einziger Hook). Und der Leser ist linear statt quadratisch, plus `GIT_READ_LIMIT`: 120 KB `git `-Wörter kosteten `gate_git` 125,7 s, also mehr als die 60 s, nach denen der Host den Hook killt — und ein gekillter Hook ist ein ALLOW (II.4). **(c) WO EIN SHELL-WORT ENDET** (Prüfrunde 12): an Whitespace oder an einem METAZEICHEN, und die Menge der Metazeichen ist geschlossen — `| & ; ( ) < > Space Tab Newline` (POSIX XCU 2.2). Genau `<` und `>` fehlten, also klebte eine Umleitung am Wort daneben: `git push>/dev/null --force origin main` hatte das Subkommando `push>/dev/null`, das kein git-Kommando ist, und ALLE ACHT PreToolUse-Hooks standen still — ein Zeichen, wo das gequotete Verb zwei brauchte (gemessen; `git>/dev/null push` sogar ohne jede Invocation, weil das Wort `git` selbst nicht mehr endete, und im office-Kit erreichte ein Commit mit INVALID-Ledger HEAD). Die Gegenrichtung derselben Lücke: `git push origin main >/dev/null 2>&1` lieferte vier positionale Token und `gate_push_token` verweigerte die normalste Schreibweise eines Push als „more than one refspec“. Eine Umleitung nimmt jetzt Operator, Ziel und den davorstehenden Filedeskriptor mit (`_redirect_tail_rx`, `_drop_io_number`; `git push2>/dev/null` behält `push2`, weil nur ein reines Ziffernwort ein Deskriptor ist). **Wrapper-Familie:** die Eigenschaft („hängt den gequoteten String an einen Kommando-Parser weiter“) ist der Test, die Namensliste ist nur das Inventar der bekannten Träger — PowerShells `Invoke-Expression`/`iex` fehlte darin, obwohl `PowerShell` als eigenes Tool gegatet wird; nicht erreichbare Formen (`-EncodedCommand`, `Start-Process -ArgumentList`, mehrstufige Pipes, Alias-/Variablen-Indirektion) sind als Restlücken benannt statt impliziert. **`gate_push_token`:** die `--dry-run`-Ausnahme wird als TOKEN gelesen, nicht als Teilstring über den zusammengefügten Argumenten — `git push -o "--dry-run" origin main` hob sonst die einzige Durchsetzung von Parity-Zeile 29 auf. |
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
| ⚓ hooks/session_status.py | anpassen | Wird Update-Zustandsautomat + session_brief-Verweis; die injizierten Blöcke disponiert → kit_state.json/generated (II.8). **Gemessen 2026-08-01 (Netz-Runde), zweimal und mit verschiedenen Mitteln:** der Hook hat **14 Emissionsstellen** (`parts.append` plus die beiden Initialzuweisungen, per AST gezählt), die sich zu **9 Blöcken** gruppieren — **7 davon schaltbar** (als echter Prozess in Projekten ausserhalb des Repos per Ablation gemessen) und 2 unbedingt: die Identitätszeile und das State-Verzeichnis-Briefing, das ein `if/else` ist und den Wortlaut TAUSCHT statt zu verschwinden. Beide Zahlen sind gepinnt, weil keine die andere abdeckt: die Ablation kann einen unbedingten Block nicht sehen (gemessen: Identitätszeile in beiden Provider-Wortlauten gelöscht → Vollsuite grün), die AST-Zählung keinen, der aufgehört hat auf seinen Input zu reagieren. Drei davon haben mehrere Wortlaute (die Versionsansage drei, das State-Verzeichnis-Briefing zwei, das Update-Banner eine Codex-Erweiterung, die nur zusammen mit ihm erscheint und gemessen >200 Zeichen zusätzlich beiträgt); das sind Varianten EINES Blocks. Gepinnt in `test_shortening_net.py:test_the_session_start_hook_emits_what_the_disposition_counts`, damit die Umschreibung eine gemessene Ausgangszahl hat statt einer geschätzten. **Was II.8 wegnimmt und was danach niemand trägt:** (a) Identitätszeile, (b) Git-Branch, (d) State-Verzeichnis-Briefing (das IST der geforderte session_brief-Verweis, schon gebaut), (g) Model/Effort-Drift und (i) Projektpfad-Wechsel sind von II.8 gar nicht disponiert und bleiben. (c) Versionsansage: der `kit_updated_from`-Marker fällt laut II.8 restlos, die Ansage selbst wird ein Zustandsübergang. (e) `KIT UPDATE AVAILABLE` wird der Zustand `update_available` — der Name existiert in II.8, ein PRODUZENT existiert nicht: gemessen schreibt `write_kit_state.py` nur `restart_required` und `kit_trust_state.py:transition` nur `active`/`hooks_trust_required`; `update_available`, `approved`, `applying` und `failed_rolled_back` kommen im ganzen ausgelieferten Baum in keiner Schreibstelle vor. (f) `KIT MERGE BACKLOG` + Nag-Zähler und (h) der Transkript-Hinweis sind die zwei Blöcke, die II.8 ausdrücklich „restlos ersetzt" — **und ihren Inhalt trägt danach nichts**: welche Projektdateien nach einem Update von den Kit-Templates abweichen, erzeugen die Scaffold-Skripte in `kit_update_pending.*`, und `kit_state.json` hat kein Feld dafür; der Transkript-Hinweis beantwortet „was hat die letzte Session entschieden und nicht protokolliert", was der session_brief per Definition nicht weiss (er liest den State, nicht das Gespräch). Beides ist Befund, nicht Aufräumarbeit — die Umschreibung braucht dafür einen Entscheid, keine Zeile weniger. |

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
| ⚓ skills/software-architect/SKILL.md | anpassen | + draw.io-ARC statt Mermaid, architecture.yaml-Auflösung (II.6a). **Nachtrag 2026-07-26:** zwei unerfüllbare Zusagen entschärft — `freeze_architecture` hat nur Testaufrufer (Rolle nennt jetzt den staged Pfad), und „a project that wants the guard needs you to create it“ (`coding_guidelines.yaml`) ist durch `gate_write_scope` gesperrt. **Nachtrag 2026-07-31:** die Heimat der Knöpfe ist entschieden — sie sind `INV`-Items: ein `INV` mit `text` ist eine Regel, eines mit `value` ein Konfigurationsknopf (gefunden über sein `scope`), und ein `scope`, der ein Verzeichnis dieses Repos nennt, MACHT es zur Source-Area. Damit ist die Zeile `templates/project_memory/coding_guidelines.yaml` beantwortet. **Nachtrag 2026-07-26 (Gegenprüfung 2):** die Premise-Re-Check-Pflicht sagte „record the outcome in **that item's** `premise_rechecks`“, wobei das grammatisch nächste Antezedens „a decision“ war. `report.py:_check_premise_recheck` liest das Feld ausschließlich vom **PR/RQ/CR** (Z. 522), nie vom DEC — am DEC notiert erzeugt es eine Warnung, die nie verschwindet. Jetzt ausdrücklich das PR/CR bzw. RQ/CR, das die DEC NENNT. |

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
| ⚓ templates/project_memory/generate_dashboard.py | anpassen | Liest künftig generated/index.yaml + aktive Items; dashboard_history entfällt; Lockstep (II.7/II.11/2). **Nachtrag 2026-07-26:** verschoben nach `templates/repo/scripts/generate_dashboard.py` — `gate_write_scope` lehnt jede schreibfähige Kommandozeile ab, die das State-Verzeichnis nennt, also war der dokumentierte („non-skippable“) Aufruf für jeden Agenten mit exit 2 gesperrt, solange das Skript darin lag. Ausgabe bleibt `project_memory/generated/dashboard.html`. **Nachtrag 2026-07-26 (Migration, II.10a):** die Migration muss `project_memory/{generate_dashboard.py,progress.dashboard.template.html}` in BESTEHENDEN Projekten entfernen — `init_project_memory` löscht nichts und listet nur noch, was im Template steht, also bleibt der V1-Generator dort liegen, wird nicht mehr als `[kept]`/divergent gemeldet und liest gelöschte Monolithen. **Nachtrag 2026-07-26 (CLI-Einstieg, II.11/4):** Generator und `retro.py` nennen `python scripts/harness.py generate-index` als Abhilfe, `kit_checks` nennt `python scripts/harness.py doctor`; ein `harness`-Executable existiert nirgends (`prog="harness"` in `kernel/cli.py` ist nur Hilfetext, `python -m kernel.cli` scheitert an `ModuleNotFoundError`, und die funktionierenden Varianten nennen die Enforcement-Ebene und werden von `gate_write_scope` mit exit 2 abgelehnt). Beide Meldungen nennen jetzt zusätzlich den heute begehbaren Weg (jeder Kernel-State-Write schreibt den Index mit); die ~40 weiteren `python scripts/harness.py …`-Nennungen in den Hooks gehören an die Gruppe, die den CLI-Shim baut. |
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
| ⚓ templates/repo/scripts/kit_checks.py | anpassen | yaml-lint/file-budget/module-invariants/enforcement-diff bleiben; progress.yaml-Vertragsprüfung entfällt (Lockstep II.11/2). **Nachtrag 2026-07-26 — was hinter „bleiben“ steckt:** (a) `module_invariants` und `file_budget`/`source_areas` lesen ihre Knöpfe aus `_GUIDELINE_FILES`, und ein V2-dev-Projekt hat KEINE dieser Dateien mehr (coding_guidelines.yaml aufgelöst, Zeile 156) — die Architektur-Invariante ist damit **inert** (`if not rules: return`) und das Budget nicht mehr tunbar/exemptierbar; die Knöpfe brauchen die in Zeile 156 versprochene neue Heimat, `_knob_hint` sagt dem User bis dahin die Wahrheit. (b) `check_state_validity` ist NEU und ein harter `fail` im Merge-Pfad — verlangt hat ihn nur die research-Zeile 434, er ist spiegelbedingt auch in dev. (c) `archive/` ist aus dem rekursiven yaml-lint ausgenommen (eingefrorene Items, monoton wachsend, kalter CI-Read), Parse-Schritt auf `CSafeLoader`. (d) `python scripts/harness.py doctor` als Abhilfe existiert noch nicht — siehe den CLI-Vermerk in Zeile 164. |
| templates/repo/scripts/quality.py | anpassen | Quality-Pipeline bleibt (Fast-Mode II.10a); + Latenz-Bench. **OFFEN (2026-07-26, von der Lockstep-Gruppe gemeldet):** `_declared_source_areas()` ist ein ZWEITER Leser des `source_areas:`-Knopfs mit eigener Extraktion, eigenem Regex-Fallback und einer eigenen Kopie der Guidelines-Dateinamen (`kit_checks._GUIDELINE_FILES`). Nur der Docstring wurde entschärft (er behauptete „the same parser“); die Zusammenführung gehört in diese Zeile. |
| ⚓ templates/repo/scripts/retro.py | anpassen | Read-only-Retro bleibt; Datenquellen Per-Item statt progress/tasks; Auditor-Routine-Anbindung. **OFFEN (2026-07-26):** Datenquellen sind umgestellt; die Auditor-Routine-Anbindung (II.10a: Evidence pro Lauf, Wochen-ID + Lease, `APR.kind: routine`) ist NICHT gebaut — es existiert weder ein Produzent für Audit-Evidence noch ein APR-`kind`-Feld, retro könnte nur eine erfundene Form lesen. Gehört an die Gruppe, die II.10a baut. |

**tools:**

| pfad | disposition | begründung |
|---|---|---|
| tools/bump_kit_version.py | übernehmen | Versions-/Content-Hash-Stempelung bleibt. |
| tools/eval/README.md | übernehmen | Eval-Muster (Szenarien + LLM-Judge) bleibt gültig. |
| ⚓ tools/eval/scenarios.yaml | anpassen | Work-Orders/read_first auf V2-Item-Typen. **Nachtrag 2026-07-27:** umgestellt — und die Datei liest NICHTS (kein Runner, kein CI-Schritt), sie wird von Hand ausgeführt. Damit hing die Umstellung an keiner Prüfung: die HEAD-Fassung `read_first: [product_requirements.yaml PRD-0001]` blieb grün, weil der Lockstep-Sweep den PFAD beurteilt und ein nackter Monolithname keiner ist. Jetzt prüft `test_the_eval_scenarios_name_only_state_files_a_v2_project_has` sie mit demselben Vokabular-Aufruf wie die Entry-Gates (Union der drei Kits, nur `ANY`-Ausnahmen); mit der HEAD-Zeile rot gemessen. |
| ⚓ tools/test_e2e.py | anpassen | E2E-Pfade auf V2-Flow (Draft-PR→SR→TSK, Approval, Lock); Fixtures Per-Item. **Nachtrag 2026-07-27:** die Fixtures waren umgestellt, die KETTE fehlte — die Zeile war zur Hälfte offen und im Bericht der Lockstep-Gruppe als „ja“ abgehakt. Jetzt gebaut: `test_e2e_the_draft_to_dispatch_chain_runs_through_the_shipped_hooks` (Draft-PR → Freigabe durch den ausgelieferten `_gate.py`-Launcher → SR → TSK → Lease → Spawn, plus Rollen-Mismatch als Gegenrichtung) und `test_e2e_a_lock_held_by_a_foreign_process_makes_the_gate_wait_not_skip` (II.12 v2.1: „zweiter Prozess wartet/blockt“, als Laufzeit gemessen — 2,10 s Wartezeit gegen 2,0 s Haltedauer; ohne Lock 0,32 s = rot). Nicht enthalten und weiter offen: der volle II.12-E2E pro Kit (QA → Abnahme → Archiv, FR-Triage, Session-Rekonstruktion). |
| ⚓ tools/test_hooks.py | anpassen | Hook-Tests auf V2/gate_dispatch/Kernel (II.12-Matrix); Fixtures Per-Item. **Nachtrag 2026-07-26 (Gegenprüfung 2):** `test_instruction_files_name_only_state_files_a_v2_project_has` hielt seine eigene Zusage („a plain typo in a path a role is told to read“) nicht: es las nur Backtick-Spans, verankerte den Dateinamen an `$` und prüfte ausschließlich den BASENAME. Gemessen grün bei drei echten Regressionen (Monolithpfad ohne Backticks, Backtick-Span mit Nachtext, Verzeichnis-Tippfehler in einem Item-Pfad). Jetzt drei Behauptungen statt einer — Dateiname im ROHTEXT, Verzeichnis-Existenz gegen Template-Baum ∪ `ACTIVE_DIRS` (+ `STATE_DIRS_NOT_SHIPPED` mit Begründung), und die ÜBEREINSTIMMUNG Typ↔Verzeichnis in beiden Prosaformen, womit die §6-Tabellen gegen die Konstante gepinnt sind. Acht Mutationen in Sandkopien geprüft: Baseline grün, alle acht rot. Neu: `test_no_instruction_file_names_a_hook_its_own_kit_does_not_ship` (Gegenrichtung zu `test_every_hook_documented_in_its_constitution`; „Hook“ ist definiert als „ein Modul, das irgendein Kit ausliefert“, damit der Rubrik-Schlüssel `gate_health` nicht mitzählt). **Nachtrag 2026-07-27 (Teilumsetzung, ehrlich fortgeschrieben):** die Fixtures sind per-Item und der Lockstep-Beweis liegt hier; „Hook-Tests auf V2/gate_dispatch/Kernel (II.12-Matrix)“ ist es NICHT im Sinne einer Matrix-Rückverfolgung. Die Abdeckung liegt verteilt in `tools/test_hooks_v2.py` (Dispatch-Lebenszyklus, Approval-Protokoll, Lock/Audit), `tools/test_approvals_dispatch.py`, `tools/test_kernel.py`, `tools/test_state.py`; II.12 ist Fließtext, keine parsebare Tabelle, also existiert kein Test, der Matrixzeile gegen Testnamen abgleicht. Offene Hälfte (Rest an die Gruppe, die II.10a/II.12 abnimmt): Auditor-Routine-Tests, Codex-Pfad `audited`, Latenz-Bench, Research-E2E RQ→HYP→EXP. Ausserdem gehört `tools/test_hooks_v2.py` sinngemäss unter diese Zeile — es fehlt im Inventar. **Nachtrag 2026-07-27 (Prüfrunde 3, Status statt Fortschreibung):** die Zeile ist damit **HALB ERFÜLLT und bleibt OFFEN** — Fixtures/Per-Item ja, II.12-Matrix-Rückverfolgung nein. Die Fortschreibung oben beschreibt, was statt der Anordnung getan wurde; sie ersetzt sie nicht. Was in dieser Runde dazukam: der Vollständigkeitsbeweis liest jetzt auch Python-`#`-Kommentare (`tokenize`) und faltet Pfadkompositionen nach der Frage „was tut der Aufruf mit seinen Argumenten“ statt nach einer Liste von Schreibweisen (`Path(...)`, `.joinpath`, `+`); `item_file` ist erweiterungsblind und greift dort, wo ein Item-HOME beansprucht wird (`design/wireframes/DSN-0001.html` vorher grün); ein `Join-Path`-Kopf, der mit `-` beginnt, ist ein Parametername und wird nicht gefaltet. **Nachtrag 2026-07-27 (Prüfrunde 7, Befund 10):** `README.md` ist aus `MIGRATION_DOC_FILES` ENTFERNT und wird jetzt mitgesweept. Die Ausnahme galt „der Aufzeichnung der Migration“ — die Wurzel-README ist aber keine Aufzeichnung, sondern die Beschreibung dessen, was das Harness IST, und wird bei jeder Änderung neu geschrieben (dasselbe Argument, das der Kommentar für `radar/README.md` schon führte). Der Preis war gemessen: ihr `gate_git`-Absatz behauptete eine Runde lang weiter, das Gate blocke „EVERY merge/push, because it still looks for a V1-era `project_memory/*report*.yaml`“, nachdem das Gate längst auf dem Evidence-Store lief — und nichts konnte rot werden. Sweepen ist gratis (die Datei nennt heute keinen V1-Pfad, mit dem Leser des Sweeps selbst gemessen: 0 Treffer); mit dem alten Satz wieder eingesetzt ist `test_nothing_shipped_still_spells_a_v1_monolith_path` rot. |
| tools/conftest.py | anpassen | Fehlte im Inventar (nachgetragen 2026-07-27). Trägt den `known_hole`-Marker und das V1-Inventar: `V1_MONOLITHS` (die elf Speicher, die dieser Lockstep verschoben hat) und NEU `V1_ROOT_STORES_NOT_YET_MIGRATED` (`coding_guidelines.yaml`, `testing_guidelines.yaml`, `process_definitions.yaml`, `*report*.yaml` — dieselbe Definition, aber ausgeliefertem Code noch gekoppelt; Zeilen 115/159/176/249/338/507/556). Ohne die zweite Liste behauptete der Beweis Vollständigkeit gegenüber einer Aufzählung, die gegen ihre eigene Definition unvollständig war. **Nachtrag 2026-07-27 (Gruppe „gate_git auf Evidence-Items”):** der `*report*.yaml`-Eintrag ist GELÖSCHT und in `V1_MONOLITHS` verschoben — `gate_git` liest jetzt den Evidence-Store, kein ausgeliefertes Kit LIEST oder SCHREIBT den alten Pfad mehr (der Modul-Docstring beider `gate_git.py` nennt ihn weiter, und zwar absichtlich: er begründet, was ersetzt wurde. Der Sweep liest Docstrings bewusst nicht — `_running_strings`, dokumentierte Entscheidung —, die Zeile ist also grün, und die Behauptung gilt für laufenden Code und `#`-Kommentare, nicht für Prosa im Modulkopf), und damit gehört der Speicher dem Vollständigkeitsbeweis (`test_nothing_shipped_still_spells_a_v1_monolith_path`), der eine Rückkehr des Pfades rot meldet — mit einer Mutation in einer Sandkopie gemessen. Offen bleiben drei Speicher, nicht vier. |
| ⚓ tools/test_hooks_v2.py | anpassen | Fehlte im Inventar (nachgetragen 2026-07-27); zweitgrößte Datei des Repos. V2-Verhalten: Dispatch-Lebenszyklus, Approval-Protokoll, Lock/Audit, doctor/Capability-Matrix, office-PII. Fixtures Per-Item. **Nachtrag 2026-07-27:** `test_the_ui_inventory_snapshot_rule_is_shipped` prüfte mit einem ±300-Zeichen-Fenster auf ein blosses `CR`-Token und wurde in der Verfassung von der Glossarzeile drei Zeilen darüber allein erfüllt — die UI-Pflicht liess sich durch „visible UI elements may be removed freely“ ersetzen, ohne dass der Test rot wurde. Jetzt wird die REGEL gesucht (ein Satz, der Entfernen/Ersetzen an ein CR bindet) im selben Markdown-Block wie die Snapshot-Nennung; vier Mutationen rot, Nachbarblock-Kontrolle grün. **Nachtrag 2026-07-28 (Prüfrunde 7, Befunde 6–7 und 11–13):** die Trust-/Bundle-Tests hingen am VERSION-Stempel des echten `team-kits/` — jede unbebumpte Kit-Änderung liess sie mit einer sachfremden Meldung fallen, und der wichtigste davon (`test_trust_cannot_be_reset_by_re_running_the_recorder`) mass in diesem Zustand seine eigene Aussage nicht mehr, weil er auf der Stempelprüfung abbrach, bevor das Bundle je verglichen wurde. Fixture und Recorder laufen jetzt gegen dieselbe neu gestempelte Kopie (`_restamped_staging`), ebenso die beiden Scaffold-Tests; verbleibende Kopplung ist gewollt und trägt den Namen der Sache: `test_validate_py_is_green` (neu — eine grüne Suite war bis dahin keine Aussage über `validate.py`) und die drei Installer-Tests, die `install.ps1` samt seinem `validate.py`-Aufruf ausführen. Ausserdem: die Cross-Kit-Schranke ist keine Zahl mit Spielraum mehr, sondern zwei abgeleitete Mengen (Import-Abschluss und Registrierung↔Auslieferung), wobei die Registrierungsprüfung JEDEN `.py`-Namen eines Kommandos verlangt und nicht mehr die um den Launcher bereinigte Zuordnung — `_gate.py` war sonst die eine Datei ohne jede Auslieferungsprüfung (gemessen: gelöscht, alles grün, `validate.py` rc 0); und die Test-Stagings kopieren nach `kernel.hashing.transient_ignore_globs()` statt nach einer von Hand geschriebenen, gegen die Definition bereits unvollständigen Globliste. **Nachtrag 2026-07-28 (Prüfrunde 8, Befunde 3–5, 7–8):** die Launcher-Zuordnungsregel steht als `_gates_in` einmal da statt viermal von Hand (die vierte Kopie trug das Literal `_gate.py` und hätte jede Umbenennung von `GATE_LAUNCHER` überlebt — gemessen: heute identische Ausgabe, nach Umbenennung folgt die neue Form, die Literalform nicht). Beide Leerlaufschranken sind Mengenaussagen: der Import-Abschluss wird PRO KIT gegen Leere geprüft (der Boden `>= len(KITS)` blieb grün, wenn die Ableitung für genau ein Kit erblindete), und der Kopfzeilentest verlangt, dass die Menge der Skripte MIT Anspruch die Menge der registrierten Gates IST — vorher war „Klammern löschen“ der billigste Weg aus einem Rot, und `gate_filing.py` hatte ihn genommen. Dafür tragen jetzt alle registrierten Gates eine vollständige `Event(matcher)`-Kopfzeile (neun Dateien plus die drei fehlenden Events in `gate_dispatch`); die Matcher-Schreibweise ist aus dem Rumpf von `gate_write_scope` verschwunden, wo sie ohnehin schon ein Tool zu kurz war. `_file_write_matcher_tools` leitet die Toolmenge als Vereinigung über ALLE Kits ab (mit einem Kit blieb es grün, als das office-Kit den Matcher erweiterte). Und die beiden Symlink-Tests `skip`en ohne Privileg, womit genau die Eigenschaft aus Runde-6-Befund 6 auf einer Maschine ohne Developer Mode wieder ungemessen wäre: `test_the_link_branches_are_measured_on_a_machine_without_symlink_privilege` simuliert das PRÄDIKAT (`os.path.islink` über ein echtes Verzeichnis und eine echte Datei) und fährt damit die echten Zweige von `_bundle_files`, `_hash_subtrees` und dem Stranger-Scan; drei Mutationen rot (blinder Walk-Zweig, `_hash_subtrees` mit eigenem Walk, flacher Zweig auf blankem `os.path.islink`). |
| tools/test_kernel.py · tools/test_state.py · tools/test_schemas.py · tools/test_report.py · tools/test_backlog_types.py · tools/test_approvals_dispatch.py · tools/test_staging_cli.py | übernehmen | Fehlten im Inventar (nachgetragen 2026-07-27). V2-eigene Testmodule — sie sind mit dem State-Kernel entstanden und beschreiben V2-Mechanik, es gibt an ihnen nichts umzustellen. |
| tools/gen_known_holes.py | übernehmen | Fehlte im Inventar (nachgetragen 2026-07-27). Erzeugt `kernel/known_holes.json` + Digest aus pytests eigener Marker-Sammlung; V2-Mechanik, unverändert gültig. |
| tools/probes/** | übernehmen | Fehlten im Inventar (nachgetragen 2026-07-27). Manuelle Sonden für Hook-/Settings-Verhalten des Providers, kit- und zustandsunabhängig. |
| tools/test_shortening_net.py · tools/pin_constitution_sections.py · tools/constitution_section_pins.json | übernehmen | Neu 2026-08-01 (Netz-Runde), das Netz für die II.11/3-Kürzung. Das Testmodul löst das Mechanismus-Feld der Paritätsmatrix gegen laufenden Code auf (AST + Registrierung auf BEIDEN Oberflächen), pinnt jede Verfassungssektion aller drei Kits gegen einen Digest ihres eigenen Rumpfs und zählt die SessionStart-Blöcke per Ablation am echten Prozess. Der Pin wird mit `python tools/pin_constitution_sections.py --write` erneuert — bewusst von Hand, weil ein Pin, der sich im Testlauf selbst heilt, nichts aufzeichnet. V2-eigen; es gibt daran nichts umzustellen. |
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
| gen_provider_artifacts.py | anpassen | Provider-Parität muss neue Gates (gate_dispatch/guard_memory_budget) + Enforcement-Matrix abbilden (II.11/4). **Nachtrag 2026-07-28 (Prüfrunde 7, Befunde 8–9 und die Nachprüfung dazu):** `codex_matchers` übersetzt die TOOLMENGE eines Matchers statt der ersten Tabellengruppe, die sie schneidet — der ausgelieferte gemischte Matcher `Bash\|PowerShell\|Edit\|Write\|MultiEdit` von `gate_filing` erreichte Codex nur als `apply_patch`, die Shell-Hälfte dieses Gates fehlte dort seit Bestehen des Kits; der `mcp__*`-Zweig, den Kommentar und Test schon führten, ist erreichbar; `CODEX_UNSUPPORTED_TOOLS` entscheidet jetzt die deklarierte Lücke, alles Übrige bricht mit dem Namen ab, statt still zu verschwinden. **Dokuseite (Befund 3 der Gegenprüfung):** die Spec belegte die Parität in II.4 mechanisch mit `Agent\|Task → None` — nach der Umbenennung eine tote Zitatstelle (die Funktion liefert `()`), von nichts gepinnt. Sie steht dort jetzt als ausführbarer Aufruf, und `test_the_specs_codex_parity_evidence_is_still_produced_by_the_generator` wertet jede solche Behauptung der Spec gegen den Generator aus und verlangt, dass jeder zitierte `CODEX_*`-Name dort existiert. **Nachtrag 2026-07-28 (Prüfrunde 8, Befunde 1–2):** die Definition „ein Matcher nennt eine MENGE VON TOOLS“ gilt nicht für die eigenen Daten dieses Repos — alle drei Kits registrieren `Notification` mit `agent_completed|agent_needs_input`, das sind Benachrichtigungsarten. `codex_matchers` hätte dafür den Generator mit „nicht übersetzbares TOOL“ abgebrochen; dass das nie passierte, hing allein daran, dass `Notification` nicht in `CODEX_EVENTS` steht — eine Kopplung zwischen zwei Tupeln, die nirgends ausgesprochen war. Worüber ein Matcher entscheidet, ist jetzt eine Eigenschaft des EVENTS (`TOOL_MATCHED_EVENTS`), und `gen_codex_hooks` fragt die Tooltabelle nur für diese Events (`codex_matchers_for`). Dazu die fehlende Abdeckung des harten `SystemExit` aus Runde 7: `test_every_registration_a_kit_writes_survives_the_codex_translation` läuft pro Kit über settings.json UND jede Agent-Frontmatter und überdies über JEDE Registrierung, die das Kit irgendwo schreibt — auch über die Events, die Codex heute nicht erreichen. Zwei Mutationen rot: ein `WebFetch`-Matcher in research-team (vorher: Suite grün, Scaffold kaputt) und `codex_matchers_for` ohne die Event-Bedingung. |
| ⚓ init_project_memory.ps1 | anpassen | Kopiert künftig die typisierte V2-Struktur statt der Monolith-YAMLs (II.2/II.11/4). |
| ⚓ init_project_memory.sh | anpassen | POSIX-Zwilling desselben Init-Skripts. |
| model_tiers.yaml | übernehmen | Providerneutrale Modelltiers, zustandsunabhängig. |
| preset_config.py | übernehmen | Strikter Preset-Parser bleibt gültig. |
| registry.yaml | anpassen | Routing-Mechanik bleibt; V1-Beschreibungstexte („PRD→SRD→Task", „append-only ledger") auf V2. |
| ⚓ scaffold_team.ps1 | anpassen | V2-Struktur, neue Hooks, kit_state.json, .gitignore generated/, .vscode draw.io (II.6a/II.8/II.11). |
| ⚓ scaffold_team.sh | anpassen | POSIX-Zwilling desselben Scaffold-Skripts. |
| ⚓ write_kit_state.py | anpassen | Fehlte im Inventar (nachgetragen 2026-07-28). Der Trust-Recorder des Scaffolds (II.8): schreibt `.claude/kit_state.json` gegen den kanonischen `kernel.hashing.hook_bundle_hash` und verweigert alles, was nicht die Installation dieses Kits ist. **Nachtrag 2026-07-28 (Prüfrunde 8, Befund 6):** `hook_bundle_hash` antwortet zweimal `None` — kein Subtree vorhanden, und eine Datei darin nicht lesbar — und der Recorder las beide als „leer“: rc 2 mit der Meldung „no enforcement bundle under X“, die den Leser des zweiten Falls nach einer fehlenden Installation suchen lässt statt nach der Datei, die sich nicht öffnen liess. Die beiden Fälle werden jetzt an `BUNDLE_SUBTREES` gegen die Platte unterschieden; unlesbar ist rc 1 („ich habe nachgesehen und verweigere“), leer bleibt rc 2 („es gab nichts anzusehen“). Gedeckt von `test_a_bundle_that_cannot_be_measured_is_refused_not_reported_as_absent` — immer laufende Hälfte über das `None` als EINGABE, Ende-zu-Ende-Hälfte über einen kaputten Symlink in `.claude/hooks`, wo die Maschine einen erlaubt; Mutation (beide Fälle wieder eine Meldung) rot. |

**office-team/agents:**

| pfad | disposition | begründung |
|---|---|---|
| bookkeeper.md | anpassen | Craft bleibt; Flow/Budgets auf V2 (Result-Envelope, Write-Scope, II.4/II.5). |
| compliance-researcher.md | anpassen | Wie bookkeeper. |
| marketing-planner.md | anpassen | Wie bookkeeper. |
| office-developer.md | anpassen | Wie bookkeeper. |
| office-manager.md | anpassen | Lead auf V2: Draft-PR/State-Kernel/APR-Protokoll, ≤-Budgets (II.1/II.2). |
| product-editor.md | anpassen | Wie bookkeeper. |
| project-auditor.md | anpassen | Auditor wird Routine (APR.kind:routine) statt Delivery-Station (II.1/II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:ROOT_DISPATCH_KINDS` = {scope, delivery}, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. **Nachtrag 2026-07-31 (Blocker-Runde): erledigt.** Der Kernel hat die Route — `dispatch.py:_covering_routine_apr`, als DRITTER Weg neben Root- und Analysis-Route und ausdrücklich NICHT durch Aufnahme von `routine` in `approvals.py:ROOT_DISPATCH_KINDS`: die Route bindet, was Spec II.2 bindet, sonst wäre sie ein Blankoscheck. Geprüft werden (a) die Freigabe selbst über `approvals.py:assert_apr_in_force` (widerrufen, Provenienz über die konsumierte Anfrage, fremdes Item, Ablauf — pro Dispatch neu, also auch zwischen Lease und Spawn), (b) die ROLLE aus dem geprägten Manifest gegen `TSK.assigned_role`, (c) READ-ONLY über `dispatch.py:_claims_writable_scope`: ein Task mit `allowed_scope` wird auf dieser Route abgelehnt, womit eine Routinefreigabe nie Implementierungsarbeit legitimiert. `approvals.py:ROUTINE_MANIFEST_FIELDS` macht Rolle/Scope/Trigger/Takt beim Anlegen der Anfrage zur Pflicht — eine Routine, die nichts bindet, wird dem User gar nicht erst zur Unterschrift vorgelegt. Gemessen vorher/nachher mit gültigem, unabgelaufenem, nicht widerrufenem routine-APR am Wurzel-Item und Audit-`TSK` READY: `create_lease` REFUSED → ALLOWED und `gate_dispatch` als echter PreToolUse-Prozess rc 0; abgelaufen, widerrufen, falsche Rolle, schreibender Scope und „ohne jede Freigabe“ bleiben verweigert, Scope-, Delivery- und Analysis-Route unverändert erlaubt. Die Rollentexte (`agents/project-auditor.md` + `skills/project-auditor/SKILL.md`, alle drei Kits) sagen jetzt beides. **Nicht geschlossen, benannt:** Trigger und Takt liegen im gehashten Manifest, aber kein Gate liest sie (die von II.10a geforderten `last_completed`/`next_due` haben keinen Produzenten), der Read-only-Scope des Manifests hat kein Lese-Gate, und KEIN Kommando der ausgelieferten Oberfläche erzeugt eine ablaufende Freigabe — `request-approval` bietet nur die item-abgeleiteten Arten, was `analysis` genauso trifft wie `routine`. Und: eine am Wurzel-Item geprägte Routine ZIEHT dessen `approval_ref` auf sich (der Mint schreibt das Feld für jede item-gebundene Freigabe), womit die Delivery-Route — die genau dieses eine Feld liest — für Implementierungs-Tasks unter dieser Wurzel bis zur erneuten Scope-Freigabe verweigert; gemessen und in `test_approvals_dispatch.py:test_minting_a_routine_on_a_live_root_takes_its_approval_ref` festgehalten. Die Interaktion ist älter als diese Route (eine item-gebundene `analysis` tut dasselbe), aber diese Route lädt sie erstmals ein. Nicht durch Aufweiten der Delivery-Route repariert: welche APR die trägt, ist eine daneben geschriebene Entscheidung und war in dieser Runde ausdrücklich unverändert zu halten. **Nachtrag 2026-07-31 (Gegenprüfung der Blocker-Runde):** vier Korrekturen. (a) READ-ONLY ist ein PLAN-Check, kein Sandkasten — gemessen an einem gebundenen Auditor mit leerem `allowed_scope` gegen alle acht registrierten `Bash`-Gates: `echo pwned > src/x.py`, `rm -rf src`, `git commit -am wip` je rc 0, während derselbe Pfad über `Write` rc 2 gibt (Sanity: eine Shell-Schreibung in den kanonischen State blockt weiterhin). Ursache: `gate_write_scope.handle_shell` löst den gebundenen Task nie auf und liest weder `allowed_scope` noch `forbidden_scope` — Regel 2 der Tabelle im eigenen Docstring existiert auf dem Shell-Pfad nicht, vorbestehend und für JEDEN gebundenen Spezialisten. Der Shell-Pfad wird in dieser Runde NICHT gebaut (eigenes Paket, eigene Gegenprüfung); stattdessen sagen alle vier ausgelieferten Stellen jetzt, was gebaut ist, und die Lücke ist als `known_hole` auf `state_write_protection.shell` festgenagelt — `doctor` führt die Capability dadurch `unverified`. (b) Die Rolle wird aus der GEPRÄGTEN Anfrage gelesen, nie aus der APR-Datei; `consumed_request` vergleicht `subject_manifest` nicht, ein dort ergänzter Schlüssel hätte also jede Rolle gedeckt — jetzt gepinnt. (c) Der `approval_ref`-Diebstahl ist ein ERNEUERUNGS-, kein Reihenfolgeproblem: `routine` ist zeitlich geboxt und wiederkehrend, also wandert das Feld bei JEDER Erneuerung; ein Validator-WARN (`report.py:_check_dispatch_approval_presented`) meldet ab sofort „Wurzel präsentiert eine nicht-dispatchende Freigabe, während eine gültige scope/delivery-Freigabe im Store liegt“. Dieser Check las den Approvals-Store zuerst INNERHALB der Item-Schleife erneut — O(Items × Freigaben) auf einem Pfad, den `gate_memory_complete` bei jedem Bash-Aufruf fährt, und die wöchentlich neu geprägte Routine lässt genau diese Form wachsen. Gemessen bei 300 Items und 700 Freigabedateien: 300 betroffene Items 35,5 s → 5,8 s nach einem einzigen Durchlauf in `{Item-ID: [Freigabe, …]}`, bei identischen Warnungszahlen (1/5/20/50/300). (d) Eine UNGÜLTIGE scope/delivery-APR am Root machte die Task-Routen unerreichbar — gemessen: widerrufene Scope-Freigabe, gültige Routine, Audit-Dispatch NEIN, also genau in der Lage, für die der Auditor da ist. Die Root-Route fällt jetzt durch statt zu raisen — aber NUR für einen Task ohne schreibenden Scope. **Korrektur 2026-07-31 (dieselbe Gegenprüfung, zweite Runde):** der erste Wurf fiel bedingungslos durch und begründete das mit „beide Task-Routen prüfen ihre eigene Bindung vollständig“. Das gilt für die Routine-Route und NICHT für die Analysis-Route: `dispatch.py:_covering_analysis_apr` bindet einen GELISTETEN Task und sonst nichts — keine Rolle, keinen Scope. Gemessen mit einer analysis-APR, die einen Implementierungs-Task listet: Wurzel widerrufen → Dispatch ERLAUBT, Wurzel out-of-band editiert (Revision unverändert, also greift auch der `root_revision`-Check nicht) → ERLAUBT. Damit hob das Durchfallen genau die zwei Stolperdrähte auf, für die `assert_apr_in_force` existiert, und der Widerruf ist der schlimmere Fall, weil der User die Freigabe bewusst zurückgezogen hat. Die Regel lautet jetzt: **eine Wurzel, deren Freigabe nichts mehr gewährt, darf noch GELESEN, nie mehr BESCHRIEBEN werden** — durchgefallen wird nur bei `not _claims_writable_scope(task)`, sonst bekommt der Task die Root-Verweigerung wörtlich. Gemessen nachher: schreibender Task unter widerrufener/editierter/fehlender Wurzel-APR → verweigert mit dem jeweiligen Root-Grund; Audit unter denselben drei → erlaubt. Zusätzlich lag `read_apr` ausserhalb des `try`, weshalb ausgerechnet der Grund „APR-Datei fehlt“ als `ApprovalError` durchschlug („das Harness ist kaputt, ruf den Doctor“) und die Routine-Route für diesen einen Grund verschlossen blieb — jetzt `dispatch.py:_read_root_apr`. Zusätzlich rendert die Freigabefrage jetzt JEDEN Schlüssel des gehashten Manifests sortiert — Rolle, Scope, Trigger, Takt UND das Ablaufdatum als UTC-Datum (als Epoch-Zahl ist es das Feld, das ein Mensch am wenigsten beurteilen kann, und bei einer zeitlich geboxten stehenden Spawn-Erlaubnis das wichtigste); der User unterschrieb vorher eine Rolle und eine Laufzeit, die er nie sah. Der Fragetext enthält dadurch aufruferkontrollierten Text: geschmuggelter `[APR-REQ:…]`-Marker macht die Frage mehrdeutig und prägt NICHT (fail-closed, gepinnt) — eine Rolle kann damit allerdings ihre eigene Freigabe unmintbar machen (Selbst-DoS), benannt statt geschlossen. |
| ⚓ records-clerk.md | anpassen | Filing gegen filing_plan.yaml-Wahrheit; filing_log wird Scan-Index (II.9). |
| shop-curator.md | anpassen | Wie bookkeeper. |

**office-team/constitution + hooks:**

| pfad | disposition | begründung |
|---|---|---|
| ⚓ constitution/AGENTS.md | anpassen | ≤150 Zeilen NACH Ersatzgates, V2-Zustandsmodell, Monolith-Refs raus (II.5/II.10a/II.11). **Konkret gemeldet 2026-07-26:** Zeilen 70/83/137 beschreiben `filing_log.yaml` im Präsens, als existiere die Datei. Sie wird von nichts erzeugt und von keinem Gate gelesen (`filing_plan.yaml` ist die Wahrheit); `scripts/pii_scan.py`, `inbox/README.txt` und `templates/project_memory/README.md` sagen das inzwischen im Konjunktiv. **Nachtrag 2026-07-26 (Verfassungen/Agents/Skills):** vier Behauptungen ohne Code ehrlich gemacht — (a) NEUER §0-Write-Lock-Punkt (wie dev/research; nennt zusätzlich, dass §4 Phasen 1–4 damit unausführbar sind und dass `gate_filing`s eigene Remedy „have the records-clerk propose filing_plan.yaml rules“ gesperrt ist); der in dieser Runde neu eingefügte Satz „die master-data files … sind configuration and reference data, **not items**“ behauptete eine Ausnahme, die `gate_write_scope._assert_state_write_allowed` nicht kennt. (b) §1: `gate_proc_approved` „hard-blocks“ → der Hook liest den gelöschten V1-Monolithen `process_definitions.yaml` und exit(0) bei Abwesenheit, blockt also NICHTS (das V2-Bootstrap-Loch aus II.4 ist permanent offen); dieselbe Datei erklärte drei Zeilen höher, dass genau dieser Monolith keinen Nachfolger hat. (c) §1/§4/Phase 4: `scripts/proc_hash.py` und `scripts/process_doc.py` crashen an derselben gelöschten Datei, und KEIN ausgeliefertes Kommando berechnet `approved_hash`, den `report.py:validate_state` bei APPROVED/ACTIVE-PROC als **error** verlangt ⇒ ein office-Projekt konnte keinen gültigen freigegebenen PROC bekommen und laut §1 keinen Spezialisten spawnen. (d) §2.4 Verfahrensdoku-Renderer als kaputt benannt. **ERLEDIGT 2026-07-31:** `gate_proc_approved` liest `procedures/active/PROC-*.yaml` und blockt bei LEEREM Bestand (Spec II.4), `approved_hash` wird vom MINT gestempelt, und die beiden Skripte lesen dieselben Items (Zeile `hooks/gate_proc_approved.py`, Zeile `scripts/proc_hash.py`, Zeile `scripts/process_doc.py`). **Nachtrag 2026-07-26 (Gegenprüfung 2):** (e) die vier in Runde 1 neu eingefügten `(§8)`-Verweise (Z. 25/44/75/114) zeigten auf einen Abschnitt, der die zitierte Regel NICHT enthielt — §8 sagte nur „the enforcement layer itself is off-limits“, nie „ein fehlzündendes Gate ist ein Infrastruktur-Defekt, den du meldest statt umgehst“ (dev/research haben sie als §2 Item 10). §8 trägt den Satz jetzt, im Wortlaut von dev §2.10. (f) §0 nennt zusätzlich die Shell-Hälfte des Gates (`init_project_memory`/`scaffold_team`, siehe Zeile 87). (g) §2 Item 1 nannte `guard_no_adhoc` — einen Hook, den dieses Kit NICHT ausliefert (Vorbestand seit HEAD); die Zeile sagt jetzt, dass die Regel hier Policy ist, und `test_no_instruction_file_names_a_hook_its_own_kit_does_not_ship` hält die Richtung Verfassung→Hook ab jetzt fest. (h) die Auditor-Routine-Zeile ehrlich gemacht (siehe Zeile 236). |
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
| ⚓ hooks/session_status.py | anpassen | Update-Zustandsautomat, Blöcke → kit_state.json + session_brief (II.8). Blockzahl und Nachfolger-Befund stehen bei der dev-Fassung dieser Datei in Teil 1 (§1.1) und gelten für die geteilten Blöcke; die office-Fassung hat zusätzlich `due_reports` und `stale_register_entries`, die dort NICHT mitgezählt und nicht gemessen sind. |

**office-team presets/settings/skills:**

| pfad | disposition | begründung |
|---|---|---|
| presets.yaml | übernehmen | Preset→Rollen-Mapping bleibt. |
| settings/settings.json | anpassen | Neue Gates rein, guard_ledger_direct raus (II.11/2). |
| office-team/VERSION | anpassen | V2-Bump (II.11/4). |
| skills/bookkeeper/SKILL.md | anpassen | ≤-Budgets, Result-Envelope-Flow; Craft bleibt (II.5). **BEKANNTE MID-LOCKSTEP-LÜCKE, gemeldet 2026-07-26 (Gegenprüfung 2), gilt für alle „Wie bookkeeper“-Zeilen (269/270/271/273/276):** das office-Kit hat derzeit ZWEI Ausgabekontrakte. `records-clerk`, `project-auditor` und `office-manager` sind auf das Result-Envelope umgestellt; diese sechs tragen weiter den V1-Block (`summary`/`proc`/`booked`/…). `dispatch.py:submit_result` validiert `result_envelope` mit `strict: true`, `gate_subagent_output` verlangt nur `summary:` — die sechs fallen also erst durch, wenn ein Ergebnis wirklich übernommen wird. Dispositionskonform (kein ⚓, späterer Schritt), aber NICHT erledigt. |
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
| project-auditor.md | anpassen | Auditor-Routine (APR.kind:routine, II.1/II.10a). **Nachtrag 2026-07-26 (Gegenprüfung 2, Verfassungen/Agents/Skills):** die Runde-1-Zeile behauptete „dispatched on a revocable `APR.kind: routine` … an expired routine approval blocks the dispatch". Gemessen (gültiger, unabgelaufener, nicht widerrufener routine-APR am Root, Audit-`TSK` READY, `dispatch.create_lease`): **dispatch REFUSED** — `approvals.py:ROOT_DISPATCH_KINDS` = {scope, delivery}, und `_assert_dispatch_authorised_locked` kennt nur diese zwei plus die `analysis`-Route, die den Task LISTEN muss; `routine` fällt durch beide, womit `_assert_not_expired` auf diesem Pfad toter Code ist. Der Text sagt jetzt die messbare Lage: der Audit-Dispatch reitet auf einer `APR.kind: analysis` (dort greifen Ablauf UND Widerruf), und die ROUTINE-Semantik (Takt, Trigger, Rolle-und-Scope-Bindung) ist unerzwungene Policy — melden. **Blockierende Vorbedingung für den Abschluss dieses Lockstep-Schritts:** der Kernel muss `routine` in die Dispatch-Autorisierung aufnehmen (Spec II.1/II.10a fordert die Route ausdrücklich), und `tools/test_approvals_dispatch.py` testet Expiry bisher nur mit `analysis`. **Nachtrag 2026-07-31 (Blocker-Runde): erledigt.** Der Kernel hat die Route — `dispatch.py:_covering_routine_apr`, als DRITTER Weg neben Root- und Analysis-Route und ausdrücklich NICHT durch Aufnahme von `routine` in `approvals.py:ROOT_DISPATCH_KINDS`: die Route bindet, was Spec II.2 bindet, sonst wäre sie ein Blankoscheck. Geprüft werden (a) die Freigabe selbst über `approvals.py:assert_apr_in_force` (widerrufen, Provenienz über die konsumierte Anfrage, fremdes Item, Ablauf — pro Dispatch neu, also auch zwischen Lease und Spawn), (b) die ROLLE aus dem geprägten Manifest gegen `TSK.assigned_role`, (c) READ-ONLY über `dispatch.py:_claims_writable_scope`: ein Task mit `allowed_scope` wird auf dieser Route abgelehnt, womit eine Routinefreigabe nie Implementierungsarbeit legitimiert. `approvals.py:ROUTINE_MANIFEST_FIELDS` macht Rolle/Scope/Trigger/Takt beim Anlegen der Anfrage zur Pflicht — eine Routine, die nichts bindet, wird dem User gar nicht erst zur Unterschrift vorgelegt. Gemessen vorher/nachher mit gültigem, unabgelaufenem, nicht widerrufenem routine-APR am Wurzel-Item und Audit-`TSK` READY: `create_lease` REFUSED → ALLOWED und `gate_dispatch` als echter PreToolUse-Prozess rc 0; abgelaufen, widerrufen, falsche Rolle, schreibender Scope und „ohne jede Freigabe“ bleiben verweigert, Scope-, Delivery- und Analysis-Route unverändert erlaubt. Die Rollentexte (`agents/project-auditor.md` + `skills/project-auditor/SKILL.md`, alle drei Kits) sagen jetzt beides. **Nicht geschlossen, benannt:** Trigger und Takt liegen im gehashten Manifest, aber kein Gate liest sie (die von II.10a geforderten `last_completed`/`next_due` haben keinen Produzenten), der Read-only-Scope des Manifests hat kein Lese-Gate, und KEIN Kommando der ausgelieferten Oberfläche erzeugt eine ablaufende Freigabe — `request-approval` bietet nur die item-abgeleiteten Arten, was `analysis` genauso trifft wie `routine`. Und: eine am Wurzel-Item geprägte Routine ZIEHT dessen `approval_ref` auf sich (der Mint schreibt das Feld für jede item-gebundene Freigabe), womit die Delivery-Route — die genau dieses eine Feld liest — für Implementierungs-Tasks unter dieser Wurzel bis zur erneuten Scope-Freigabe verweigert; gemessen und in `test_approvals_dispatch.py:test_minting_a_routine_on_a_live_root_takes_its_approval_ref` festgehalten. Die Interaktion ist älter als diese Route (eine item-gebundene `analysis` tut dasselbe), aber diese Route lädt sie erstmals ein. Nicht durch Aufweiten der Delivery-Route repariert: welche APR die trägt, ist eine daneben geschriebene Entscheidung und war in dieser Runde ausdrücklich unverändert zu halten. **Nachtrag 2026-07-31 (Gegenprüfung der Blocker-Runde):** vier Korrekturen. (a) READ-ONLY ist ein PLAN-Check, kein Sandkasten — gemessen an einem gebundenen Auditor mit leerem `allowed_scope` gegen alle acht registrierten `Bash`-Gates: `echo pwned > src/x.py`, `rm -rf src`, `git commit -am wip` je rc 0, während derselbe Pfad über `Write` rc 2 gibt (Sanity: eine Shell-Schreibung in den kanonischen State blockt weiterhin). Ursache: `gate_write_scope.handle_shell` löst den gebundenen Task nie auf und liest weder `allowed_scope` noch `forbidden_scope` — Regel 2 der Tabelle im eigenen Docstring existiert auf dem Shell-Pfad nicht, vorbestehend und für JEDEN gebundenen Spezialisten. Der Shell-Pfad wird in dieser Runde NICHT gebaut (eigenes Paket, eigene Gegenprüfung); stattdessen sagen alle vier ausgelieferten Stellen jetzt, was gebaut ist, und die Lücke ist als `known_hole` auf `state_write_protection.shell` festgenagelt — `doctor` führt die Capability dadurch `unverified`. (b) Die Rolle wird aus der GEPRÄGTEN Anfrage gelesen, nie aus der APR-Datei; `consumed_request` vergleicht `subject_manifest` nicht, ein dort ergänzter Schlüssel hätte also jede Rolle gedeckt — jetzt gepinnt. (c) Der `approval_ref`-Diebstahl ist ein ERNEUERUNGS-, kein Reihenfolgeproblem: `routine` ist zeitlich geboxt und wiederkehrend, also wandert das Feld bei JEDER Erneuerung; ein Validator-WARN (`report.py:_check_dispatch_approval_presented`) meldet ab sofort „Wurzel präsentiert eine nicht-dispatchende Freigabe, während eine gültige scope/delivery-Freigabe im Store liegt“. Dieser Check las den Approvals-Store zuerst INNERHALB der Item-Schleife erneut — O(Items × Freigaben) auf einem Pfad, den `gate_memory_complete` bei jedem Bash-Aufruf fährt, und die wöchentlich neu geprägte Routine lässt genau diese Form wachsen. Gemessen bei 300 Items und 700 Freigabedateien: 300 betroffene Items 35,5 s → 5,8 s nach einem einzigen Durchlauf in `{Item-ID: [Freigabe, …]}`, bei identischen Warnungszahlen (1/5/20/50/300). (d) Eine UNGÜLTIGE scope/delivery-APR am Root machte die Task-Routen unerreichbar — gemessen: widerrufene Scope-Freigabe, gültige Routine, Audit-Dispatch NEIN, also genau in der Lage, für die der Auditor da ist. Die Root-Route fällt jetzt durch statt zu raisen — aber NUR für einen Task ohne schreibenden Scope. **Korrektur 2026-07-31 (dieselbe Gegenprüfung, zweite Runde):** der erste Wurf fiel bedingungslos durch und begründete das mit „beide Task-Routen prüfen ihre eigene Bindung vollständig“. Das gilt für die Routine-Route und NICHT für die Analysis-Route: `dispatch.py:_covering_analysis_apr` bindet einen GELISTETEN Task und sonst nichts — keine Rolle, keinen Scope. Gemessen mit einer analysis-APR, die einen Implementierungs-Task listet: Wurzel widerrufen → Dispatch ERLAUBT, Wurzel out-of-band editiert (Revision unverändert, also greift auch der `root_revision`-Check nicht) → ERLAUBT. Damit hob das Durchfallen genau die zwei Stolperdrähte auf, für die `assert_apr_in_force` existiert, und der Widerruf ist der schlimmere Fall, weil der User die Freigabe bewusst zurückgezogen hat. Die Regel lautet jetzt: **eine Wurzel, deren Freigabe nichts mehr gewährt, darf noch GELESEN, nie mehr BESCHRIEBEN werden** — durchgefallen wird nur bei `not _claims_writable_scope(task)`, sonst bekommt der Task die Root-Verweigerung wörtlich. Gemessen nachher: schreibender Task unter widerrufener/editierter/fehlender Wurzel-APR → verweigert mit dem jeweiligen Root-Grund; Audit unter denselben drei → erlaubt. Zusätzlich lag `read_apr` ausserhalb des `try`, weshalb ausgerechnet der Grund „APR-Datei fehlt“ als `ApprovalError` durchschlug („das Harness ist kaputt, ruf den Doctor“) und die Routine-Route für diesen einen Grund verschlossen blieb — jetzt `dispatch.py:_read_root_apr`. Zusätzlich rendert die Freigabefrage jetzt JEDEN Schlüssel des gehashten Manifests sortiert — Rolle, Scope, Trigger, Takt UND das Ablaufdatum als UTC-Datum (als Epoch-Zahl ist es das Feld, das ein Mensch am wenigsten beurteilen kann, und bei einer zeitlich geboxten stehenden Spawn-Erlaubnis das wichtigste); der User unterschrieb vorher eine Rolle und eine Laufzeit, die er nie sah. Der Fragetext enthält dadurch aufruferkontrollierten Text: geschmuggelter `[APR-REQ:…]`-Marker macht die Frage mehrdeutig und prägt NICHT (fail-closed, gepinnt) — eine Rolle kann damit allerdings ihre eigene Freigabe unmintbar machen (Selbst-DoS), benannt statt geschlossen. |
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
| hooks/gate_git.py | anpassen | Branch↔Item + typgerechter Status statt PRD-\d (II.10). **Nachtrag 2026-07-27 (Gruppe „gate_git auf Evidence-Items"):** ERLEDIGT — die Datei ist byteidentisch mit `dev-team/hooks/gate_git.py` (`KIT_SPECIFIC_HOOKS`-Eintrag gelöscht: die HEAD-Kopien unterschieden sich nur in `PRD-\d+` vs. `RQ-\d+`, und die Wurzeltypen kommen jetzt aus `_root.ROOT_ITEM_TYPES`). Begründung von Ziel-Bestimmung und Statusprüfung siehe Zeile 115. |
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
| ⚓ hooks/session_status.py | anpassen | Update-Zustandsautomat (II.8); Blockzahl und Nachfolger-Befund bei der dev-Fassung in §1.1 — die research-Fassung ist deren Zwilling. |

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

## 2. Lockstep-Disposition (82 ⚓-Dateien)

**Messwert vs. Schätzung:** Die v2.1 nennt „~76" (Grep über 6 Monolith-Namen). Phase 0 misst
mit der ERWEITERTEN 7-Namen-Liste (v2.1 fügt `architecture.yaml` hinzu, wegen
`gate_packaging_decision`) 79 Grep-Treffer: 41 in Teil 1 + 38 in Teil 2 — **plus 1
Nicht-Grep-Mitglied**: `research/hooks/gate_memory_complete.py`, das über seinen
masterplan-Check (:162–164) an masterplan.md koppelt und von Spec II.11/0(a) ausdrücklich
als Lockstep-Mitglied benannt ist (Fable-Check-3-Fund) → **80 Dateien** in jener Erhebung.
Davon sind 2 rein historisch/dokumentarisch (HARNESS_LOG.md: übernehmen; README.md:
Doku-Anpassung) — der Rest ist enforcement- oder inhaltlich gekoppelt und Bestandteil des
EINEN atomaren Release (II.11/2): kein Teilrelease entfernt einen Monolithen, solange
irgendein Gate/Skript/Template ihn erwartet.

**Massgeblich ist die Tabelle, nicht dieser Absatz.** Die Zahl oben in der Überschrift wird aus
den ⚓-Zeilen von §1 GEZÄHLT (`tools/test_disposition.py`); die 80 im Absatz sind der Messwert
vom 2026-07-24, den spätere Runden mit zwei weiteren Zeilen überholt haben.

**Teil 1 (42):** HARNESS_LOG.md · README.md · dev/constitution/AGENTS.md ·
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

**Teil 2 (40):** team-kits-Root: init_project_memory.{ps1,sh} · scaffold_team.{ps1,sh} ·
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

Quellen-Kürzel: `dev/off/res` = Kit · `AGENTS` = constitution/AGENTS.md · Lead-Dateien
(`pm`/`om` = agents-Datei, `pm-sk`/`om-sk` = Lead-SKILL): `pm, pm-sk` (dev) · `om, om-sk` (off) ·
`pm, pm-sk` (res) · Spezialisten: `arch, be, fe, qa, design,
audit, re, devops` (dev) · `clerk, book, editor, curator, compl, mkt, odev, audit` (off) ·
`method, rschr, analyst, review, writer, audit, re` (res).
**Jedes hier deklarierte Kürzel löst der Test gegen ein Kit auf; ein Kürzel, das die Legende
nicht nennt, ist ein Fehler und keine leere Menge.**
v2.1-Gate-Kürzel: GS1 Spawn-Form · GS2 gate_dispatch · GS3 Write-Scope · GS4
State-Validator · GS5 CI/Merge · APR2 Zwei-Phasen-Freigabeprotokoll.

**⚙ = das MECHANISMUS-FELD, und es ist der Grund, warum diese Tabelle beim Kürzen etwas wert
ist.** Eine Zeile mit Löschlizenz (siehe Vokabular unten) erlaubt, die Regel als Prosa zu
streichen — also muss sie den Ersatz BENENNEN, als auflösbares `<datei>.py:<symbol>`, und zwar
FÜR JEDES KIT, in dessen Text die Regel steht. `tools/test_shortening_net.py` löst jedes Symbol
per AST auf; liegt die Datei in einem Kit-`hooks/`-Verzeichnis, verlangt derselbe Test, dass der
Hook dort REGISTRIERT ist (`settings/settings.json`, gelesen mit `report.py:_wired_hooks`, oder
die `hooks:`-Frontmatter einer ausgelieferten Agent-Datei) UND dass der Matcher ihn für die
Tool-Namen erreichen kann, die der Hook selbst prüft — ein Gate, das nie feuern kann, ist kein
Mechanismus. Gemessen vor dieser Runde — gezählt über die DESIGNATION, also die Klassifikation
vor dem ersten datierten Nachtrag, weil ein Nachtrag, der zufällig Code zitiert, nicht die Zeile
ist, die ihren Mechanismus benennt: von 43 Zeilen mit Mechanismus-Anspruch nannten 0 ein
auflösbares Symbol, 21 einen Hook-Namen im Fliesstext, 9 nur ein GS-Kürzel und 13 gar nichts.
(Über die ganze Zelle gelesen kommt man auf 0/22/10/11 — dieselben 43, andere Frage.)

**Feldsyntax.** Einträge werden mit ` · ` getrennt; ein Eintrag darf mit `dev:` / `off:` /
`res:` / `dev+res:` beginnen und gilt dann nur für diese Kits, ein Eintrag ohne Präfix für alle
übrigen Quell-Kits der Zeile. Das ist nötig, weil die Matrix eine Regel EINMAL klassifiziert,
während sie in bis zu drei Verfassungen steht, die verschiedene Hooks ausliefern.

**Klassifikationsvokabular — geschlossen, und der Test liest es HIER:** `behalten` ·
`bewusst geändert` · `bewusst entfernt` · `durch Gate ersetzt` · `durch Test ersetzt` ·
`durch Gate+Test ersetzt` · `durch Gate ersetzt + behalten` · `durch Test GEPINNT → behalten`.

**Löschlizenz tragen genau diese vier:** `durch Gate ersetzt` · `durch Test ersetzt` ·
`durch Gate+Test ersetzt` · `durch Gate ersetzt + behalten`. Alle anderen lassen die Regel
stehen, wo sie steht.

**`durch Test GEPINNT → behalten` ist neu (2026-08-01) und korrigiert eine umgekehrte Lizenz.**
Ein Test, der einen AUSGELIEFERTEN Instruktionstext LIEST, ist ein Pin auf diesen Text: er wird
rot, wenn der Text verschwindet. Die Zeilen 25 und 97 nannten
`test_hooks_v2.py:test_the_ui_inventory_snapshot_rule_is_shipped` als „Ersatz“ und lizenzierten
damit das Löschen genau der Prosa, die dieser Test verlangt — gemessen: die lizenzierte Zeile aus
`dev-team/constitution/AGENTS.md` §7 entfernt, und der „Ersatz“ fällt mit „constitution/AGENTS.md
no longer names the UI inventory snapshot“. Der Test erkennt diese Eigenschaft per AST
(`test_shortening_net.py:_reads_shipped_instructions`) und verbietet sie in der Lizenzklasse.

**Was das Feld NICHT sagt:** dass der Mechanismus die Regel durchsetzt. Es sagt, dass er
existiert und läuft. Die Passung Regel↔Mechanismus bleibt eine Leseentscheidung — der Test macht
ZWEI Fälle unmöglich: ein Ersatz, den es nicht gibt, und einer, der rot wird, sobald man die
Lizenz benutzt.

**Der dritte Fall ist nur halb geschlossen, und die Hälfte ist gezählt.** Ein Matcher lässt sich
nur gegen einen Hook beurteilen, der sagt, auf welche Tools er reagiert (`data.get("tool_name")`);
zehn der registrierten dev-Hooks sagen es nicht — darunter `gate_write_scope`, der meistzitierte
Mechanismus dieser Tabelle. Gemessen: beide `gate_write_scope`-Registrierungen durch eine auf
`matcher: "WebFetch"` ersetzt, der Hook sieht danach weder einen Datei-Write noch ein Kommando,
und das Netz blieb grün. **12 der 32 wirksamen Lizenzen ruhen auf einem Hook ohne Tool-Wächter**
(4, 15, 17, 19, 34, 36, 37, 41, 56, 62, 73, 106). Die naheliegende Reparatur — die Tool-Klasse aus
dem gelesenen Payload-Feld ableiten — braucht eine Tabelle (`file_paths` = Datei-Tools,
`tool_input.command` = Shell-Tools, `questions` = `AskUserQuestion`, `subagent_type` =
`Agent`/`Task`), also genau die Aufzählung von Sonderfällen, die dieses Repo wiederholt bezahlt
hat, und sie schlägt fehl, sobald ein Hook ein Feld aus einem anderen Grund anfasst. Eine falsche
Ableitung verweigert Lizenzen mit einer unwahren Begründung. Deshalb steht hier eine ZAHL, die rot
wird, wenn sie wächst, und keine Heuristik.

**Der Pin-Detektor erkennt drei Schreibweisen, nicht vier.** `open(...)`, `Path(...).read_text()`
und `Path(...).open()` werden erkannt (gemessen an einem Probemodul mit denselben Konstanten);
ein Lesezugriff HINTER einem Helfer nicht. Und „ausgelieferter Instruktionstext" heisst
`constitution/`, `agents/`, `skills/` — abgeleitet aus dem Lead-Paket, nicht getippt —, damit
Projektskripte unter `templates/` nicht als Text-Pin gelesen werden (gemessen: `render`, `main`
und `lint` in `generate_dashboard.py`/`pii_scan.py`/`report_lint.py` wären es sonst).

**9 Zeilen tragen mindestens ein `⚙ offen`** (3, 6, 14, 48, 49, 54, 80, 82, 99): dort behauptet
die Klassifikation einen Gate-/Test-Ersatz, und im laufenden Code steht keiner — bei 3, 6, 14 und
49 nur für eines der Quell-Kits, was genügt, denn die Prosa steht in jedem. Das ist Befund, nicht
Vorschlag: ob diese neun umklassifiziert werden (wie Zeile 108 es 2026-07-26 wurde), ist ein
Userentscheid und wurde hier bewusst NICHT vorweggenommen.
**32 Zeilen tragen nach dieser Runde eine wirksame Löschlizenz** — nur an diesen darf die
Kürzung Prosa streichen. Beide Zahlen zählt der Test aus der Tabelle und prüft sie gegen diese
Sätze.

**Und die Grenze, die der Ausführende VOR dem ersten Schnitt kennen muss: 17 der 32 wirksamen
Lizenzen** (26, 30, 62, 64, 65, 66, 73, 86, 88, 90, 92, 94, 98, 102, 106, 115, 116) nennen
mindestens eine SPEZIALISTEN-Rollendatei als Quelle, und Spezialisten-SKILLs liegen ausserhalb des
Lead-Pakets, das der Sektionspin bewacht. Gemessen: „Never change SRs, architecture, or
requirements." aus `skills/backend-developer/SKILL.md` gelöscht — drei Tests grün. Reihenfolge
Diese Menge wird gezählt, nicht gepflegt: die von Hand geschriebene Fassung nannte Zeile 49, die
dieselbe Runde per Quell-Kit-Korrektur offen gemacht hatte, und übersah Zeile 88 (`res/re:22-30`,
ein kit-präfigiertes Spezialistenkürzel) — dieselbe Zahl, andere Menge. Reihenfolge
daher: **Lead-Pakete zuerst** (voll bewacht), **Spezialisten-Dateien danach und einzeln**, und
`python tools/pin_constitution_sections.py --write --note "…"` **nach jeder abgeschlossenen
Datei** statt einmal am Ende — sonst steht im Journal ein Grund für neunzig Zeilen, und das ist
wieder die Geste, gegen die es gebaut wurde.

| # | Regel (Kurzform) | Quelle(n) | Klassifikation |
|---|---|---|---|
| 1 | Deutsch zum User, Code/Artefakte Englisch | dev/AGENTS:4; off/AGENTS:4-6; res/AGENTS:4; dev/pm:15; off/om:14-15; res/pm:15 | behalten (min-keep) |
| 2 | Dokumentinhalt bleibt Originalsprache | off/AGENTS:6; off/om:15 | behalten |
| 3 | Orchestrator schreibt keinen Produktcode | dev/AGENTS:57; dev/pm:19; res/AGENTS:56; res/pm:20; off/om:20-22 | durch Gate ersetzt (→GS3; heute guard_pm_scope) ⚙ dev+res: `guard_pm_scope.py:check` · off: offen — das office-Kit liefert `guard_pm_scope` nicht aus; welcher Mechanismus dort den Orchestrator vom Produktcode fernhält, ist nicht gemessen |
| 4 | Kein Spawn ohne freigegebenen Task / Userfreigabe | dev/AGENTS:39; off/AGENTS:36-37; dev/pm-sk:81-88 | durch Gate ersetzt (→GS2 + analysis-APR) ⚙ `gate_dispatch.py:handle_pre_tool_use`, `dispatch.py:_assert_dispatch_authorised_locked` |
| 5 | „Ein Writer pro Datei" (PM pflegt project_memory) | dev/AGENTS:48,122-133; off/AGENTS:82,156-169; res/AGENTS:45,117-129 | bewusst geändert (Kernel wird einziger Schreiber; Rollen liefern Envelopes, II.1) |
| 6 | Single Source of Truth; keine Ad-hoc-Dateien | dev/AGENTS:44-47; off/AGENTS:47-50; res/AGENTS:42-44 | durch Gate ersetzt (→GS3+GS4) — **Gemessen 2026-08-01 (Netz-Runde):** das office-Kit liefert `guard_no_adhoc` nicht aus; dort sperrt nur `gate_write_scope.py:handle_file_write` das Zustandsverzeichnis, und die Ad-hoc-Dateiregel selbst hat keinen Leser. ⚙ dev+res: `guard_no_adhoc.py:check`, `gate_write_scope.py:handle_file_write` · off: offen — die Ad-hoc-Hälfte der Regel hat im office-Kit keinen Mechanismus |
| 7 | Kein DONE/Merge ohne QA-PASS in Reports | dev/AGENTS:51-52; res/AGENTS:48-49; dev/pm-sk:105-108 | durch Gate ersetzt (→GS4 DONE→VALIDATED via Evidence; GS5) — **korrigiert 2026-07-26:** GS5 ist NICHT wirksam; `gate_git` verlangt weiter einen V1-`project_memory/*report*.yaml` und blockt daher JEDEN merge/push, ohne dass Evidence ihn lösen kann (Dispositionszeile 115/338 offen). **Nachtrag 2026-07-27:** ERLEDIGT. `gate_git` liest den Evidence-Store (`kernel.backlog_types.ACTIVE_DIRS["EVD"]`) über die eine Definition `kernel.report.qa_verdicts`: je Evidence-Art (`test`/`review`/`acceptance`; `audit` beurteilt das Projekt und öffnet nie einen Merge) zählt die NEUESTE Evidence, die das gemergte Item deckt — direkt oder über den Referenzgraphen (TSK→PR, auch archiviert). Der Merge öffnet bei mindestens einem Urteil und keinem `fail`; ein nach einem PASS erfasster FAIL schliesst ihn wieder. Produzent: `python scripts/harness.py evidence` (`kernel/cli.py`), also derselbe Kernel-Schreibweg wie für jedes andere Item — der verbleibende Block ist der fehlende CLI-Shim (Zeile 87), nicht mehr eine Datei, die niemand schreiben KANN. Rollen-Text (QA-, Reviewer-, drei Auditor-SKILLs) und beide Verfassungszeilen nennen den Mechanismus. **Nachtrag 2026-07-27 (Prüfrunde 7 eingearbeitet):** drei Nachschärfungen, jede mit einem gemessenen Fehlakzept als Anlass. (a) Ziel = JEDES vom Kommando genannte Wurzel-Item statt der ersten ID im Rohtext (Zeile 115b) — sonst hob ein `-m "… PR-0002"` die Bindung auf. (b) Ohne jede Bindung (Branch nennt kein Item) fällt das Gate NICHT mehr auf ein globales „neuestes pro Art" zurück, sondern verlangt „kein offenes `fail` irgendwo", gruppiert je (Item, Art) — `report.qa_verdicts_by_subject`; das flache Lesen war der V1-Fehlakzept auf Dateiebene, aus typisierten Items nachgebaut (gemessen: `git push origin main` war durch ein fremdes PASS offen). (c) `EVD` ist nach dem Erfassen UNVERÄNDERLICH (`backlog_types.IMMUTABLE_TYPES`) — über den sanktionierten Edit-Pfad wurde ein `fail` in ein `pass` umgeschrieben und eine `related`-Bindung auf ein anderes Item gesetzt, beides ohne neues Item und ohne Spur; zusätzlich läuft `_assert_origins_resolve` jetzt auch auf dem Edit-Pfad. Die Vokabulare (`QA_EVIDENCE_KINDS`/`EVIDENCE_RESULTS`) sind gegen die sechs Rollentexte, beide `gate_git`-Kopien und die README gepinnt (`test_no_instruction_text_names_an_evidence_kind_or_verdict_the_kernel_refuses`). **Nachtrag 2026-07-27 (Prüfrunde 9 eingearbeitet):** drei Nachschärfungen am Beleg selbst. (a) `--artifact-ref` ist PFLICHT (`backlog_types.NONEMPTY_FIELDS`, im Kernel erzwungen, nicht nur in argparse) — vorher lief `python scripts/harness.py evidence … --summary "sieht gut aus"` ohne jeden Beleg durch und öffnete den Merge, während jeder Rollentext und jeder Remedy-Satz des Gates die Referenz als DEN Beweis präsentierte; `related` fällt unter dieselbe Regel, weil eine Evidence ohne Bindung kein Delivery beurteilt. Ein neuer Sweep prüft, dass jede in einem ausgelieferten Text buchstabierte `python scripts/harness.py evidence`-Zeile jedes vom echten Parser verlangte Argument nennt. (b) `QA_EVIDENCE_KINDS` ist abgeleitet statt zweitgelistet (`EVIDENCE_KINDS - PROJECT_EVIDENCE_KINDS`, Ausnahme `audit`) — eine nur in `EVIDENCE_KINDS` ergänzte Art wäre sonst stillschweigend zu „beurteilt kein Delivery“ geworden. (c) Der Test für einen unlesbaren `result` hat jetzt eine ältere, legale `pass`-Evidence derselben Art daneben: mit nur einem Datensatz führten „als kein-Pass gelesen“ und „still übersprungen“ beide zu rc 2, der fail-closed-Charakter war an nichts gepinnt (per Mutation gemessen). **Nachtrag 2026-07-28 (Prüfrunde 11 eingearbeitet):** die Merge-Blockade ist damit VERSCHOBEN, nicht beseitigt — `python scripts/harness.py evidence` ist der einzige Produzent, kein Kit installiert ein `harness`-Executable, `python -m kernel.cli` findet den als `.claude/kernel` installierten Kernel nicht, und jede Kommandozeile, die `.claude` nennt, lehnt `gate_write_scope` ab; gemessen blockt `git push` weiter mit „no QA Evidence in this project“. Diese Tatsache trägt jetzt ein PIN statt eines Berichtssatzes: `conftest.NO_INSTALLED_EVIDENCE_PRODUCER_CLAIM/_DOCS` plus `test_the_evidence_the_merge_gate_demands_has_no_producer_a_project_can_run` (misst die BEDINGUNG, nicht einen Pfad) und `test_every_document_that_teaches_the_merge_rule_says_the_evidence_cannot_be_produced` (der Satz steht wieder in der README, gleichlautend zu §0 der drei Verfassungen). Beide werden ROT, sobald der CLI-Shim (Zeile 87) ausgeliefert wird — das ist der Moment, in dem Konstanten, Tests und Caveat gemeinsam gelöscht werden. Zusätzlich: der Referenzgraph zählte seine Typen auf und kannte `SR` nicht (`SR.derives_from` ist Pflichtfeld) — eine Evidence an einem `SR` deckte dessen Wurzel nicht, der Merge wurde der Rolle, die genau diese Arbeit beurteilt hatte, mit „nothing judges this work“ verweigert. `backlog_types.PARENT_FIELDS` leitet die Bindungsfelder jetzt aus den Feldkontrakten ab; `report._parent_bindings`, `report._root_of`, der Referenzgraph-Block des Validators und `state._assert_origins_resolve` lesen alle diese eine Definition. **Nachtrag 2026-07-28 (Prüfrunde 11b eingearbeitet):** vier Nachschärfungen, jede mit einer Messung als Anlass. (a) Der gepinnte Satz war ZU STARK: „kein Subkommando kann aufgerufen werden“ ist keine Aussage, die eine Textprüfung tragen kann — `gate_write_scope` liest die Kommandozeile, und gemessen kam eine Schreibweise durch, die sie nicht erkennt. Behauptet wird jetzt nur noch, was die INSTALLATION hergibt („entry point is not installed“); was am Gate vorbeikommt, ist dessen Lücke (Runde-11-Befund 1), kein Einstieg. Der Testschritt, der `python .claude/kernel/cli.py` als „vom Gate geschlossen“ vorführte, ist gestrichen: der Pfad scheitert ohnehin am relativen Import, ist also gar kein lauffähiger Einstieg. (b) Die Dokumentliste ist ABGELEITET statt aufgezählt (vier Pfade wären grün geblieben, während fünf weitere ausgelieferte Texte dieselbe Tatsache in eigener Formulierung tragen): geprüft wird jeder BLOCK, der `python scripts/harness.py evidence` nennt — inklusive der vier Remedy-Texte beider `gate_git`-Kopien, gelesen als zusammengesetzter String — und jeder ABSCHNITT, der `gate_git` samt Evidence erklärt. Die gemeldete Regression (ehrlicher Satz aus dem Merge-Gate-Absatz der README gelöscht) ist damit rot; vorher blieb sie grün, weil die Phrase in einem thematisch fremden Absatz stand. (c) `PARENT_FIELDS` wird aus BEIDEN Kontraktquellen abgeleitet (`REQUIRED_FIELDS` ∪ `kernel/schemas/*` über `schemas.item_field_contracts`); `ARC`/`WFR`/`DSN` erzeugten sonst exakt denselben Schaden wie `SR` — gemessen: Review-Evidence an einer `ARC` deckte die Wurzel nicht. `DSN` hat dafür ein eigenes Manifest-Schema bekommen (`root` ist seine Bindung), und der Feldpflicht-Block des Validators liest jetzt `DECLARED_REQUIRED_FIELDS` — vorher lief er für genau die drei eingefrorenen Typen nullmal, obwohl II.8 ihm „ARC ohne derives_from → Validator-Flag“ zuweist. (d) Die neuen Tests assertieren gegen UNABHÄNGIGE Quellen (Schema-Dateien mit eigenem Leser, plus ein Korpus echter, über den Kernel erfasster Items), nachdem drei von ihnen ihre Erwartung aus der geprüften Landkarte gebaut hatten und bei deren Mutation grün blieben. Zusätzlich: `gate_write_scope`s Remedy nennt kein `kernel.cli` mehr (in einem Projekt nicht importierbar), und der Shim-Pin liest neben dem Dateibaum die Schreibstellen beider Installer — `scaffold_team.sh` erzeugt `CLAUDE.md` inline, ein generierter Shim hätte den Pin grün gelassen. **Nachtrag 2026-07-29 (Einstiegspunkt-Runde):** die Blockade ist GELÖST, nicht mehr nur verschoben. `scripts/harness.py` wird von beiden Scaffolds kit-owned installiert; Abnahme in einem gescaffoldeten Projekt AUSSERHALB des Repos, alles als echte Hook-Prozesse: `git merge feat/PR-0001-x` → rc 2 „no QA Evidence for PR-0001"; `python scripts/harness.py evidence --kind test --result pass --related PR-0001 --summary … --artifact-ref staging/TSK-0001/run.log` → alle acht PreToolUse-Gates rc 0, danach wirklich ausgeführt (`EVD-0001 test: pass`); derselbe Merge → rc 0. Damit sind `conftest.NO_INSTALLED_EVIDENCE_PRODUCER_CLAIM`, `conftest.EVIDENCE_PRODUCER_CLAIM_SCOPE` und die vier daran hängenden Tests GELÖSCHT, zusammen mit dem Caveat in allen ausgelieferten Texten. An ihre Stelle treten zwei abgeleitete Prüfungen: jeder Code-Span in einem ausgelieferten Text, der mit dem blossen Wort `harness` beginnt, ist verboten (die EINE Schreibweise kommt aus `kernel.cli.INVOCATION`), und jede in einem Rollentext genannte `python scripts/harness.py <cmd>`-Zeile muss ein Subkommando des echten Parsers nennen oder im selben Block sagen, dass es die Oberfläche noch nicht hat. ⚙ `gate_git.py:_refuse_unless_the_item_is_green`, `report.py:qa_verdicts` |
| 8 | Nur Produktfragen an User; Technik ans Team | dev/AGENTS:53; res/AGENTS:50; off/AGENTS:113-114 | behalten — **kein Gate (R2)** |
| 9 | Technische Frage an User = Defekt | dev/AGENTS:200-203; res/AGENTS:179-181 | behalten — **kein Gate (R2)** |
| 10 | Anti-Sycophancy: nie stumm zustimmen | dev/AGENTS:198; res/AGENTS:176-177; off/AGENTS:186 | behalten |
| 11 | Immer eine Option empfehlen | dev/AGENTS:199; res/AGENTS:178; dev/pm-sk:124 | behalten |
| 12 | Eigeninitiative 3 Stufen; nie eigenmächtig | dev/AGENTS:204-207; res/AGENTS:182-184 | behalten |
| 13 | Vor Vorschlag bestehende Items lesen; nie duplizieren | dev/AGENTS:54; res/AGENTS:52 | behalten (GS5 ID-Eindeutigkeit stützt) |
| 14 | Guidelines VOR Implementierung | dev/AGENTS:56; res/AGENTS:53-55; arch:59-62; method:35-43 | durch Gate ersetzt (→guard_guidelines; ggf. INV/SR) — **korrigiert 2026-07-26:** `guard_guidelines` ist KONDITIONAL (ohne `coding_guidelines.yaml` exit 0) und V2 liefert kein Template dafür; die Datei kann derzeit auch von niemandem angelegt werden (`gate_write_scope`). Im Default-V2-Projekt also **behalten (Prosa)** bis die Heimat des Knopfes entschieden ist (Zeilen 156/189) **Überholt, gemessen 2026-08-01 (Netz-Runde):** diese Korrektur beschreibt einen Zustand, den es nicht mehr gibt. `guard_guidelines` wurde auf `INV`-Items umgeschrieben (`invariants/active/`, Auswahl über `guard_guidelines.py:_governs`), ist über die Agent-Frontmatter der acht schreibenden dev-Spezialisten REGISTRIERT (nicht über `settings.json`, weil er nicht für den Lead feuern soll) und `python scripts/harness.py capture INV ...` kann die Items anlegen. Konditional bleibt er: ein Projekt ohne einen einzigen `INV` hat hier kein Regime, und der dev-Verfassungstext sagt genau das. ⚙ dev: `guard_guidelines.py:_governs` · res: offen — das research-Kit liefert `guard_guidelines` nicht aus, die Regel steht dort aber im Text (`res/AGENTS:53-55`, dieselben Zeilen, die Zeile 80 als offen führt) |
| 15 | Nur installierte Rolle; kein Generic/zweiter PM; explizites run_in_background | dev/AGENTS:38-40; off/AGENTS:38-41; res/AGENTS:35-38 | durch Gate ersetzt (→GS1+GS2) ⚙ `guard_agent_spawn.py:main`, `gate_dispatch.py:handle_pre_tool_use` |
| 16 | Nach Parallelarbeit alle Ergebnisse abwarten | dev/AGENTS:40; res/AGENTS:38 | behalten |
| 17 | Gleiche Dateien serialisieren | dev/pm-sk:90-93 | durch Gate ersetzt (→GS3 + Kernel-Lock) ⚙ `lock.py:KernelLock`, `gate_write_scope.py:_assert_in_scope` |
| 18 | Pflicht-Work-Order-Template | dev/pm-sk:85-88; res/pm-sk:36-37; off/om-sk:37-39 | durch Gate ersetzt (→GS2; TSK-Pflichtfelder) ⚙ `dispatch.py:create_task`, `schemas.py:item_required_fields` |
| 19 | Output-Contract (summary/verdict) sonst Block | dev/AGENTS:68; off/AGENTS:99; res/AGENTS:68 | durch Gate ersetzt (→Envelope-Schema/submit-result) ⚙ `gate_subagent_output.py:main`, `dispatch.py:submit_result` |
| 20 | Claims gegen Artefakte verifizieren | dev/pm:67; off/om-sk:40 | behalten |
| 21 | Startup-Gate: kein Spawn vor bestätigtem Preset | dev/AGENTS:24-25; off/AGENTS:21-22; res/AGENTS:24 | behalten (II.10a Erster Projektstart) |
| 22 | Draft-Pickup: nie Discovery bei Null | dev/AGENTS:22-23; res/AGENTS:22-23 | behalten (masterplan eingefroren) |
| 23 | Masterplan kritisch prüfen | dev/pm-sk:18-27; res/pm:43 | behalten — **kein Gate (R13)** |
| 24 | Änderung an APPROVED nur via CR+Freigabe | dev/AGENTS:100-102,144-150; res/AGENTS:96-97 | durch Gate ersetzt (→Freigabe-Invalidierung, II.2) ⚙ `approvals.py:approved_content_hash`, `backlog_types.py:invalidation_target` |
| 25 | Sichtbares UI-Element entfernen = IMMER CR | dev/AGENTS:146-148; fe:40; qa:33; design:93 | durch Test GEPINNT → behalten — **korrigiert 2026-08-01 (Netz-Runde):** die Einstufung war umgekehrt. Der genannte Test LIEST die drei ausgelieferten Texte und wird rot, sobald die Regel dort fehlt — er pinnt die Prosa, er ersetzt sie nicht. **nicht in II.12 (R5)** ⚙ `test_hooks_v2.py:test_the_ui_inventory_snapshot_rule_is_shipped` |
| 26 | BUG → Regressionstest (rot vor Fix) | dev/AGENTS:149-150; qa:81-83 | durch Gate+Test ersetzt (BUG VERIFIED via Evidence) ⚙ `state.py:_assert_confirmed`, `state.py:CONFIRMING_EVIDENCE` |
| 27 | Branch pro PRD/RQ (`feat/PRD-…`) | dev/AGENTS:154; res/AGENTS:137 | bewusst geändert (V2 `<typ>/<ITEM-ID>-<slug>`, II.10) |
| 28 | Conventional Commits pro Task | dev/AGENTS:154; res/AGENTS:137; off/AGENTS:196 | behalten |
| 29 | Push nur nach expliziter Userfreigabe | dev/AGENTS:156; res/AGENTS:138; off/AGENTS:198 | behalten — **kein Consent-Gate (R1)** |
| 30 | Nie force-push | dev/AGENTS:156; devops:49 | durch Gate ersetzt (→gate_git, GS5) ⚙ `gate_git.py:FORCE_RX` |
| 31 | Nie auf dirty Worktree arbeiten | dev/AGENTS:156; res/AGENTS:139; dev/pm:72 | behalten (Migration gated; Normalfall **R11**) |
| 32 | End-of-Phase: YAML→Dashboard→Commit | dev/AGENTS:49-50; res/AGENTS:46-47 | bewusst geändert (Index atomar im Kernel, II.2/II.7) |
| 33 | progress.yaml ONE-Line + append-only log | dev/pm-sk:118-123; off/om-sk:45; res/pm-sk:60-61 | bewusst entfernt (progress.yaml entfällt → session_brief, II.2/II.5) |
| 34 | Dashboard nur generiert | dev/AGENTS:141; res/AGENTS:133; off/AGENTS:168 | durch Gate ersetzt — **präzisiert 2026-07-26 (Gegenprüfung 2):** der Mechanismus ist nicht „nicht committet“, sondern `gate_write_scope`: der einzige Produzent schreibt nach `project_memory/generated/`, und dorthin ist JEDER Tool-Write gesperrt (gemessen). Der dev-Satz „`progress.dashboard.html` is generated only, **never hand-edited**“ ist mit §6a restlos gestrichen (nur die Vollständigkeits-Regel derselben Passage wurde nach §6 gerettet); office/research behalten je eine Textfassung („generated/ is kernel output, never hand-edited“). **Nachtrag 2026-08-01 (Netz-Runde):** die Quellenspalte ist für dev VERALTET — `dev/AGENTS:141` zeigt heute in §6, und dev trägt den Satz seit derselben Korrektur nicht mehr (nur office/research tun es). Das ist der Grund, warum diese Runde KEINE Regel→Sektion-Landkarte aus den Zeilennummern abgeleitet hat: sie hätte hier eine Sektion für eine Regel haften lassen, die sie nicht trägt. ⚙ `gate_write_scope.py:_assert_state_write_allowed` |
| 35 | Pflicht-YAML-Vollständigkeit bei Abnahme | dev/AGENTS:139-140; res/AGENTS:131-132 | durch Gate ersetzt (→gate_memory_complete-Nachfolger; GS4) ⚙ `gate_memory_complete.py:state_errors`, `report.py:validate_state` |
| 36 | Kein Projektstatus in Agent-Memory | dev/AGENTS:18-21; off/AGENTS:17-20; res/AGENTS:19-21 | durch Gate ersetzt (→guard_memory_budget + GS4) ⚙ `guard_memory_budget.py:_check_ids` |
| 37 | MEMORY.md INDEX ≤40 Zeilen | dev/AGENTS:21; off/AGENTS:20; res/AGENTS:21 | durch Gate ersetzt (→guard_memory_budget; II.12) ⚙ `guard_memory_budget.py:_check_size` |
| 38 | Enforcement-Layer tabu (Settings/Hooks) | dev/AGENTS:84-87; res/AGENTS:81-83; off/AGENTS:189-192 | behalten (→guard_harness_selfmod, II.4) |
| 39 | Fehlblockende Guard = Defekt melden, nie umgehen | dev/AGENTS:86-87; dev/pm-sk:162-170 | behalten |
| 40 | Fragen von Prosa eingeleitet; Ask-Loops begrenzt | dev/AGENTS:91-92; off/AGENTS:112-114 | behalten |
| 41 | Fragen selbst-enthaltend, nie „oben" | dev/pm-sk:34-40; off/om-sk:24-28; res/pm-sk:23-27 | durch Gate ersetzt (→guard_question_context; APR2) ⚙ `guard_question_context.py:main`, `gate_approval.py:handle_pre_tool_use` |
| 42 | Presets mechanisch; Upgrade=OK→Scaffold→Restart | dev/AGENTS:170-172; res/AGENTS:153-154 | behalten |
| 43 | Modell-Eskalationsleiter user-gated | dev/AGENTS:173-179; res/AGENTS:155-160 | behalten |
| 44 | Codex-TOMLs read-only; nur Full-Scaffold | dev/AGENTS:180-184; off/AGENTS:177-180 | behalten |
| 45 | Nach 3 QA-Fails: STOP + Optionen | dev/AGENTS:212-214; res/AGENTS:189-191 | behalten |
| 46 | Toter Spezialist: 1 Retry, dann eskalieren | dev/AGENTS:213-214 | behalten (Lease-Timeout→READY gated) |
| 47 | Tech-Debt geflaggt, nie still refactoren | dev/AGENTS:188; res/AGENTS:168-169; arch:66 | behalten |
| 48 | Flags/Findings verpuffen nicht (TSK oder Skip-Log) | dev/AGENTS:190-194; res/AGENTS:170-172 | durch Gate ersetzt (→Auditor-Routine, II.10a) — **gemessen 2026-08-01 (Netz-Runde):** die Routine-Route `dispatch.py:_covering_routine_apr` autorisiert den Auditor-LAUF und bindet Rolle und Read-only-Scope; dass ein Flag oder ein Finding danach zu TSK/BUG/CR oder zu einem Skip-Decision-Item wird, liest kein Gate und kein Validator-Check. Die Regel selbst hat also keinen Ersatz. ⚙ offen — die Verpuffungs-Regel trägt heute nichts ausser Prosa. |
| 49 | File-Budget harte Grenze | dev/AGENTS:75,192-193; audit:26 | durch Gate ersetzt (→gate_pipeline / `scripts/kit_checks.py` + GS4) — **korrigiert 2026-07-25:** guard_memory_budget deckt NUR agent-memory, nicht das Quelldatei-Budget — **Gemessen 2026-08-01 (Netz-Runde):** die Quelle `audit:26` ist die Auditor-Rolle ALLER DREI Kits, `kit_checks.py` liefern aber nur dev und research aus; im office-Kit hat die Budget-Regel keinen Mechanismus. ⚙ dev+res: `kit_checks.py:check_file_budget` · off: offen — das office-Kit liefert kein `kit_checks.py` aus |
| 50 | Auditor täglich/PM-getriggert | dev/AGENTS:194; res/AGENTS:172 | bewusst geändert (wöchentlich+ereignisbasiert, APR routine, II.10a) |
| 51 | Auditor read-only; ein Lauf=ein review_findings-Eintrag | dev/audit:34-36; off/audit:34-36; res/audit:34-36 | bewusst geändert (read-only via APR-Scope+GS3; Evidence statt review_findings, II.10a) |
| 52 | Artefakte sofort aktuell; derives_from-Impact prüfen | dev/AGENTS:218-219; res/AGENTS:195 | durch Gate ersetzt (→GS4 Referenzgraph/Invalidierung) ⚙ `report.py:_check_task_origins`, `approvals.py:approved_content_hash` |
| 53 | Kit-Update pending-file-Contract; nie Scaffold-Wiederholung | dev/AGENTS:219-221; dev/pm-sk:172-190; res/pm-sk:72-90 | bewusst geändert (kit_state.json ersetzt restlos, II.8) |
| 54 | Session mit Versionswechsel: nicht delegieren, EIN Restart | dev/AGENTS:220; dev/pm-sk:176-179 | durch Gate ersetzt (→kit_state.json + /hooks-Trust, II.8) — **Gemessen 2026-08-01 (Netz-Runde):** `kit_trust_state.py:transition` SCHREIBT den Zustand und gibt Text für einen SessionStart-Hook aus, der nicht blocken kann. Die Regel lautet „nicht delegieren“ — und kein Dispatch-Gate liest den Trust-State (`gate_dispatch.py` und `dispatch.py` nennen `kit_state` nirgends). ⚙ offen — der Zustand wird geschrieben, aber von keinem Gate gelesen |
| 55 | Onboarding: read-only zuerst, User bestätigt | dev/pm-sk:147-152; res/pm-sk:104-109 | behalten (II.10a) |
| 56 | Work-Order nennt APPROVED PROC (office) | off/AGENTS:36-37,100; off/om:50-51 | durch Gate ersetzt (→gate_proc_approved OHNE Bootstrap-Loch) — **korrigiert 2026-07-26:** das Loch ist NICHT geschlossen; der Hook liest den gelöschten V1-Monolithen und exit(0) bei Abwesenheit, blockt also in jedem V2-Projekt nichts. Bis zur Umstellung **behalten (Prosa)**, so auch in Verfassung/Agent/SKILL formuliert **Überholt, gemessen 2026-08-01 (Netz-Runde):** auch diese Korrektur ist eingeholt. `gate_proc_approved` liest die PROC-ITEMS (`gate_proc_approved.py:_executable_procs`), ein leerer Bestand BLOCKT jetzt (spec II.4) statt durchzulassen, und der Hook ist im office-Kit auf `PreToolUse(Agent|Task)` registriert. Das Bootstrap-Loch ist zu; was offen bleibt, ist nichts an dieser Zeile. ⚙ `gate_proc_approved.py:_executable_procs` |
| 57 | PROC-Edit entwertet Freigabe; re-hash bei User-OK | off/AGENTS:32-34; off/om:60 | durch Gate ersetzt (→Invalidierung PROC→DRAFT; Hash II.2) — **teilweise, korrigiert 2026-07-26:** die Invalidierung greift (Kernel hasht `steps`+`roles`), das RE-HASH nicht: `proc_hash.py` crasht am gelöschten Monolithen und der Kernel liefert kein Hash-Kommando, während `report.py` `approved_hash` bei APPROVED/ACTIVE als error verlangt ⚙ `approvals.py:approved_content_hash` |
| 58 | `processes:` muss Mapping bleiben | off/AGENTS:42-43 | bewusst geändert (PROC Per-Item; Monolith entfällt, II.9) |
| 59 | NICHTS wird gesendet; Outbound nur DRAFT in outbox/ | off/AGENTS:52-55; off/om:23-25; curator:23-24 | behalten — Codex nur Policy → **Teil-Enforcement (R4)** |
| 60 | Live-Shop-Mutation braucht PROC + Bestätigung | off/AGENTS:143; curator:24 | behalten |
| 61 | Ledger append-only + guard_ledger_direct | off/AGENTS:56-61; book:23-28 | bewusst geändert (I.3: Append-only ABGESCHAFFT; Guard GELÖSCHT; gate_ledger_valid) |
| 62 | Ledger-Zeilenvalidierung | off/AGENTS:58-59; book:23 | durch Gate ersetzt (→gate_ledger_valid, II.9/II.12) ⚙ `gate_ledger_valid.py:judge` |
| 63 | Reports generiert, nie handgeschrieben | off/AGENTS:63-65; book:31-33 | behalten |
| 64 | Filing verifiziert; gate_filing blockt | off/AGENTS:66-68; clerk:22-24 | durch Gate ersetzt (→gate_filing; filing_log→Scan-Index) ⚙ `gate_filing.py:check` |
| 65 | fs_tripwire: nie Delete/Move auf inbox/archive | off/AGENTS:68-69; clerk:20-24 | durch Gate ersetzt (→guard_fs_tripwire/Integrity-Guard) ⚙ `guard_fs_tripwire.py:main` |
| 66 | Unklassifizierbare Datei: unberührt + User fragen | clerk:26 | durch Test ersetzt (II.12 vorhanden) ⚙ `gate_filing.py:rule_matches`, `test_hooks.py:test_gate_filing_blocks_a_target_no_rule_covers` |
| 67 | filing_plan = einzige Maschinen-Wahrheit | clerk:16-20 | bewusst geändert (Ableitungsrichtung umgedreht, II.9) |
| 68 | Clerk löscht nie; Quarantäne; sha256-Dubletten | clerk:35-42 | behalten |
| 69 | Kein Steuer-/Rechtsrat; Disclaimer bleiben | off/AGENTS:70-73; book:9; compl:9,27 | behalten |
| 70 | Privacy-Honesty (kein DPA-Versprechen) | off/AGENTS:74-77 | behalten |
| 71 | Datenminimierung: Personennamen nur im Ledger | off/AGENTS:77-81; clerk:38-40 | behalten — **kein Gate (R3; 140-Namen-Vorfall)** |
| 72 | inbox/archive/outbox NICHT getrackt (GDPR) | off/AGENTS:196-198 | behalten (→Scaffold-.gitignore) |
| 73 | office-developer: nur konsumieren, nie mutieren | off/AGENTS:149-151; odev:16-20 | durch Gate ersetzt (→GS3 allowed_scope) ⚙ `gate_write_scope.py:_assert_in_scope` |
| 74 | office-developer deterministisch+self-verify | odev:22-31 | behalten |
| 75 | product-editor einziger Produkttext-Writer | off/AGENTS:139; editor:22-26 | behalten (→GS3) |
| 76 | bookkeeper: UNCLEAR statt erfinden | book:17-27 | behalten |
| 77 | compliance: kein Eintrag ohne Quelle | compl:19-27 | behalten |
| 78 | marketing: keine Credentials; nichts posten | mkt:16-25 | behalten |
| 79 | shop-curator v1 read-only; Claims mit Quelle | curator:16-25 | behalten |
| 80 | Research-Guidelines (Repro/Seeds/kein p-Hacking) | res/AGENTS:53-55; rschr:16-19 | durch Gate ersetzt (→INV/gate_pipeline) — behavioral **R9** ⚙ offen — `gate_pipeline` führt die Projekt-Pipeline aus, aber nichts darin liest Seeds, Repro-Rezept oder Auswertungsdisziplin; die INV-Hälfte hat im research-Kit keinen Leser (`guard_guidelines.py` liefert nur dev aus). |
| 81 | Scientific Honesty | res/AGENTS:176-177; analyst:22-23 | behalten — **kein Gate (R9)** |
| 82 | Reproduzierbarkeit zuerst; Ausreißer nie still droppen | rschr:16-20; analyst:15-18 | durch Gate ersetzt (→Reviewer-Repro; gate_pipeline) ⚙ offen — dieselbe Lage wie Zeile 80: die Reviewer-Reproduktion ist Rollenprosa, und `gate_pipeline` beurteilt den Pipeline-Exitcode, nicht die Reproduktion. |
| 83 | Report-Writer ändert nie Daten/Schlüsse | writer:11-12,44 | behalten |
| 84 | Report pro EXP sofort nach PASS; sonst incomplete | res/AGENTS:214-220; review:29-30 | behalten — **kein Gate (R7)** |
| 85 | FZulG-Regeln (Stunden, DOIs, ≤7 Jahre) | res/AGENTS:198-211; method:30-34 | behalten (Domänenregel) |
| 86 | Reviewer reproduziert; rote Pipeline/PII = FAIL | review:18-27 | durch Gate ersetzt (→gate_pipeline; GS5) ⚙ `gate_pipeline.py:main`, `gate_git.py:_refuse_unless_the_item_is_green` |
| 87 | premise_invalidation_triggers-Re-Check | dev/AGENTS:167; arch:52-58; method:24-29 | behalten — **kein Gate (R8)** |
| 88 | research-engineer: Provenance/Checksums, nie fabrizieren | res/re:22-30 | durch Gate ersetzt + behalten ⚙ `backlog_types.py:NONEMPTY_FIELDS` |
| 89 | Architect hält Mermaid-Diagramm aktuell | arch:20-21 | bewusst geändert (→.drawio.svg-ARC; Mermaid nur ephemer, II.6a) |
| 90 | packaging.method Pflicht; Gate blockt TODO | arch:42-48; dev/AGENTS:78 | durch Gate ersetzt (→gate_packaging_decision auf Architektur-Item) ⚙ `gate_packaging_decision.py:resolved_packaging` |
| 91 | Richtige Domänen-Toolchain, nie aus Gedächtnis | arch:24-40; method:38-42 | behalten — **kein Gate** |
| 92 | Stacks deklariert; ohne Checks = FAIL | arch:40-41; devops:17 | durch Gate ersetzt (→gate_pipeline stacks) ⚙ `gate_pipeline.py:main` |
| 93 | Load-Test-Weglassen = explizite ADR-Zeile; STRIDE | arch:57-65 | behalten |
| 94 | testing_guidelines je Stack Pflicht; Coverage | qa:35-44; dev/AGENTS:76 | durch Gate ersetzt (→gate_test_coverage-Nachfolger) ⚙ `gate_test_coverage.py:_governed_source_areas` |
| 95 | Design-Fidelity: Build MUSS design matchen | qa:16-34; fe:23-41; design:88-102 | behalten (min-keep #9; →design_ref-Gate II.6a) |
| 96 | A11y-Audit (WCAG AA) = FAIL wenn fehlend | qa:26-29; design:81 | behalten |
| 97 | Consistency gemessen; UI-Inventar-Snapshot | qa:30-34; fe:38-41 | durch Test GEPINNT → behalten — **korrigiert 2026-08-01 (Netz-Runde):** wie Zeile 25 — derselbe Test, dieselbe umgekehrte Lizenz. **nicht in II.12 (R5)** ⚙ `test_hooks_v2.py:test_the_ui_inventory_snapshot_rule_is_shipped` |
| 98 | Staged Testing; Vollsuite 1× pro Verdikt | qa:46-66; be:20-23; dev/pm-sk:98-104 | durch Gate ersetzt (→Fast Mode, II.10a) ⚙ `gate_pipeline.py:main` |
| 99 | real_run ist Testobjekt; SKIPPED ≠ PASS | qa:58-64; dev/pm-sk:109-117 | durch Test ersetzt (II.5 Regressionstests) ⚙ offen — kein Test im Harness und kein Kit-Skript beurteilt, ob ein Projektlauf übersprungene Tests als Erfolg verbucht; die Regel ist Rollenprosa. |
| 100 | Delivery-Freshness: served Hash == Build | qa:64-66; fe:35-37 | behalten — **kein Gate/Test (R6)** |
| 101 | jsdom-grün ≠ Browser-grün | fe:29-31 | behalten |
| 102 | high/critical Security = FAIL; DoD vollständig | qa:70-80; devops:24 | durch Gate ersetzt (→gate_pipeline; GS4/GS5) — **korrigiert 2026-07-26:** die DoD-Hälfte trägt nicht. Der Ersatz für `definition_of_done.yaml` war „AC + `INV` mit existierendem Test“, und die INV-check-Existenzprüfung ist in `report.py` ausdrücklich AUFGESCHOBEN (Phase 2, B.2-10; gemessen null Findings). Jetzt als **Prüfpflicht der QA/Reviewer-Rolle** formuliert; Validator-Regel = offener Phase-2-Rest ⚙ `gate_pipeline.py:main` |
| 103 | perf-Regression >25% untersucht | qa:66,69 | behalten |
| 104 | Devs legen eigene TSKs an (TODO→…) | be:16-24; fe:17-42 | bewusst geändert (Kernel/Orchestrator legt Tasks VOR Spawn an; V2-Automat, II.2/II.3) |
| 105 | Mockup-as-Base; nie umfärben | fe:23-27; design:64-68 | behalten (min-keep #9) |
| 106 | Devs erfinden keine Dauerregeln; ändern nie SRs | be:25-30; fe:43-48 | durch Gate ersetzt (→GS3 forbidden_scope) ⚙ `gate_write_scope.py:_assert_not_forbidden` |
| 107 | UI-Sequenz: kein neues UI-PRD vor Sichtung | dev/pm-sk:46-49 | behalten — **kein Gate (R12)** |
| 108 | Design-Ambition = User-Entscheid ZUERST | dev/pm-sk:57-70; design:104-109 | ~~durch Gate ersetzt~~ → **behalten (Prosa), korrigiert 2026-07-26:** es gibt kein Gate. `approvals.py`/`dispatch.py`/`report.py` kennen `WFR`/`wireframe` nirgends, und die II.6a-Freeze-Funktionen (`freeze_wireframe`/`freeze_design`/`freeze_architecture`) haben KEINEN Produktionsaufrufer (nur `tools/test_staging_cli.py`) und kein CLI-Subkommando. Das ist die Regel des synaipse-Vorfalls: sie steht jetzt ausdrücklich als Prosa-Pflicht mit dem PM als einzigem Wächter im Lead-SKILL. **Nachzubauen:** Freeze-Subkommandos + eine Validator-/Approval-Regel „UI-Scope ohne WFR blockt den scope-APR“ |
| 109 | Designer-Qualitätslatte non-negotiable | design:13-33 | behalten |
| 110 | Self-contained design_preview + per-view Mockups | design:52-68 | behalten (→DSN, II.6a) |
| 111 | Designer spricht nie direkt mit User | design:59,118 | behalten |
| 112 | DevOps pusht/deployt nie eigeninitiativ | devops:49-50; res/re:31 | behalten (→gate_git) — Consent-Teil **R1** |
| 113 | Fremde Docker-Projekte tabu | devops:46-48 | behalten — **kein Gate (R10)** |
| 114 | Compose-Projektname gepinnt | devops:40-45 | behalten (kit_checks warnt) |
| 115 | Partielle Läufe NIE Merge-Evidence | devops:56-58; qa:51 | durch Gate ersetzt (→Fast Mode, II.10a/II.12) — **Nachtrag 2026-07-27:** umgesetzt über `EVD.result`, das im Kernel auf `pass|fail` geschlossen ist; ein Lauf, der nicht entscheiden konnte, ist ein `fail` mit Begründung im `summary`. Ein drittes „inconclusive“ wäre der Wert, auf den ein Gate nicht handeln kann. ⚙ `backlog_types.py:EVIDENCE_RESULTS`, `quality.py:_report` |
| 116 | Pipeline bei Projektstart (Format→…→SCA) | devops:15-33; res/re:15-19 | durch Gate ersetzt (→gate_pipeline, GS5) ⚙ `gate_pipeline.py:main` |

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

### 6.5 Pro Revision gespeicherte Items — zwei Lesarten desselben Verzeichnisses (GESCHLOSSEN 2026-07-31)
`state._frozen_revision_path` definiert: „an item stored per revision IS its newest revision“ —
`WFR-0001` ist `design/wireframes/WFR-0001.r03.yaml`. `report._iter_active` liest dasselbe
Verzeichnis nach der älteren Regel „jede `*.yaml` ist ein Item“. Beide Lesarten stehen seit dieser
Runde nebeneinander, und die zweite Freigabe eines Wireframes/Designs macht sie sichtbar:

```
design/wireframes/  ->  WFR-0001.r01.yaml, WFR-0001.r02.yaml
report.validate_state -> ERROR  WFR-0001 duplicate id (also at design\wireframes\WFR-0001.r01.yaml)
```

`gate_memory_complete` blockt auf Validator-**Fehlern**, also sperrt das zweite Einfrieren eines
Wireframes jeden Merge, bis eine Revision von Hand verschwindet — was bei einem eingefrorenen,
unveränderlichen Artefakt niemand tun darf.

**Vorbestehend** (die Per-Revision-Dateinamen und die Duplikatsregel sind älter als
`_frozen_revision_path`), deshalb NICHT in der Runde geändert, die das gemessen hat: die
Reparatur sitzt in `_iter_active`, und daran hängen Validator, `session_brief`, `generated/index`
und das Dashboard — eigener Auftrag, eigene Gegenprüfung. **Zu entscheiden:** ob `_iter_active`
die Revisionsregel aus `_frozen_revision_path` übernimmt (nur die neueste Revision ist das aktive
Item, die älteren sind Historie) — die Lesart, die der Rest des Kernels bereits verwendet — oder
ob die Duplikatsregel eine Ausnahme für pro Revision gespeicherte Typen bekommt. Erste Variante
empfohlen: sie hält die Regel an EINER Stelle. Der Docstring von `_frozen_revision_path` nennt
diesen Widerspruch inzwischen ausdrücklich, damit die Definition dort nichts verspricht, was der
zweite Leser nicht einhält.

**Nachtrag 2026-07-31 (Blocker-Runde): erledigt nach Variante 1.** Die Lesart sitzt jetzt an EINER
Stelle — `state.py:split_revision` zerlegt den Dateinamen, `state.py:iter_active_items` beantwortet
daraus „welche Dateien eines aktiven Verzeichnisses sind Items“, und `state.py:revision_name` setzt
denselben Namen zusammen, den diese Leser wieder auseinandernehmen. `report.py:_iter_active`,
`state.py:_regenerate_index_locked` (der zweite Leser, der die alte Regel als eigene Kopie trug —
der Index listete das zweimal eingefrorene Wireframe als ZWEI Zeilen mit einer ID) und
`staging.py:_next_frozen_revision` lesen sie. Gemessen vorher/nachher an zwei echten
`freeze_wireframe`-Läufen: `validate` 1 error → 0 errors, `gate_memory_complete` auf `git merge`
rc 2 → rc 0, Index 2 Zeilen → 1 Zeile (Revision 2). Beide Dateien bleiben liegen; die ältere
Revision ist Historie, nicht Müll. **Gegenrichtung gemessen und erhalten:** zwei VERSCHIEDENE
Dateien mit einer ID bleiben `duplicate id`, und ein schlichtes `<ID>.yaml` neben `<ID>.rNN.yaml`
ebenfalls — zwei Heimaten für eine ID sind ein Widerspruch, kein Revisionspaar. Variante 2
(Ausnahme in der Duplikatsregel) wäre daran gescheitert: als Mutation eingesetzt macht sie genau
diesen Gegenrichtungstest rot. **Nicht geschlossen, benannt:** `generate_dashboard.py:read_item`
setzt zu einer Indexzeile weiter `<ID>.yaml` zusammen und findet für pro Revision gespeicherte
Items keine Datei (der Body bleibt leer) — vorbestehend, durch diese Runde weder besser noch
schlechter; und `state.py:_max_number` zählt `<ID>.rNN`-Dateien bei der ID-Vergabe nicht mit, was
heute folgenlos bleibt, weil kein Aufrufer `allocate_id` für einen eingefrorenen Typ ruft.

**Nachtrag 2026-07-31 (Gegenprüfung):** das Prädikat ist jetzt EINE Funktion — der erste Wurf hatte es zweimal (`_frozen_revision_path` verlangte den Item-Suffix, `iter_active_items` nahm jeden), womit `WFR-0001.r03.backup.yaml` für Validator und Index das aktive Item war, während `read_anywhere` weiter `r02` auflöste: derselbe Defekt eine Dateiform weiter. `state.py:item_revision` beantwortet die Frage für alle Leser; die zwei zusätzlich dokumentierten Bedingungen (Basis muss eine Item-ID sein; `re.ASCII`, damit `WFR-0001.r١٢.yaml` keine Revision 12 ist) sind gepinnt. `report.py:_delivery_evidence` liest jetzt ebenfalls über `iter_active_items` — die letzte private Verzeichnisliste IM Kernel. **Weiter offen, benannt:** vier private Kopien der alten Regel AUSSERHALB des Kernels — `gate_packaging_decision.py` (ARC), office `gate_proc_approved.py`, `process_doc.py`, `proc_hash.py` (PROC) — je „jede `*.yaml` ist ein Item“. Heute folgenlos, weil keiner dieser Typen im aktiven Verzeichnis pro Revision liegt; nicht gezogen, weil die Hooks stdlib-first sind und für eine Verzeichnisliste keinen Kernel-Import aufnehmen sollen. Ebenfalls offen: `WFR-0001.r2.yaml` neben `.r02.yaml` — eine wird still unsichtbar statt als `duplicate id` gemeldet; alle drei Leser sind sich einig, und nur eine handgelegte Datei erreicht es.

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

**Netz-Runde 2026-08-01 — was vor der Kürzung (II.11/3) noch entschieden werden muss.** Die
Kürzung hat jetzt Rückmeldung: `tools/test_shortening_net.py`. Offen und ausdrücklich NICHT von
dieser Runde entschieden:

1. **Die neun Zeilen mit `⚙ offen` (3, 6, 14, 48, 49, 54, 80, 82, 99).** Ihre Klassifikation sagt
   „durch Gate/Test ersetzt", der laufende Code hat keinen Ersatz — bei 3, 6, 14 und 49 nur für
   eines der Kits, in deren Text die Regel steht, was genügt. Entweder wird der Mechanismus
   gebaut, oder die Zeile wird umklassifiziert, wie Zeile 108 es 2026-07-26 wurde. Bis dahin darf
   die Prosa dieser neun Regeln beim Rückbau NICHT wegfallen. Gegenzahl: **32 Zeilen** tragen eine
   wirksame Löschlizenz — davon ruhen **12 auf einem Hook ohne Tool-Wächter** (§3) und **17
   nennen eine Spezialisten-Rollendatei**, die kein Pin bewacht. Beide Einschränkungen stehen in
   §3, wo der Ausführende sie liest.
2. **Die Regel→Sektion-Landkarte gibt es nicht.** Der Sektionspin merkt, DASS eine Sektion
   verschwindet, sich ändert oder umbenannt wird, aber nicht, WELCHE Matrixzeilen dabei ihr
   Zuhause verlieren — die Quellenspalte nennt Zeilennummern, und mindestens eine davon ist
   gemessen veraltet (Zeile 34, dev). Eine belastbare Landkarte sind 122 handgeprüfte
   Zeile↔Sektion-Zuordnungen; sie wurde bewusst nicht aus den Zeilennummern abgeleitet, weil eine
   falsche Landkarte schlechter ist als keine. Was das Netz stattdessen leistet: die Quellen-KITS
   werden aufgelöst, also fällt eine Lizenz auf, die nur in einem der Kits gilt — und ein
   Kürzel, das die Legende nicht kennt, ist ein Fehler statt einer leeren Menge.
3. **Die Zustandsautomat-Umschreibung von `session_status`** ist gemessen, aber nicht gebaut:
   Blockzahl, Nachfolger und die zwei Blöcke ohne Nachfolger stehen bei der Datei in §1.1.


---

## 9. Sektionspin-Journal (append-only)

Jede übernommene Änderung an einer Lead-Paket-Sektion, eine Zeile pro Sektion, geschrieben
von `tools/pin_constitution_sections.py --write`. Der Pin selbst steht in
`tools/constitution_section_pins.json`; dieses Journal ist der Grund, warum das Übernehmen
einer Änderung ein Vorgang ist und keine Geste. Wer hier nichts schreiben will, hat den Pin
nicht gelesen.


- 2026-08-01 · **ERSTPIN** · 91 Sektionen über 9 Dateien (drei Lead-Pakete) · keine
  Einzelbestätigung, weil es keinen Vorzustand gab, gegen den zu bestätigen wäre. Ab hier
  schreibt jede übernommene Änderung ihre eigene Zeile.