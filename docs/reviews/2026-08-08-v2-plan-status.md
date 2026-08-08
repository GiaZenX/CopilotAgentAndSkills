# TSK-0024 — Wie weit ist der V2-Plan (II.11, Schritte 0–5) abgearbeitet?

**Datum:** 2026-08-08 · **Auftrag:** `project_memory/tasks/active/TSK-0024.yaml` (type: analysis,
`allowed_scope: docs/reviews/**`) · **Methode:** read-only am laufenden Code. Jedes Verdikt unten
steht auf einem Lauf oder auf geparstem Code, nicht auf einer Zeichenkettensuche über Prosa.

## 0. Was gemessen wurde, und was ausdrücklich nicht

Alle Läufe fanden in Wegwerf-Projekten **außerhalb** des Repos statt (`%TEMP%\tsk0024*`); im Repo
wurde nichts geschrieben außer dieser Datei. Die Sonden liegen unter
`C:\Users\zenti\AppData\Local\Temp\tsk0024\` (`probe.py`, `probe2.py`, `probe3.py`, `probe4.sh`,
`probe5.py`, `probe7.sh`, `probe8.py`).

**Nicht gefahren:** `python -m pytest tools/` (schreibt nach `project_memory/.audit/`, und ein
zweiter Umsetzer arbeitete parallel im Baum). Der Suite-Lauf von heute — **2305 bestanden / 12
übersprungen** — ist eine **fremde Messung**, vom Sitzungsagenten übernommen und hier als solche
gekennzeichnet; ich habe sie nicht wiederholt. Der einzige pytest-Lauf, den dieser Bericht selbst
gefahren hat, ist `tools/test_disposition.py` (8 Tests, s. u.).

**Ausgeklammert nach II.14 (Folgearbeit, zählt nicht als offener Rest):** die Migrationsläufe für
`portfolio`, `synaipse` und `BuyPlugGo`, die `INV-HARDWARE-ORDER`-Klärung, das
`filing_plan`-Cutover, das `legacy_files`-Inventar und die Aufbewahrungsregel für
`.claude/projects`. Ebenso II.10: die Migrations-**Ausführung** ist dort selbst als Folgearbeit
markiert — das **Werkzeug** dagegen ist Teil des Harness und wird unten gemessen.

## 1. Die Zahlen des Plans gegen die Zahlen von heute

| Größe | Plan / Phase 0 | heute | Befehl, der die heutige Zahl erzeugt hat |
|---|---|---|---|
| getrackte Dateien | 274 (Messwert 2026-07-24, II.11/0) | **399** | `git ls-files \| wc -l` |
| Vollinventar der Disposition | 284 Zeilen | **284** (unverändert, s. §2/Schritt 0) | `python -m pytest tools/test_disposition.py -q` → 8 passed |
| Monolith-Abhängige (Lockstep) | „~76" (II.11/2, II.13); Phase 0 maß 82 ⚓-Zeilen | **32 Dateien nennen überhaupt noch einen der 7 Plan-Namen**, **0 zeigen auf den Zustandsort** | s. §4 |
| injizierte SessionStart-Blöcke | „ALLE ~6" (II.11/3) | **16 / 19 / 16** (dev / office / research) | AST-Zählung der `parts.append`-Stellen in `hooks/session_status.py` |
| Lead-Paket | frühere feste Grenze 25 600 B, „≤150 Zeilen" — beide gestrichen | dev **30 649**, office **31 762**, research **34 736** B, je 2 Dateien | `lead_package.size()/ceiling()/files()` je Kit aufgerufen |
| Testfunktionen | — | **1544** in 17 Dateien (inkl. `.claude/hooks/test_gates.py` mit 80) | AST-Zählung `FunctionDef`, Name beginnt mit `test_` |
| Kernel-Kommandofläche | — | **17** Unterkommandos, `update-kit` **nicht** darunter | `PYTHONPATH=team-kits python -B -m kernel.cli --help` |
| Item-Vokabular | — | 10 Typen mit Automat, 17 `ACTIVE_DIRS`, 60 Zeilen `V1_STATUS_MAPPING` | `kernel.backlog_types` importiert und ausgelesen |

**Versionsstände (alle mit `cat`/`git show` gelesen):**

| Ort | Stand | Kernel vorhanden? |
|---|---|---|
| Arbeitsbaum `team-kits/*/VERSION` | `2026.08.07-4` | ja |
| `HEAD` (feat/harness-v2) | `2026.08.04-3` | ja (16 Dateien) |
| `main` | `2026.07.18-3` | **nein** (`git ls-tree main team-kits/kernel/` ist leer) |
| Ablage `~/.claude/team-kits` | `2026.08.03-7` | ja |

Branchlage: `git rev-list --count main..HEAD` = **25** Commits; `git status --porcelain` = **60**
Einträge; `git diff --stat HEAD` = **49 Dateien, 13 227 Einfügungen, 150 Löschungen**.

## 2. Die sechs Verdikte

### Schritt 0 — Vollinventar + Paritätsmatrix + Spikes → **fertig**

`docs/reviews/phase0-disposition.md` liegt vor, §7 trägt „**BESTÄTIGT 2026-07-24**", §5 die drei
Spike-Verdikte (S1 verified, S2b negativ entschieden, S3 verified). Der Beleg ist kein Lesen des
Dokuments, sondern ein Lauf: `python -m pytest tools/test_disposition.py -q` → **8 passed** (2,84 s).
Diese Tests zählen die Zeilen der beiden Inventartabellen und halten jede Zelle und jede Zahl im
Kurzfazit dagegen — eine nachgetragene Zeile ohne Summenkorrektur ist ein Testfehler.

**Was das Verdikt nicht behauptet:** Der Bericht ist gegen **sich selbst** konsistent, nicht gegen
den Baum. Das steht im Bericht selbst (Abschnitt 1, „Dieser Abgleich ist historisch") und ist
messbar: 284 disponierte Zeilen gegen heute **399** getrackte Dateien. Der Zuwachs von 125 Dateien
ist nicht disponiert und wird von nichts gemeldet. Das ist eine Eigenschaft der Abnahme („Bericht
vom 2026-07-24, bestätigt"), kein offener Rest von Schritt 0 — aber es heißt: die Disposition ist
als **Momentaufnahme** fertig, nicht als gepflegte Liste.

### Schritt 1 — State-Kernel + Schemas → **fertig**

Gemessen an einem leeren Wegwerf-Projekt (`probe.py`):

* `ProjectState.capture("PR", {"title": …})` → `StateError: capture PR is missing required fields:
  class, problem, goal, acceptance_criteria, invariants, out_of_scope, priority` — die Pflichtfelder
  aus II.2 werden beim Schreiben durchgesetzt, nicht bloß dokumentiert.
* vollständiges `PR` → `product/active/PR-0001.yaml` + `generated/index.yaml`; `generate-index` rc 0,
  `validate` rc 0 („0 error(s), 0 warning(s)"), `doctor` rc 0 mit vollständigem Bericht.
* Schemadateien in `team-kits/kernel/schemas/`: `result_envelope.yaml`, `session_brief.yaml`,
  `arc_companion.yaml`, `wfr_companion.yaml`, `dsn_manifest.yaml` (+ README) — die vier von II.11/1
  geforderten sind da, die Status-Mapping-Tabelle aus II.10 liegt maschinenlesbar als
  `kernel.backlog_types.V1_STATUS_MAPPING` (60 Zeilen, direkt ausgelesen) statt als Schemadatei.
* Das verallgemeinerte Hash-Modul ist `kernel/hashing.py`; sein Nutzpfad lief mit: die Freigabe in
  §Schritt 2 wurde durch den **echten** `gate_approval`-Hook geprägt (`APR-0001`), was ohne das
  Hash-Modul nicht durchläuft.

### Schritt 2 — neue Hooks + Lockstep in EINEM atomaren Release → **teilweise**

**Was steht (je als Prozesslauf, JSON auf stdin, Projekt außerhalb des Repos):**

| Messung | Ergebnis |
|---|---|
| `gate_dispatch.py`, Spawn ohne Header | **rc 2** — „no HARNESS_DISPATCH header in the spawn prompt" |
| `gate_dispatch.py`, Header mit erfundener Task-Id | **rc 2** — „malformed HARNESS_DISPATCH header" |
| `gate_dispatch.py`, echter Header aus `dispatch.create_lease` | **rc 0** |
| zweiter Spawn auf derselben Lease | **rc 2** — „a second claim on one lease is blocked" |
| `dispatch.create_lease` ein zweites Mal | `DispatchError: TSK-0001 is LEASED, not READY` |
| `guard_memory_budget.py`, `MEMORY.md` mit 41 Zeilen | **rc 2** („41 lines … budget is 40 lines") |
| dieselbe Datei mit 40 Zeilen | **rc 0** |
| office `gate_ledger_valid.py`, kaputtes `ledger/2026.csv` + `git commit` | **rc 2**, mit Spaltenliste und Abhilfe |
| `guard_ledger_direct.py` in einem der drei Kits | **nicht vorhanden** (Löschung aus II.11/2 vollzogen) |

Der Rollen-Mismatch-Fall ist **nicht** sauber gemessen: mein zweiter Spawn trug dieselbe Lease, und
das Gate verweigerte ihn mit der Zweitanspruchs-Begründung, bevor die Rolle geprüft wurde. rc 2 ja,
aber aus dem anderen Grund — ich schreibe das hin, statt es als Rollenprüfung zu verkaufen.

**Lockstep — die Umstellung selbst ist vollzogen:**

* Der ausgelieferte Sweep (`tools/test_hooks.py::_sweep_state_root` gegen
  `tools/conftest.py::V1_MONOLITHS`, 15 Einträge) meldet über den ganzen Baum **0 Verstöße**
  (direkt aufgerufen, nicht über pytest).
* Kein Kit-Template legt einen Monolithen an den Zustandsort: über alle drei
  `templates/project_memory/`-Bäume gelaufen, je **leere** Fundliste.
* Der frisch installierte Zustand ist typisiert: `init_project_memory.sh dev-team` erzeugt 20
  Verzeichnisse/Dateien, keine davon ein Monolith.

**Was fehlt — und es ist genau das Wort „atomares Release":** Das Release hat an der einzigen
Stelle, an der es messbar ist, nicht stattgefunden.

1. `main` trägt weiterhin V1 (`team-kits/kernel` fehlt, dev-VERSION `2026.07.18-3`).
2. Der V2-Stand liegt auf `feat/harness-v2`: 25 Commits **plus** 60 uncommittete Einträge
   (49 Dateien / 13 227 Zeilen gegen HEAD).
3. Die globale Ablage `~/.claude/team-kits` steht auf `2026.08.03-7` — ein Zwischenstand, der weder
   `main` noch `HEAD` noch dem Arbeitsbaum entspricht.

Der Lockstep ist also **im Code** vollständig und **als Auslieferung** dreigeteilt. Solange das so
ist, kann kein Projekt „den einen Stand" installieren.

### Schritt 3 — session_status + Templates + Lead-Paket → **teilweise**

**Was steht** (gemessen am **installierten** Hook eines echten Scaffold-Laufs, `probe4.sh`: das
Repo-Kit wurde in ein Wegwerf-`$HOME` kopiert und von dort mit `scaffold_team.sh dev-team`
installiert):

* Der SessionStart-Kontext nennt `project_memory/generated/session_brief.yaml` als das, was **vor**
  der ersten Antwort zu lesen ist, samt Regenerierbefehl und dessen Pflichtflags.
* Der Wand-Block feuert: „UNFILLED PROJECT DOCUMENTS — a WALL, not a to-do: product/masterplan.md
  (gate_memory_complete: …); project_config.yaml (…)" — und `doctor` führt dieselben zwei Dateien
  unter `gated_documents`.
* Der Update-Zustandsautomat feuert und unterscheidet die Richtung: mit dem Repo auf `2026.08.07-4`
  und der Ablage auf `2026.08.03-7` kam **„KIT DOWNGRADE OFFERED, do NOT run the scaffold"**; nach
  Zurückstempeln des Repos auf `2026.01.01-1` kam **„KIT UPDATE AVAILABLE"**. Zwei der vier Zweige
  also direkt gemessen; die Zweige „MISMATCH" (unlesbarer Stempel) und „CONTENT MISMATCH" (gleiche
  Version, anderer Hash) habe ich nicht ausgelöst.
* Templates typisiert: dev `product/ system/ tasks/ design/ architecture/ approvals/ evidence/
  invariants/ inbox/ changes/ bugs/ decisions/ archive/ staging/` + `project_config.yaml`.
* Die Größenregel aus II.5 ist **hart erzwungen**, nicht nur aufgezeichnet: `tools/validate.py` im
  Kindprozess mit auf 10 B gesenktem `lead_package.ceiling` → **rc 1** mit drei Verstößen
  („lead instruction package is 30649 bytes (> 10 recorded, spec II.5)"); mit dem echten Rekord
  → rc 0. Das Repo selbst ist grün: `python tools/validate.py` → „all structural checks passed".

**Was fehlt, einzeln belegt:**

1. **Die Kürzung des Lead-Pakets ist nicht erfolgt.** Das Journal in
   `docs/reviews/phase0-disposition.md` §10 zeigt für dev `30183 → 30649 B` seit der Ersterfassung
   (zwei SHRANK-Zeilen über −2 B und −6 B, drei GREW-Zeilen über +60/+191/+221 B). II.11/3 verlangt
   die Kürzung *nach* den ersetzenden Gates aus Schritt 2 — die Gates stehen, die Kürzung steht aus.
2. **Das Netz für diese Kürzung trägt eine gezählte Lücke.** `tools/test_shortening_net.py`
   (Kopfkommentar, geparst gelesen) prüft, dass jede Löschlizenz der Paritätsmatrix ihren Ersatz als
   `datei.py:symbol` benennt und der Hook registriert ist — **aber** sechs registrierte dev-Hooks
   deklarieren keine Werkzeuge, darunter `gate_write_scope`, der meistzitierte Ersatz; für die wird
   der Matcher nicht beurteilt. Die darauf ruhenden Lizenzen sind gezählt, nicht geschlossen.
3. **ITEM-Templates existieren als Dateien nicht.** In keinem der drei
   `templates/project_memory/`-Bäume liegt ein Item-Gerüst (`find … -type f` zeigt nur `.gitkeep`,
   `README.md`, `project_config.yaml`, `product/masterplan.md` und die Referenzdateien der Kits).
   Die Funktion wird stattdessen vom Kernel getragen (Pflichtfeld-Verweigerung oben, `REQUIRED_FIELDS`
   für 17 Typen). Ob II.11/3 damit erfüllt ist, ist eine Lesart-Entscheidung — s. §6 offene Fragen.
4. **„ALLE ~6 injizierten Blöcke disponiert"** ist gegen die heutige Zahl zu lesen: es sind 16 (dev),
   19 (office), 16 (research) Emissionsstellen. Sie sind durch die AST-Zählung in
   `tools/test_shortening_net.py` gegen stilles Löschen gesichert; ob jeder einzelne Block
   *disponiert* wurde, sagt keine Messung, die ich fahren konnte.

### Schritt 4 — doctor, Scaffold/Init, Provider-Artefakte, VERSION, globale Einstiegsdateien → **teilweise**

**Was steht** (alles aus dem Scaffold-Lauf `probe4.sh` bzw. Hash-Vergleich):

* `harness doctor` läuft aus dem installierten Einstiegspunkt `scripts/harness.py` und liefert
  `kit: dev-team`, `kit_version: 2026.08.07-4`, `hook_bundle_hash == recorded_hook_bundle_hash`
  (`bundle_matches_recorded: true`), die fünf installierten Spezialisten, Lock-, Lease- und
  Validator-Stand, `record_scan_coverage`, `gated_documents` und die Capability-Matrix.
* `kit_state.json`-Konsolidierung: der Scaffold schreibt `.claude/kit_state.json ->
  restart_required (76b1962330bb)`.
* `gen_provider_artifacts.py`-Regen: „codex artifacts: .codex/config.toml + hooks.json + 4
  specialist agent(s) + 5 native skill(s)".
* VERSION + registry: `.claude/kit_version` = `2026.08.07-4`; `team-kits/registry.yaml` beschreibt
  die V2-Hierarchie (`PR -> SR -> TSK`, `requires_before_install` je Kit).
* Globale Einstiegsdateien auf dem V2-Fluss **und ausgerollt**: SHA-256 von
  `user/claude/CLAUDE.md` == SHA-256 von `~/.claude/CLAUDE.md` (`95cdcbcf762c`), ebenso
  `team-kits/registry.yaml` == `~/.claude/team-kits/registry.yaml` (`4b3d131c0261`). Zusätzlich
  gemessen: `user/claude/CLAUDE.md` nennt **keinen** der 15 V1-Monolithnamen (Bare-Name-Zählung §4).
  `user/claude/settings.json` weicht von der installierten Fassung ab (`eca627c2df4f` vs
  `09ba289cfd00`) — erwartbar, weil die Datei persönliche Werte trägt und beim Einspielen gemergt
  wird; ich habe den Merge nicht nachgemessen.

**Was fehlt:**

1. **„Migration der alten Marker" ist für einen V1-Bestand nicht gebaut.** Gemessen (`probe7.sh`):
   ein Projekt mit `.claude/kit_version = 2026.07.18-3`, Kit-Marker und einem V1-Zustand
   (`product_requirements.yaml`, `tasks.yaml`) nimmt das V2-Scaffold **kommentarlos** an — der
   Stempel steht danach auf `2026.08.07-4`, die beiden Monolithen liegen unverändert am Zustandsort.
   Erst der installierte Validator meldet sie („holds 1 V1 backlog record(s) … Remedy: run
   `python scripts/harness.py migrate --dry-run`"). Keine Datenzerstörung, aber auch keine
   Vorklassifikation.
2. **`harness.py update-kit` fehlt.** `DEC-0001` (status VALID) und `FR-0006` (status OPEN) tragen
   die Nutzerentscheidung vom 2026-08-04, dass der PM das Kit selbst einspielt; die Kommandofläche
   des Kernels führt kein `update-kit` (17 Unterkommandos, geprüft am Parser). Der ausgelieferte
   SessionStart-Text sagt heute folgerichtig „ASK THE USER TO RUN the scaffold_team script".

### Schritt 5 — Tests nach II.12 + seitliche V2-RC → **teilweise (die RC-Hälfte: nicht begonnen)**

**Testhälfte:** 1544 Testfunktionen in 17 Dateien; die Suite lief heute grün (fremde Messung,
2305/12). Der E2E-Bestand deckt die Kette an den ausgelieferten Hooks ab
(`test_e2e_the_draft_to_dispatch_chain_runs_through_the_shipped_hooks`,
`test_e2e_the_merge_gate_opens_on_evidence_a_role_produced_and_shuts_on_a_fresh_fail`, plus
Umlaut-/BOM-/Lock-Fälle). Eine **Namensdurchsicht** aller 1544 Testnamen findet keinen Treffer für
`latency`, `1000`/`thousand`, `pilot` — die Latenz-Bench und der 1000-Item-Dashboard-Fall aus II.12
haben also keinen nach ihnen benannten Test. Das ist ein Indiz, kein Beweis der Abwesenheit: ich
habe nicht alle Tests gelesen. Genau diesen Abgleich trägt das offene `FR-0004` („Stufe 5: Spec
II.12 gegen das Gebaute abgleichen").

**RC-Hälfte: nicht begonnen, und in einem Punkt bereits überholt.**

* Kein Pinning-, kein Parallelinstallations-Mechanismus: im Installer findet sich nichts dergleichen
  (`scaffold_team.sh` kennt nur Gleichstands-Erkennung und Versionsstempel), und der gemessene Lauf
  über einen V1-Bestand (oben) installiert V2 statt zu pinnen.
* Die Ablage `~/.claude/team-kits` **ist bereits ein V2-Bau** (`2026.08.03-7`, `kernel/` vorhanden,
  typisierte Templates) — also nicht eine RC *neben* V1, sondern V2 am Standardort. Der Plan macht
  das von einem bestandenen Piloten und einer ausdrücklichen Nutzerfreigabe abhängig.
* Ein Pilot ist nicht gelaufen; `FR-0004` steht OPEN.

## 3. Die Lockstep-Zahl selbst ermittelt

Der Plan nennt „~76 Monolith-Abhängige" (II.11/2, II.13), Phase 0 maß 82 ⚓-Zeilen.

**Heute, drei Erhebungen, alle selbst gefahren:**

1. `git grep -l -E "product_requirements\.yaml|system_requirements\.yaml|tasks\.yaml|design\.yaml|
   progress\.yaml|filing_log\.yaml|architecture\.yaml"` → **32 Dateien**. Davon sind 8 Dokumente in
   `docs/`, 2 Wurzeldokumente (`README.md`, `HARNESS_LOG.md`), 5 Testdateien und 17 in
   `team-kits/`.
2. Eigene Erhebung über **alle 399 getrackten Dateien** mit der Inventardefinition aus
   `tools/conftest.py::V1_MONOLITHS` (15 Einträge, importiert statt abgeschrieben) und der Regel
   „letztes Segment ist ein Monolithname **und** das Segment darüber ist `project_memory` oder es
   gibt keines": **11 Dateien**, davon 3 Dokumente in `docs/`, 2 Testdateien, und in `team-kits/`
   ausschließlich Stellen in **Docstrings/Kommentaren** (`*/hooks/_root.py`, `dev|research
   /hooks/gate_git.py`) sowie eine bewusst defensive `.gitignore`-Zeile im Office-Template.
3. Derselbe Sweep mit dem **ausgelieferten** Leser (`test_hooks._sweep_state_root`, der Python über
   AST liest, Docstrings verwirft und Kommentare über `tokenize` zurückholt): **0 Verstöße**.

Der Unterschied zwischen (2) und (3) ist genau die Docstring-Regel und keine Diskrepanz im Urteil.

**Bare-Namen** (der Name irgendwo im Text, ohne Pfadanspruch): **47 Dateien**, davon 26 in
`team-kits/` — durchgesehen: Kernel-Migrationsvokabular (`migrate.py`, `backlog_types.py`,
`state.py`, `report.py`), „V1 las X, V2 liest Y"-Kommentare in den Gates und die
`arc_companion.yaml`-Begründung zu `packaging`.

**Antwort auf die Planzahl:** von ~76/82 gekoppelten Dateien sind heute **0** gekoppelt; **32**
nennen einen Namen noch, und jede dieser Nennungen ist Prosa, Migrationsvokabular oder eine
defensive Ignorierregel. Die Umstellung ist inhaltlich durch. Nicht durch ist ihre **Auslieferung**
als ein Stand (§2/Schritt 2).

## 4. Was zwischen heute und einem lauffähigen Piloten (Schritt 5) liegt

Sortiert nach Härte, jeder Punkt mit seiner Messung oben:

1. **Ein Stand, den man installieren kann.** Heute existiert V2 dreifach verschieden
   (`main` = V1, `HEAD` = `2026.08.04-3`, Arbeitsbaum = `2026.08.07-4` mit 60 offenen Einträgen,
   Ablage = `2026.08.03-7`). Ein Pilot, der auf der Ablage startet, misst keinen dieser Stände.
   Das ist der Punkt, an dem „EIN atomares Release" noch aussteht.
2. **Die seitliche RC + das Pinning** (`FR-0004`): heute installiert der Scaffold V2 über einen
   V1-Bestand, ohne ihn zu klassifizieren (gemessen). Ohne Pin ist „bestehende Repos bleiben auf V1"
   eine Absicht, kein Mechanismus.
3. **`harness.py update-kit`** (`DEC-0001` / `FR-0006`): ohne das Kommando kann der PM ein Update
   nicht selbst einspielen — die Nutzerentscheidung vom 2026-08-04 ist im Code nicht abgebildet.
4. **Der II.12-Abgleich selbst** (`FR-0004`, Teil 1): welche Phase-0-Aussagen gemessen und welche nur
   gelesen waren. Zwei benannte Kandidaten aus diesem Bericht: Latenz-Bench und
   1000-Item-Dashboard tragen keinen nach ihnen benannten Test.
5. **13 offene BUG-Items und 10 offene FR-Items** im Zustand dieses Repos (gezählt über
   `generated/index.yaml`: 78 Items, davon `BUG OPEN` 13, `FR OPEN` 10, `PR DRAFT` 3,
   `SR PROPOSED` 8, `TSK DRAFT` 21 + `TSK FAILED` 1, `DEC VALID` 22). Darunter mindestens zwei, die
   einen Piloten direkt treffen: `BUG-0005` (der Sitzungsbrief verliert die letzte
   Nutzerentscheidung) und `BUG-0010` (ohne Lease ist eine Aufgabe nicht ehrlich abschließbar).
6. **Die Kürzung des Lead-Pakets** (§2/Schritt 3): heute lädt jede Sitzung 30–35 KB Verfassung +
   Leaddatei. Das blockiert keinen Piloten, verfälscht aber jede Aussage über Kontextkosten, die
   der Pilot liefern soll.

Nicht auf dieser Liste, weil II.14: die Migration von `portfolio`, `synaipse`, `BuyPlugGo` und die
Transkriptregel. Das **Werkzeug** dafür läuft: `migrate --dry-run` gegen einen handgebauten
V1-Zustand liefert Plan-Digest, Import-, Unentscheidbar-, Blockiert- und
„carried, not translated"-Listen und **verweigert** die Ausführung, solange etwas offen ist (rc 1) —
inklusive der ehrlichen Zeile, dass II.10s fail-closed-Wächter über zurückbehaltene V1-Dateien
**nicht** gebaut ist.

## 5. Offene Fragen (nicht entscheidbar mit dem, was ich messen konnte)

1. **Ist die Ablage auf V2 eine Entscheidung oder ein Nebeneffekt?** `~/.claude/team-kits` steht auf
   `2026.08.03-7` (V2). Der Plan macht das vom Piloten plus Nutzerfreigabe abhängig. Ob diese
   Freigabe erteilt wurde, steht in keiner Datei, die ich gelesen habe.
2. **Was heißt „ITEM-Templates" in II.11/3?** Dateien gibt es nicht; die Pflichtfelder erzwingt der
   Kernel. Beides erfüllt denselben Zweck — welche Lesart der Plan meint, entscheidet der Nutzer.
3. **Der Ablageort der Vergleichsversion ist providerabhängig.** `scaffold_team.sh` liest `$HOME`,
   `session_status.py` liest `os.path.expanduser("~")` — unter Windows also `USERPROFILE`. Gemessen
   in `probe4.sh`: mit gesetztem `HOME` auf ein Wegwerf-Verzeichnis meldete der Hook trotzdem den
   Stand aus dem echten Profil. Auf einem normalen Host fallen beide zusammen; wo nicht, vergleicht
   der PM gegen eine andere Ablage, als der Installer benutzt. Ich führe das als Beobachtung, nicht
   als Befund — ich habe keinen Fall gemessen, in dem das im Betrieb schadet.
4. **Der Zustand dieses Repos taugt nicht als Fortschrittsmaß.** 21 TSK stehen auf DRAFT, während
   ihre Arbeit im Baum liegt. Deshalb steht in diesem Bericht kein einziges Verdikt auf einem
   Item-Status.
5. **Die Richtungsprüfung fehlt im „seit der letzten Sitzung geändert"-Zweig.** Gemessen: nachdem
   ich `.claude/kit_version` von `2026.08.07-4` auf `2026.01.01-1` zurückgeschrieben hatte, meldete
   `session_status` „KIT UPDATED since this repo's last session: 2026.08.07-4 -> 2026.01.01-1",
   während der Ablagen-Vergleich im selben Lauf sauber zwischen Update und Downgrade unterscheidet.
   Der Weg dorthin führt über ein handgeschriebenes `kit_version`, also über etwas, das der Scaffold
   nie erzeugt — ich melde es als Beobachtung und nicht als Befund, weil ich keine Kette gemessen
   habe, die ohne Handarbeit dorthin kommt.
