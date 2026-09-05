# TSK-0126 — Merge-Runde Generation 4 (PR-0003), Merge-Protokoll

Basis: `feat/harness-v2` @ `75a00d1`, Haupt-Checkout `C:\Offline Repos\AgentAndSkills`.
Vier Ströme, vier Patches, jeder mit eigenem PASS-Urteil. Kein Commit, kein Push in dieser Runde.
Arbeitsverzeichnis der Runde: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0126/`.

---

## 0. Der verworfene Weg (eine Zeile, FR-0084-Form)

Verworfen: die vier Ströme als vier `git merge`-Vorgänge über ihre Arbeitsbäume
(`_worktrees/g4-*`) zusammenzuführen statt über ihre Patches — abgelehnt, weil ein Arbeitsbaum
neben dem Patch noch Probier-Dateien, vorläufige `VERSION`-Stempel und Rig-Reste trägt und ein
Merge über den Baum sie stillschweigend mitnimmt; die Generation-3-Regel („jeder Strom wird aus
seinem PATCH gemergt") ist genau daraus entstanden.

---

## 1. Die vier Patches — Eingangsmessung

| Strom | Patch | Bytes | Köpfe | Zeilen | CR-Bytes | VERSION-Hunks |
|---|---|---|---|---|---|---|
| G4-4 hygiene (TSK-0125) | `_round-scratch/TSK-0125/stream-hygiene.patch` | 90 217 | 10 | 1376 | **0** | **0** |
| G4-2 kernel (TSK-0122) | `_round-scratch/TSK-0122/stream-kernel.patch` | 268 876 | 18 | 4281 | **0** | **0** |
| G4-1 testgate (TSK-0121) | `_round-scratch/TSK-0121/stream-testgate.patch` | 336 024 | 24 | 5534 | **0** | **0** |
| G4-3 procedure (TSK-0123) | `_round-scratch/TSK-0123/stream-procedure.patch` | 127 110 | 20 | 1829 | **0** | **0** |

Gemessen von `_round-scratch/TSK-0126/inspect_patches.py`. **Kein Patch trägt einen VERSION-Hunk**
— die Zuschnitt-Regel aus `DEC-0070` hat gehalten; kein Zuschnitt-Befund an dieser Stelle.

Die Nähte, die aus den Patch-Köpfen selbst folgen (eine Datei, mehr als ein Strom):

| Datei | Ströme |
|---|---|
| `.claude/hooks/test_gates.py` | hygiene, kernel, testgate |
| `docs/POST_V2_WISHLIST.md` | alle vier |
| `docs/reviews/phase0-disposition.md` | testgate, procedure |
| `tools/constitution_section_pins.json` | testgate, procedure |

`tools/lead_package_sizes.json` steht in **keinem** zweiten Patch (nur G4-3) — die im Auftrag
erwartete Naht „+886 B ×3 plus was die anderen Ströme wachsen ließen" ist deshalb keine
Patch-Kollision, sondern eine **Nachrechnung** (Naht 3).

---

## 2. Anwendungsreihenfolge und Zeilenenden

1. **G4-4 hygiene** (`git -c core.autocrlf=false apply`) — rc 0, 10/10 sauber.
2. **`python tools/normalise_line_endings.py --apply`**
   - **vorher** (`_round-scratch/TSK-0126/eol_state.py`): 1794 verfolgte Dateien, **53** Textdateien
     mit CR-Bytes, 516 Binärdateien mit CR.
   - Werkzeug: **52 normalisiert, 1 nicht erreichbar** (`project_memory/.audit/hook_events.jsonl`,
     kanonischer Zustand — Gate 1).
   - **nachher**: **1** Textdatei mit CR, genau die eine nicht erreichbare.
   - Gegenprobe: `git diff --numstat` über die 52 ist **leer**, `git ls-files --eol` meldet
     `i/lf w/lf` — der Indexblob war schon LF, die Reparatur betrifft nur den Arbeitsbaum.
     `git status` listet sie trotzdem (Stat-Cache, Größenwechsel), `git diff HEAD` — woraus Gate 3
     seinen Hash bildet — sieht sie nicht. Für den Lead heißt das: die ~52 „geänderten" Dateien in
     `git status` tragen keinen Inhalt in den Commit.
3. **G4-2 kernel** — 17/18 sauber, `docs/POST_V2_WISHLIST.md` von Hand (Naht 5).
4. **G4-1 testgate** — 22/24 sauber, `test_gates.py` und die Löcherliste von Hand (Nähte 1, 5).
5. **G4-3 procedure** — 18/20 sauber, Löcherliste und Dispositionsjournal von Hand (Nähte 4, 5).

---

## 3. Nahttabelle — Auflösung und Schiedsrichter

| # | Naht | Auflösung | Schiedsrichter, gemessen |
|---|---|---|---|
| 1 | `.claude/hooks/test_gates.py` | hygiene und kernel sauber; von G4-1 die vier Tabellen-Hunks per `git apply`, der fünfte (reiner Anhang, 750 Zeilen) von Hand angehängt, nachdem geprüft war, dass er nichts entfernt | `_round-scratch/TSK-0126/ast_union.py`: Basis 865 Definitionen, Vereinigung 975, **gemergt 975**, 0 fehlend, 0 überzählig. `ast_toplevel.py` rechnet G4-2s veröffentlichte Tabelle nach: **18 entfernt / 10 neu / 5 geändert**, und die fünf geänderten sind namentlich die von G4-2 genannten |
| 2 | die drei Verfassungen | G4-1s ein Wort (`gate_test_scope`) in die Inventarzeile ×3; G4-2s vier Sätze als Prosa (Abschnitt 3a); die fünf toten Zitate umgehängt | `tools/test_shortening_net.py` 2 rot → grün; `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text` grün; `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` rot → grün |
| 3 | `tools/lead_package_sizes.json` | G4-3s +886 B ×3 kamen mit dem Patch; die Sätze dieser Runde wachsen weiter, also EINMAL neu aufgezeichnet: dev 50 094 → **51 847** (+1753), office 55 665 → **56 728** (+1063), research 53 099 → **54 162** (+1063) | `python tools/record_lead_package_sizes.py` ohne Argument meldet keine Abweichung mehr; drei Journalzeilen angehängt |
| 4 | `docs/reviews/phase0-disposition.md` | G4-1s 3 Zeilen kamen mit dem Patch; G4-3s 16 Journalzeilen + 4 Trenner + 1 verschobene Größenzeile von Hand angehängt (`seam_disposition.py`, verweigert eine doppelte Anwendung) | `git diff --numstat` = **40 / 2** (Endstand): 25/1 nach dem Zusammenführen der beiden Ströme — G4-3s angekündigte 21 plus G4-1s 4 — plus die 9 Pin-Zeilen und 3 Größenzeilen, die diese Runde für ihre EIGENEN Verfassungssätze angehängt hat, und die eine ergänzte Begründung. Die 25/1 der ersten Fassung waren die Zahl VOR dem eigenen Anhang (Prüfrunde 1, M3.2) |
| 5 | `docs/POST_V2_WISHLIST.md` | alle vier Ströme schreiben dieselben zwei Stellen; `seam_wishlist.py` nimmt die Zusatzzeilen aus jedem Patchteil, sortiert die Übersichtszeilen nach Nummer und hängt die Abschnitte in Nummernordnung an | Abschnitte in der Reihenfolge H151 … H165, Übersichtstabelle H21 … H165 aufsteigend; Migrationslauf (Abschnitt 4) |
| 6 | `tools/provider_observations.json` | kam mit G4-1s Patch | `git diff --numstat` = **1 / 1**, Datei ist gültiges JSON |
| 7 | `team-kits/*/hooks/_kernel.py`, `team-kits/kernel/kitupdate.py` | je genau ein Schreiber — `_kernel.py` steht nur im testgate-Patch, `kitupdate.py` nur im hygiene-Patch | Dateilisten der vier Patches (`files-*.txt`); `_kernel.py` ×3 byte-gleich `13e47244d9aa` |
| 8 | Registrierungen von Gate 5 | `.claude/settings.json` mit `timeout: 120`; die drei Kit-Registrierungen **ohne** `timeout` — das ist die vom Lead ANGENOMMENE AC-2-Abweichung (eine fehlende Frist ist das bekannte Standardfenster des Providers, aus dem `_kernel.registered_window()` ableitet), kein Versehen dieser Runde | `.claude/hooks/test_gates.py` (darin die Settings-Tests, Abschnitt 8); `mirrors.py`: der neue Kit-Haken ×3 byte-gleich — der Hash steht **nur** in Abschnitt 8, weil er sich mit jeder Nacharbeit am Haken bewegt und zwei Werte für eine Datei in einem Dokument der Befund M3.1 der Prüfrunde 1 waren |
| 9 | `H158` | **bleibt OFFEN.** `team-kits/*/hooks/_routine.py` und `session_status.py` sind gegen `75a00d1` unverändert (`git diff --numstat` leer), also ist kein Ereignis-Auslöser gebaut | `tools/test_review_procedure.py::test_no_occasion_makes_the_audit_run_due_and_that_is_the_seam` — **1 passed**, und grün heißt nach seiner eigenen Konstruktion „kein Auslöser" |
| 10 | Zeiger | jeder `DEC`/`H`/Test-Zeiger des gemergten Baums löst auf | `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` grün; `.claude/hooks/test_gates.py` Selbstprüfung grün (Abschnitt 6) |

### 3a. Was in den Verfassungen wirklich steht

G4-2 hat seine Sätze auf **Deutsch** übergeben (Protokoll §8); die drei Verfassungen sind
**englische** Texte. Übernommen sind Inhalt und Testnamen, die Formulierung ist übersetzt — das ist
die einzige Abweichung von „wörtlich".

* **Lease-Verweigerung + Arbeitsbaum** — ersetzt den Absatz-Lead-in
  „…and nothing checks that for you." durch „…and the kernel refuses an overlap." und den
  Schlusssatz; byte-gleich in allen drei Verfassungen, Schiedsrichter
  `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`.
* **Posteingangs-Regel (DEC-0066)** — ein neuer Absatz, byte-gleich in allen drei
  (dev §4, research §4, office §1a); nennt `backlog_types.is_inbox_type` statt einer Typenliste.
* **Architektenschritt mit der KORRIGIERTEN SR-Pflicht (DEC-0072)** — nur in `dev-team` §4, und
  seit `DEC-0074` ist das nicht mehr nur eine Textentscheidung, sondern die gebaute Reichweite:
  der Kernel fragt die Pflicht nur in einem Projekt, das eine Heimat für `SR` hat, und das ist
  von den drei Vorlagen allein die von dev-team.
  **Korrektur gegenüber der ersten Fassung dieses Protokolls** (Prüfrunde 1, B1): dort stand,
  research werde „nie gefragt", weil seine Aufträge von einem `EXP` ableiten. Das ist FALSCH für
  jeden Auftrag, der von der `RQ`-Wurzel oder von einem `HYP` ableitet — gemessen an einem Piloten
  aus der research-Vorlage: beide REFUSED. Der Sachverhalt und seine Auflösung stehen in
  Abschnitt 12 (B1) und in `H163`.
* **Die fünf toten Zitate** von `test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`:
  drei Verfassungen (im ersetzten Absatz) und die zwei `parallel-streams`-Skills; die beiden Skills
  sind nach der Änderung byte-gleich (`f1f07e354ae8`).
* **Abschnitts-Pins EINMAL neu geschrieben**, nachdem alle Sätze standen: 9 Sektionen
  (3× Haken-Inventar, 3× Hierarchie, 3× Arbeitsschleife), eine Journalzeile je Sektion.

### 3b. „Hole items" als vierter Satz — benannte Abweichung

Der Auftrag zählt für die Verfassungen „SR duty; inbox rule; **hole items**; lease refusal".
Übergeben hat G4-2 (Protokoll §8, Nacharbeit 3) vier Sätze: Lease-Verweigerung, Lease/Arbeitsbaum,
Architektenschritt, Posteingangs-Regel. Ein Satz über Löcher als Items ist **nicht** darunter, und
gemessen (Grep über `team-kits/*/constitution/AGENTS.md`, `*/skills/**`, `*/agents/**`): kein
Kit-Text nennt `ACCEPTED_EXCEPTION`, `hole_number` oder `hole_exception`, und keiner behauptet
etwas über Lücken, das `DEC-0073` falsch gemacht hätte — der „kit-gap log" (`report-gap`) ist eine
andere Sache. Es gibt hier also nichts zu korrigieren; ein neuer Absatz wäre eine Behauptung ohne
Anlass. Geliefert sind die vier übergebenen Sätze.

---

## 4. Der Migrationslauf — Probelauf hier, schreibender Lauf beim Nutzer

**ENDSTAND, gemessen nach der Nacharbeit** — das ist die Tabelle, gegen die der Nutzer seinen
EINEN schreibenden Lauf vergleicht. Alle Zahlen aus
`_round-scratch/TSK-0126/migration_apply_copy.py`, Lauf vom 2026-09-05 nach B1/B2, eigene Kopie
von Dokument UND Zustand, vollständig ausserhalb des Repos:

| Messung | Wert |
|---|---|
| Dokument vorher | **804 292 B / 9858 Zeilen** (Stand nach der Nacharbeit 2) |
| Lauf 1 | rc 0, **155 Items, 155 Prosadateien**, 0 Kollisionen |
| Dokument nachher | **192 003 B / 2453 Zeilen** |
| Lauf 2 | rc 0, **0 geschrieben, 155 schon im Bestand** |
| sha256 nach Lauf 1 / Lauf 2 | identisch, **`61988c1592b26a1a…`** |
| erzeugter Zeigerindex | vorhanden, **155 Zeilen**, letzte `[H165](docs/holes/H165.md) BUG-0247` |
| `validate` über den migrierten Bestand | **0 Fehler / 71 Warnungen** — dieselbe Zahl wie über den UNmigrierten (gemessen), die Migration fügt keine hinzu |

Die Rechnung: 140 Einträge an `75a00d1` + 12 der vier Ströme (H151–H162) + 3 dieser Runde
(H163–H165) = **155**. G4-2s eigene Zahl 143 war seine Kopie (140 + seine drei).
*Was in der ersten Fassung dieses Abschnitts stand — 152 Items, 191 513 B, `be9a465b` — war die
Messung VOR H163/H164 und vor der Nacharbeit; sie ist ersetzt, nicht ergänzt (Prüfrunde 1, M3.3).*
Gemessen dabei auch, dass eine Übersichtszeile OHNE `### H<n>`-Abschnitt von nichts migriert wird:
H165 nur als Zeile ergab wieder 154 Items — der Abschnitt ist nachgezogen.

**Die sieben migrierten Richter**, gemessen in einer `.git`-losen Kopie des GEMERGTEN Baums
(`_round-scratch/TSK-0126/migrated_judges.py`, Lauf `judges-run6.txt`): Migration 155/155, danach
**7 passed**. Im Haupt-Repo sind sie bis zum schreibenden Lauf rot — das ist erwartet und keine
Feststellung.

**Die eine Zeile für den Lead**, aus der Repo-Wurzel `C:\Offline Repos\AgentAndSkills` — seit
Nacharbeit 3 eine KERNEL-Zeile, die in der Sitzung genommen werden kann (Abschnitt 12d):

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory migrate-holes --related-pr PR-0003 --apply
```

Die Werkzeug-Zeile `python -B tools/migrate_holes.py --root project_memory --related-pr PR-0003
--apply` tut dasselbe — dieselbe Tür, ein dünner Aufrufer — und ist gemessen ebenfalls nicht
verweigert. Warum die Kernel-Zeile trotzdem die übergebene ist, und was die Messung an Gate 1
gegenüber der Erwartung ergeben hat, steht in Abschnitt 12d.
Korrektur zu G4-2 §7: das dort vorangestellte `PYTHONPATH=team-kits` ist für die WERKZEUG-Zeile
nicht nötig (das Skript legt `team-kits` selbst auf `sys.path`, gemessen); für die Kernel-Zeile
ist es das Gegenteil — ohne es findet der Interpreter das Modul `kernel` nicht.

---

## 5. Merge-Befunde — was die Nähte zeigen und kein Strom sehen konnte

Die volle Suite ist in dieser Runde nicht Formsache gewesen: **435 failed / 4246 passed** im ersten
Lauf. Nichts davon war Zufall, und nichts davon konnte ein Strom sehen — `DEC-0050` gibt einem
Strom die lesenden Suiten, und genau die Suiten, die keiner gefahren hat, bauen ihre Leases selbst.

| # | Befund | Klasse | Erledigt |
|---|---|---|---|
| M1 | Die Architektenschritt-Pflicht (`DEC-0072`) fragt JEDES Projekt nach einem `SR`. Weder office noch research hat einen (die zweite Hälfte fand die Prüfrunde 1, B1) | Kernel × Kit | **geschlossen in der Nacharbeit** (`DEC-0074`, Abschnitt 12), `H163` |
| M2 | G4-2s Umhängen des toten Testnamens war mechanisch: drei Sätze in `H136` behaupten weiter „nichts verweigert ein überlappendes Paar" und zitieren daneben den Test, der die Verweigerung misst | Prosa | **hier korrigiert** (Zusammenfassungszeile + zwei Absätze) |
| M3 | Die Migration liest einen MODULnamen in Backticks als Testzitat und schreibt ihn ins Item; der Richter merkt es erst danach, und ein zweiter Lauf repariert nichts | Werkzeug | **benannt: `H164`**, der Einzelfall vor dem schreibenden Lauf korrigiert |
| M4 | `H159` trug genau so eine Spanne (`test_gates`) | Prosa | **hier korrigiert** (1 failed → 7 passed) |
| M5 | 435 Suitenknoten leasen ohne `conftest.drive_task_to` und schulden seit dieser Generation den Architektenschritt | Suite × Kernel | **hier repariert** (14 Stellen + der CLI-Weg) |
| M6 | Vier Stellen leasen ZWEIMAL gegen ein Repo und stossen auf die neue Überlappungs-Verweigerung | Suite × Kernel | **hier repariert** (eigene Bereiche) |
| M7 | G4-4s Bytecode-Prüfung verlangt rc 0 von jedem Werkzeug; G4-2s `tools/migrate_holes.py` verweigert einen Aufruf ohne `--root` | Suite × Werkzeug | **hier repariert** (Eigenschaft „kein Traceback" statt rc 0, plus der Test, den sie nennt) |
| M8 | G4-1s Kit-Haken nennt `test_surface` in Backticks; `test_migrate` liest das als Testzitat | Kit × Suite | **hier korrigiert** ×3 |
| M9 | Derselbe Kit-Haken buchstabiert eine `evidence`-Zeile, die argparse zurückweist (`--artifact-ref`, `--summary` fehlen) | Kit × Kernel | **hier korrigiert** ×3 |
| M10 | Die Paritätsmatrix zeigt mit `enf§1.gate-test` auf `ENFORCEMENT.md`; G4-1s neuer Abschnitt macht den Anker **mehrdeutig** | Kit × Doku | **hier korrigiert** (Zeiger verlängert) |
| M11 | Nach dem Stempel geänderte Kit-Dateien lassen ~25 Installer-/Scaffold-Tests mit „VERSION not bumped" fallen | Reihenfolge | **gemessen**, Stempel zuletzt |

### Rot-zuerst, gemessen

| Fix | Vorher | Nachher |
|---|---|---|
| G4-1s Wort in den drei Verfassungen | `tools/test_shortening_net.py` **2 failed / 34 passed** | 36 passed |
| die toten Zitate | `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` **1 failed / 60 passed** | 61 passed |
| M4 (`H159`s Spanne) | die sieben Richter über der migrierten Kopie **1 failed / 6 passed** | **7 passed** |
| die Spanne in `H164`s EIGENER Prosa (derselbe Defekt, den der Eintrag beschreibt) | **1 failed / 6 passed** | **7 passed** |
| M5/M6 | volle Suite **435 failed / 4246 passed** | Abschnitt 8 |
| M7 | in einer Kopie ausserhalb des Repos: Importfehler in `tools/bump_kit_version.py` gepflanzt → der Knoten **rc 1**, sauber **rc 0**, zurückgesetzt **rc 0** | — |
| M8 | `tools/test_migrate.py::test_every_test_the_shipped_code_cites_by_name_is_a_test_that_exists` **1 failed** | 1 passed |
| M9 | `tools/test_hooks.py::test_every_evidence_command_a_text_spells_names_every_argument_the_cli_requires` **1 failed** | 1 passed |
| M10 | `tools/test_parity_sources.py` **2 failed / 7 passed** | 9 passed |

---

## 6. `H158` — die Entscheidung dieser Runde

**Bleibt OFFEN.** Gemessen statt erinnert: `team-kits/*/hooks/_routine.py` und `session_status.py`
sind gegen `75a00d1` **unverändert** (`git diff --numstat` leer), und
`tools/test_review_procedure.py::test_no_occasion_makes_the_audit_run_due_and_that_is_the_seam` ist
**grün** — was nach seiner eigenen Konstruktion heisst, dass kein Ereignis-Auslöser gebaut wurde.
Die Grenzaussage in den drei Auditor-SKILLs und den drei Rollendefinitionen bleibt damit richtig
und wird nicht angefasst.

---

## 7. Die Löcherliste in einer Ordnung

Reihenfolge im Dokument (Übersichtstabelle und Abschnitte, beide aufsteigend geprüft):

| Loch | Strom | Stand |
|---|---|---|
| H151 | G4-1 | OFFEN, gemessen |
| H152 | G4-1 | OFFEN — EINE Fail-open-Klasse |
| H153 | G4-1 | OFFEN — zwei benannte Ausnahmen |
| H154 | G4-2 | OFFEN, zwei Klassen |
| H155 | G4-2 | OFFEN, zwei Klassen |
| H156 | G4-2 | OFFEN, zwei Klassen |
| H157 | G4-3 | OFFEN |
| H158 | G4-3 | OFFEN — hier bestätigt (Abschnitt 6) |
| H159 | G4-3 | OFFEN |
| H160 | G4-4 | OFFEN |
| H161 | G4-4 | OFFEN (Naht) |
| H162 | G4-4 | GESCHLOSSEN für die gemessene Lastklasse, mit benanntem Rest |
| **H163** | **Merge** | **GESCHLOSSEN** durch `DEC-0074` + `DEC-0079` (Nutzerentscheidung 2026-09-05, in Prüfrunde 2 präzisiert): gelesen wird die AUSLIEFERUNG des Kits, nicht der Bestand des Projekts. Rest: wo der Kit-Store nicht erreichbar ist, fällt die Ableitung fail-closed und FRAGT |
| **H164** | **Merge** | **OFFEN, gemessen, bewusst nicht geschlossen** |
| **H165** | **Merge** | **GESCHLOSSEN für beide Shell-Expansionen, die dieser Leser ausrechnen kann** — Glob (Prüfrunde 1, B2) und Klammer (Prüfrunde 2, R2-B4) — mit zwei benannten Über-Verweigerungen: ein Bereich `{1..9}` und ein QUOTIERTER Glob; dazu eine Fläche ohne `members` fail-closed |

---

## 8. Läufe und Stempel

| Lauf | Ergebnis | Dauer |
|---|---|---|
| `pytest tools/` **Lauf 1** (nach den vier Patches, nach dem ersten Stempel) | **435 failed / 4246 passed / 14 skipped** | 40:36 |
| `pytest tools/` **Lauf 2** (nach M5–M10, nach dem zweiten Stempel) | **4 failed / 4678 passed / 14 skipped** | 42:12 |
| `pytest tools/` **Lauf 3** (Ende der Erstrunde) | **4682 passed / 14 skipped / 0 failed** | 42:28 |
| `pytest tools/` **Lauf 4**, nach der Nacharbeit 1 (B1/B2/M1/M2) | **4683 passed / 14 skipped / 0 failed** | 56:02 |
| `pytest tools/` **Lauf 5**, nach der Nacharbeit 2 (R2-B1/B3/B4, M1–M3) | **4684 passed / 14 skipped / 0 failed** | 44:45 |
| `pytest tools/` **Lauf 6**, nach der Nacharbeit 3 (R3-B1, R3-M1) | **4685 passed / 14 skipped / 0 failed** | 45:23 |
| `pytest tools/` **Lauf 7 — DER LIEFERLAUF**, nach dem Kernel-Kommando `migrate-holes` | **4687 passed / 14 skipped / 0 failed** | 46:24 |
| `.claude/hooks/test_gates.py` in voller Länge, nach dem Kernel-Kommando | **7 failed / 541 passed** — genau die sieben migrierten Richter, rot bis zum schreibenden Migrationslauf (erwartet, kein Befund); 541 = die 537 der Erstrunde plus drei Knoten aus B2 plus den Klammer-Knoten aus R2-B4 | 15:16 |
| `python -m ruff check` über `team-kits tools docs .claude .github user` | **All checks passed** | — |
| `python tools/validate.py` | **all structural checks passed** | — |

Beide vollen Läufe sind mit `DELIVERY_RUN=TSK-0126` gefahren; die Zeile ist die, die das
registrierte Gate 5 durchlässt (Tabelle unten). Zwischen Lauf 2 und Lauf 3 wurde EINE Datei
geändert (`tools/test_hooks_v2.py`, die vier Bereiche aus `src/…` heraus — `src/` enthält jeden
Unterpfad, deshalb war `src/second/` keine Trennung); Lauf 4 steht nach der ganzen Nacharbeit und
deckt jede in ihr geänderte Datei mit (`DEC-0063 (4)`).

**`ruff` über das GANZE Repo ist rc 1**, und der eine Befund liegt ausserhalb des `allowed_scope`
dieses Items: `project_memory/staging/generation-5/capture_dec_office_ladder.py:65` (E402, ein
`import yaml` nach ausführbarem Code). Die Datei ist in dieser Sitzung vom Lead geschrieben worden
und gehört nicht dieser Runde; `project_memory/**` ist hier `forbidden_scope`, also ist sie
benannt und nicht angefasst. Über den vollen `allowed_scope` gemessen: **All checks passed**
(`_round-scratch/TSK-0126/run_ruff_scope.py` misst beide Seiten in einem Lauf).

**Stempel:** `python tools/bump_kit_version.py` → `team-kits/{dev,office,research}-team/VERSION` =
**`2026.09.05-6`**, und nach dem Lieferlauf `--check` → **„unchanged" ×3** (gemessen). Sechsmal
gestempelt über die Runde und darum benannt: ein Stempel muss VOR jedem Urteil stehen (M11/Z8 —
ohne ihn fallen ~25 Installer-/Scaffold-Tests mit „VERSION not bumped", in dieser Runde zweimal
gemessen, zuletzt 8 rote Knoten in `tools/test_hooks.py` nach der Nacharbeit 2), also folgt jeder
Kit-Änderung ein Stempel und dann der Lauf. Ausgeliefert wird `-4`; die vorläufigen Stempel der
vier Ströme sind alle abgelöst.

**Umfang am Ende:** `git diff --stat HEAD` = **84 Dateien, +13 505 / −531** (zwei Dateien mehr: `team-kits/kernel/holes.py` und der Lauf-Protokollordner neben diesem Dokument).
Ausserhalb des `allowed_scope` liegen `radar/decided.md` (inhaltlich **9/0** geändert),
`.gitignore` und `user/claude/statusline.py` (beide nur Zeilenenden, inhaltsgleich zu HEAD, Z6) und
die untracked `radar/2026-09-04-claude.md`, `radar/2026-09-05-codex.md`. `radar/**` ist in allen
drei Fällen die Triage des **Leads** — Zeitstempel und Inhalt weisen es aus, eine der neun Zeilen
kündigt die Merge-Prüfrunde an —, nicht ein Schreibvorgang dieser Runde; sie fahren im selben
Commit mit, und ob sie hineingehören, entscheidet der Lead (Prüfrunde 2, R2-M3).

**Gate 5 als Prozess gemessen** (`_round-scratch/TSK-0126/probe_gate5b.py`; die Registrierung in
`.claude/settings.json` bindet erst beim nächsten Sitzungsstart, also der Haken selbst mit
JSON auf stdin und dem `cwd`, das der Provider mitschickt):

| Zeile | rc |
|---|---|
| `python -m pytest tools/ -q` | **2** — „runs the WHOLE declared test surface `tools`, and nothing on it says this is the delivery run" |
| `DELIVERY_RUN=TSK-0126 python -m pytest tools/ -q` | **0** |
| `DELIVERY_RUN=TSK-0121 …` (geschlossenes Item) | **2** — „leads no open work" |
| `DELIVERY_RUN=nonsense …` | **2** |
| `python -m pytest tools/test_repo_hygiene.py -q` (eine Datei) | 0 |
| zwei Dateien / ein Knoten | 0 / 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **2** — auch die Haken-Suite ist eine erklärte Fläche und braucht das Präfix |

Ohne `cwd` im Payload antwortet das Gate auf JEDE dieser Zeilen mit rc 2 und dem Satz „could not be
placed" — das ist sein fail-closed-Zweig für ein Payload ohne Arbeitsverzeichnis, nicht sein Urteil
über die Zeile. Beide Messungen stehen hier, weil die erste ohne die zweite falsch gelesen würde.

**Spiegel, ENDSTAND gemessen** (`mirrors.py`, nach der Nacharbeit 2): `hooks/gate_test_scope.py` ×3
**`47cb66f39a3c`**, `hooks/_kernel.py` ×3 `13e47244d9aa`,
`templates/repo/scripts/kit_browser_checks.py` (dev = research) `1a7077452cf4`,
`skills/parallel-streams/SKILL.md` (dev = research) `f1f07e354ae8`. Der Haken-Hash steht **nur
hier**: er bewegt sich mit jeder Nacharbeit am Haken, und zwei Werte für eine Datei in einem
Dokument waren der Befund M3.1 der Prüfrunde 1.

**Zeilenenden, Endstand:** 1804 verfolgte Dateien (1794 plus die zehn neu aufgenommenen),
**1** Textdatei mit CR — die eine unerreichbare (`project_memory/.audit/hook_events.jsonl`).

---

## 9. (g) — die Zeile je Strom für die Rückschau der Generation 4

| Strom | Tier | Runden (Bericht + Nacharbeiten) | Prüfungen | Tokens Umsetzer / Prüfer | Wandzeit gearbeitet / Spanne | Leerlauf durch Absturz |
|---|---|---|---|---|---|---|
| G4-1 TSK-0121 | Opus | 1 + 2 Nacharbeiten + 2 Abschlüsse | 5 (FAIL / FAIL / FAIL o. Blocker / FAIL o. Blocker / **PASS**) | ~1,45 M (eigene Schätzung) / ~2,2 M (255+334+405+453+469 k) | ~12–13 h (Schätzung) / ~20 h 15 | 4 Abstürze |
| G4-2 TSK-0122 | Opus | 1 + 3 Nacharbeiten | 4 (FAIL / FAIL / FAIL nur Pflicht 6 / **PASS**) | ~731–750 k / ~1,66 M (286+394+470+510 k) | ~4 h 40 gearbeitet, ~1 h 45 reine Rechenzeit / zwei Kalendertage | 4 Abstürze |
| G4-3 TSK-0123 | Opus | 1 + 3 Nacharbeiten | 3 (FAIL / **PASS** / **PASS**) | ~740 k / ~850 k (220+305+326 k) | ~4 h 10 / ~20 h | ~11 h |
| G4-4 TSK-0125 | Opus | 1 + 2 Nacharbeiten + Abschluss | 3 (FAIL / FAIL / **PASS**) | ~0,9–1,07 M (ausdrücklich Schätzung) / ~897 k (227+317+354 k) | ~4 h 40 / ~20 h | 3 Resumes von der Platte |
| **Merge TSK-0126** | Opus | 1 Bericht + 3 Nacharbeiten (R1: B1, B2, M1–M3, m1, m2 · R2: R2-B1, R2-B3, R2-B4, R2-M1–M3 · R3: R3-B1, R3-M1 + das Kernel-Kommando `migrate-holes`) | 3 abgeschlossen (**FAIL**, **FAIL**, **FAIL mit einem Befund**), kurze Runde 4 steht aus | Umsetzer: **keine Messung möglich** — der Prozess liest seinen eigenen Verbrauch nicht; lieber keine Zahl als eine erfundene. Prüfer: in den drei Prüfberichten | **04:4x → 20:00 = ~15 h 15**, davon ~10 h Suiten- und Rig-Läufe | keiner |

Rot-Messungen der Ströme: 54 (G4-1), 22 + 2 protokollierte untaugliche Mutationen (G4-2), 55
(G4-3), je Kriterium tabelliert (G4-4). Die Merge-Runde hat **9** eigene Rot-Messungen
(Abschnitt 5), davon eine an einem gepflanzten Importfehler in einer Kopie ausserhalb des Repos.

---

## 10. Befunde GEGEN DEN ZUSCHNITT — für die Rückschau-DEC, hier nicht behoben

| # | Was | Wer |
|---|---|---|
| Z1 | Die Zeile „gemessen unter 16 CPU-Brennern" in TSK-0124 stand vor vier harten Host-Abschaltungen (Kernel-Power 41). Der Neuschnitt zu TSK-0125 kam erst danach | Lead (Zuschnitt) |
| Z2 | Die AC-2-Zeile von TSK-0121 wiederholte einen Auftragssatz, den Generation 3 bereits gemessen widerlegt hatte und den `DEC-0070` als Orchestratorfehler führt — zum zweiten Mal | Lead (Zuschnitt) |
| Z3 | `team-kits/*/hooks/_kernel.py` stand in keiner Nahttabelle, obwohl G4-1 hineinschreibt (später als N-1 zurückgezogen, weil jedes andere Item die Datei verbietet) | Zuschnitt |
| Z4 | Die schreibenden Schritte des Merges (Migrationslauf, Push) darf keine Rolle INNERHALB der Sitzung fahren — der Auftrag verlangt sie trotzdem als Ergebnis | Auftrag |
| Z5 | Die Uhrzeit-Etiketten des Rundenlogs zwischen „00:5x" und „12:0x" waren extrapoliert, nicht gelesen; gemessen war 04:27 | Lead (Protokoll) |
| **Z6** | `forbidden_scope` von TSK-0126 nennt `user/**`, während sein eigenes `expected_outputs` (1) den Lauf `normalise_line_endings.py --apply` mit **52** Dateien verlangt. Der Mechanismus ist „der Normalisierer läuft über den GANZEN Checkout", nicht „eine Datei": ausserhalb von `allowed_scope` berührt er **zwei** — `user/claude/statusline.py` und `.gitignore` (die zweite fand die Prüfrunde 1, m2). Beide sind gemessen inhaltsgleich zu HEAD, `git diff` sieht keine von beiden. Der Widerspruch steht im selben Item | Auftrag |
| **Z7** | `expected_outputs` (2) zählt „hole items" als einen der vier Verfassungssätze von G4-2; übergeben hat der Strom stattdessen den Lease-/Arbeitsbaum-Satz, und kein Kit-Text behauptet über Löcher etwas, das diese Runde falsch gemacht hätte (Abschnitt 3b) | Auftrag |
| **Z8** | `expected_outputs` (5) verlangt den vollen Lauf **vor** dem Stempel. Ohne Stempel fallen ~25 Installer-/Scaffold-Tests mit „VERSION not bumped" — gemessen in dieser Runde (25 failed / 147 passed über vier Suiten). Die Reihenfolge muss Stempel → Lauf sein | Auftrag |
| **Z9** | Kein Stromitem hat die REICHWEITE eines Kernel-Vertrags über die Kits hinweg als Naht genannt. `H163` ist die Folge: G4-2 baut eine Pflicht in den geteilten Kernel, und das office-Kit steht ohne Ausweg in seinen eigenen Texten da | Zuschnitt |
| **Z10** | `DEC-0050` gibt einem Strom die lesenden Suiten. Beide neuen Kernel-Verweigerungen dieser Generation schlagen aber in Suiten zu, die kein Strom liest — 435 rote Knoten im ersten vollen Lauf. Ein Strom, der eine DISPATCH-Regel baut, müsste jede Suite fahren, die least, und das ist heute nichts, was der Zuschnitt sagt | Zuschnitt / DEC-0050 |

---

## 11. Die zwei Zeilen, die dem Nutzer gehören

1. **Der EINE schreibende Migrationslauf**, als **Kernel**-Zeile aus der Repo-Wurzel
   `C:\Offline Repos\AgentAndSkills` — der Lead kann sie in der Sitzung nehmen, der Nutzer braucht
   keine Shell (Abschnitt 12d, Abweichung vom Auftragstext, vom Lead entschieden):
   ```
   PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory migrate-holes --related-pr PR-0003 --apply
   ```
   Danach sind die sieben Richter in `.claude/hooks/test_gates.py` grün (gemessen an einer Kopie:
   7 passed). Ein zweiter Lauf schreibt nichts (gemessen, byte-gleich), und
   `… migrate-holes --reindex` ist die Zeile für ein Loch, das der Kernel später erfasst.
2. **Der Push** für die Nachher-Richtung von AC-1 aus G4-4 (der gehostete CI-Lauf ist der Beweis,
   und kein lokales Rig IST der Runner). Das Wort des Nutzers, wie immer.

### Die EVD-Zeile für den Lead

Der Lieferlauf, wie er zu erfassen ist — die Flaggen sind vom AUSGELIEFERTEN Parser abgelesen
(`kernel.cli`, `evidence`: `--kind --result --related --summary --artifact-ref` sind Pflicht,
`--run-scope --run-command` optional), nicht erinnert. Der Diff-Hash gehört dem Lead und steht
nicht hier.

**Der Verweis ist ZUSTANDS-RELATIV**, und das ist gemessen und nicht Geschmack: die erste Fassung
zeigte auf das Runden-Scratch, und eine Probe-EVD mit genau dieser Zeile macht
`tools/test_repo_hygiene.py::test_every_artifact_ref_still_resolves_where_it_points` rot — in einer
`.git`-losen Kopie ausserhalb des Repos gemessen (`probe_evd_ref.py`): Grundlinie 1 passed, mit dem
alten Verweis **1 failed**, mit dem neuen **1 passed**, nach dem Entfernen der Probe wieder
1 passed. Dazu kommt, dass das Scratch beim Rundenabschluss aufgeräumt wird. Die Protokolle liegen
darum neben diesem Dokument.

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory evidence \
    --kind test --result pass --related TSK-0126 \
    --summary "generation-4 merge, delivery run after rework 3 and the kernel migrate-holes command: pytest tools/ 4687 passed, 14 skipped, 0 failed in 46:24; ruff clean; validate.py green; stamp 2026.09.05-6 x3, --check unchanged" \
    --artifact-ref staging/TSK-0126/run-full-suite.txt \
    --run-scope full \
    --run-command "DELIVERY_RUN=TSK-0126 python -B -m pytest tools/ -q"
```

Zweiter Datensatz für die Haken-Suite, wenn der Lead sie getrennt führen will:

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory evidence \
    --kind test --result fail --related TSK-0126 \
    --summary "generation-4 merge: .claude/hooks/test_gates.py 7 failed / 541 passed -- the seven migrated hole judges, red until the ONE writing migration run of section 11 and green on a migrated copy (155 items, 7 passed); every other node green" \
    --artifact-ref staging/TSK-0126/run-gates-suite.txt \
    --run-scope full \
    --run-command "DELIVERY_RUN=TSK-0126 python -B -m pytest .claude/hooks/test_gates.py -q"
```

`--result fail` ist dort die Wahrheit, solange der schreibende Migrationslauf nicht gelaufen ist;
die sieben roten Knoten sind die migrierten Richter und sonst nichts. Die kurzen Kommandos
(`bump --check`, `validate.py`, `ruff` beidseitig) stehen mit ihrer ganzen Ausgabe in
`staging/TSK-0126/run-short-commands.md`.

Kein Commit und kein Push in dieser Runde. Der Lead erfasst die Evidenz und committet nach dem
PASS des Merge-Prüfers.

---

## 12. Nacharbeit nach Merge-Prüfrunde 1

### B1 — `DEC-0074`: die Architektenschritt-Pflicht wird aus dem Kit-Vertrag abgeleitet

Der Prüfer hat gemessen, was die erste Fassung falsch behauptet hat: **research trifft dieselbe
Sackgasse wie office**, sobald ein Auftrag nicht von einem `EXP` ableitet. Der Nutzer hat die Frage
am 2026-09-05 als Zwei-Kit-Frage beantwortet (`DEC-0074`, Variante A von dreien): ableiten, nicht
ausnehmen.

**Gebaut** in `team-kits/kernel/dispatch.py`: `_the_project_keeps_the_architect_step(state)` ist
die erste Frage in `architect_step_owed`. Sie liest den BESTAND des Projekts —
`os.path.isdir(state.root / ACTIVE_DIRS[ARCHITECT_STEP_TYPE])`, heute `system/active` — und von den
drei Vorlagen liefert nur `dev-team` dieses Verzeichnis. Kein Kit-Name, keine Flagge: ein Kit, das
den Typ bekommt, fällt unter die Pflicht, ohne dass hier eine Zeile geändert wird. Der Kommentar
nennt `DEC-0074` neben `DEC-0072` und sagt, was gelesen wird und warum es eine Eigenschaft ist.
Die andere Hälfte von `DEC-0074` ist die Regel, die schon da war: ein Ursprung, der die Kriterien
BRINGT, entschuldigt den Schritt (`_carries_its_own_criteria`).

**Rot zuerst, als Prozesse an Piloten aller drei Kits** (`_round-scratch/TSK-0126/redfirst_dec0074.py`;
ein Pilot ist die `templates/project_memory`-Vorlage des Kits, also das, was `init_project_memory`
kopiert; Log `redfirst-dec0074.log`):

| Fall | Heimat für `SR`? | ausgeliefert | Ableitung ENTFERNT |
|---|---|---|---|
| dev-team, Ursprung = Wurzel `PR` | **True** | **REFUSED** | REFUSED |
| office-team, Ursprung = Wurzel `PROC` | False | **not asked** | **REFUSED** |
| research-team, Ursprung = Wurzel `RQ` | False | **not asked** | **REFUSED** |
| research-team, Ursprung = `HYP` | False | **not asked** | **REFUSED** |
| research-team, Ursprung = `EXP` | False | not asked | not asked (die Kriterienregel) |

und nach dem Zurückbauen wieder der ausgelieferte Stand — die Mutation ist zurückgesetzt.

**In der Suite**: der `state`-Fixture von `tools/test_approvals_dispatch.py` ist jetzt
DEV-geformt (er legt die Heimat an) und sagt in seinem Docstring, warum — ohne sie modellierte er
ein Kit, das den Schritt nicht führt, und jeder Test dieser Datei über die Pflicht liefe über
nichts. Die Gegenrichtung hat einen eigenen Knoten,
`::test_a_project_with_no_home_for_the_architect_step_is_not_asked`, der BEIDE Richtungen an einem
Projekt misst. Gemessen: mit der Ableitung und ohne den Fixture-Zusatz war genau **ein** Knoten rot
(`test_a_goal_of_an_unknown_class_is_asked_for_the_architect_step`, 1 failed / 193 passed); nach
beiden Änderungen **195 passed**.

**Die zwei falschen Sätze** sind ersetzt: `H163` (Eintrag und Übersichtszeile) und Abschnitt 3a
dieses Protokolls sagen jetzt „office **und** research, für jeden Auftrag, dessen Ursprung die
Kriterien nicht selbst trägt" — und `H163` ist **geschlossen** mit seinem benannten Rest.

### B2 — der positionale Glob (`H165`)

`python -m pytest tools/test_*.py -q` war **rc 0**, während `tools/` 40 passende Dateien hält.
Gebaut: das Gate expandiert ein Wort mit Glob-Zeichen selbst und vergleicht die Treffermenge mit
den `members` der Erklärung. Vier Kopien (Repo + drei Kits, die Kits byte-gleich), `members` als
Daten in `tools/test_surface.json`, Tripwire am laufenden Läufer. Zahlen, Kette und die benannte
Über-Verweigerung stehen in `H165`; die Prozessmessung vorher/nachher ebenfalls dort.
Drei rote Mutationen in einer Kopie ausserhalb des Repos (`redfirst_b2.py`): Zweig entfernt
2 failed, `members` entfernt 2 failed, `members` verengt 1 failed; sauber und zurückgesetzt je
3 passed.

### M1 — der Zeigerleser liest die Fortsetzungsform

`tools/test_repo_hygiene._test_citations` verlangte einen Dateiteil, und die vier neuen
G4-2-Sätze schreiben ihre zweiten Zitate als `` `::test_x` ``. Der Leser trägt jetzt die zuletzt
genannte Suitendatei über den Absatz mit; eine Fortsetzung ohne vorangehende Dateinennung bleibt
ungelesen und sagt das. Rot zuerst, in einer Kopie ausserhalb des Repos (`redfirst_m1.py`), mit der
Mutation des Prüfers (`…through` → `…throughX` in der dev-Verfassung): sauber 2 passed → Mutation
**1 failed** → Leserzweig entfernt **1 failed** (der Boden) → zurückgesetzt 2 passed.
Der Boden `::test_the_test_pointer_reader_reads_the_shapes_a_kit_file_writes` trägt beide
Richtungen als Fälle.

### M2 — `H163` nennt die Tests, die wirklich rot werden

Die erste Fassung nannte zwei Tests, die grün bleiben, wenn man die Pflicht löscht (Prüfrunde 1:
`architect_step_owed -> False` ⇒ 2 failed / 192 passed, und die beiden Genannten waren unter den
grünen). `H163` nennt jetzt die beiden, die rot werden, plus den neuen Knoten dieser Nacharbeit.

### M3 — die drei Zahlen

Alle drei neu gemessen und im Dokument ersetzt statt ergänzt: die Naht-4-Zahl (**40/2**), der
Kit-Haken-Hash (steht nur noch an EINER Stelle, Abschnitt 8) und die Tabelle des schreibenden Laufs
(**155 / 155 / 192 003 B / `61988c1592b26a1a`**, Abschnitt 4).

---

## 12b. Nacharbeit nach Merge-Prüfrunde 2

Alle sechs Befunde der Runde 1 hat der Prüfer als behoben nachgemessen. Vier neue blockierende
Befunde, drei mittlere; einer der vier (R2-B2) ist ein Aufzeichnungsfehler des Leads und wurde von
ihm als **`DEC-0079`** korrigiert.

### R2-B1 / R2-B2 — die Ableitung hängt jetzt an der AUSLIEFERUNG des Kits (`DEC-0079`)

Der erste Bau las den BESTAND des Projekts (`os.path.isdir(state.root / system/active)`). Der
Prüfer hat gemessen, was das kostet: die **kit-eigene** CLI des office-Kits nimmt `capture SR` mit
rc 0 an und legt dabei `system/active` an — ab da war jeder Auftrag unter einem `PROC` wieder
verweigert, an der Lease **und** am Spawn. Ein `mkdir` tut dasselbe. Das ist die Sackgasse, die
`DEC-0074` schliessen sollte, wieder aufgestossen von einem Befehl des Kits selbst.

**Gebaut**: `_the_kit_ships_the_architect_step(state)` ersetzt den Bestandsleser. Gefragt werden
zwei Datensätze, die es schon gibt — der Scaffold-Datensatz des Projekts
(`presets.installation(repo)["kit"]`, aus `.claude/team_kit_roles.txt`) und der Kit-Store
(`presets.kit_dir(kit)`, `~/.claude/team-kits/<kit>`) —, und die Frage ist, ob die AUSGELIEFERTE
`templates/project_memory` des Kits das Verzeichnis `ACTIVE_DIRS[ARCHITECT_STEP_TYPE]` trägt. Kein
Kit-Name, kein Schalter, und nichts, was ein Projekt an sich selbst ändern kann. Fehlt der
Datensatz oder der Store, kann der Leser nichts sagen und **fragt** (fail-closed, `DEC-0079` (4)).

**Rot zuerst, als Prozesse, ein Interpreter je Fall** (`_round-scratch/TSK-0126/redfirst_dec0079.py`,
Log `redfirst-dec0079.log`; Pilot = die `templates/project_memory` des Kits plus die zwei Zeilen,
die der Scaffold in `.claude/team_kit_roles.txt` schreibt, Kit-Store als Kopie unter einem eigenen
HOME — der globale Store wurde nicht angefasst):

| Fall | ausgeliefert | Ableitung ENTFERNT |
|---|---|---|
| dev, Wurzel-Ursprung, Vorlage wie geliefert | **REFUSED** | REFUSED |
| dev, `system/active` im Projekt **gelöscht** | **REFUSED** | REFUSED |
| office, Wurzel-Ursprung, wie geliefert | **not asked** | REFUSED |
| office, nach `mkdir system/active` | **not asked** | REFUSED |
| office, nach einem echt erfassten `SR` | **not asked** | REFUSED |
| research, Wurzel-Ursprung | **not asked** | REFUSED |
| research, Ursprung `HYP` | **not asked** | REFUSED |
| research, Ursprung `EXP` | not asked | not asked (die Kriterienregel) |

Zurückgesetzt → wieder der ausgelieferte Stand. Die zweite Zeile ist der Befund, den `H163` als
Rest führte: er ist **weg**.

**In der Suite**: der `state`-Fixture legt kein `system/active` mehr an — mit `DEC-0079` entscheidet
das nichts, und die Zeile hätte dem nächsten Leser eine Regel beigebracht, die der Kernel nicht hat.
Was die Suite weiter fragen lässt, ist der fail-closed Zweig (kein Scaffold-Datensatz), und der
Fixture-Docstring sagt genau das. Zwei Knoten statt einem:
`::test_the_architect_step_is_owed_by_the_kits_delivery_not_the_projects_stock` (drei Fälle an
einem selbst gebauten Kit-Store, darunter das von Hand angelegte Verzeichnis) und
`::test_a_project_that_names_no_kit_is_asked_for_the_architect_step` (beide Hälften des
fail-closed Zweigs). Suite danach: **196 passed**.

**`capture SR` in office bleibt erlaubt, und das ist eine Entscheidung**, keine Auslassung:
`capture` ist kit-neutral, der Typenvorrat steht in EINEM geteilten Vertrag, und ihn pro Kit zu
beschneiden wäre die Kit-Namen-Aufzählung, die `DEC-0074` (C) und `DEC-0079` ausdrücklich verworfen
haben. Nach `DEC-0079` ist der Befehl auch harmlos: gemessen (Zeile „office, nach einem echt
erfassten `SR`") bleibt die Pflicht aus. Was bleibt, ist ein Item, das in diesem Kit niemand liest —
eine Frage für die Kit-Texte, nicht für den Dispatcher.

### R2-B4 — die zweite Shell-Expansion (Klammern)

`glob.has_magic` kennt `*?[` und nicht `{`. Der Leser führt jetzt **beide** Expansionen aus, die
eine Shell auf ein positionales Pfadwort anwendet: erst Klammer (`_brace_expanded`, rekursiv, Trenner
sind die Top-Level-Kommas, eine unpaarige `{` bleibt literal wie in der Shell), dann Pfadname. Und
jede Schreibweise bekommt die Frage, die zu ihr gehört — eine ohne Glob-Zeichen den gewöhnlichen
Leser, eine mit den `members`-Vergleich; das WORT deckt, wenn irgendeine Schreibweise deckt. Diese
zweite Hälfte war der eigene Zwischenfehler dieser Nacharbeit: mit dem Klammer-Leser allein war
`pytest {tools,docs} -q` rc 0, weil der `members`-Vergleich ein Verzeichnis nie als Deckung liest.
Gemessen und korrigiert, bevor die Runde weiterlief.

Prozessmessung, Zahlen und die zwei benannten Über-Verweigerungen stehen in `H165`; rot ohne den
Fix in einer Kopie ausserhalb des Repos (`redfirst_b2c.py`): Zweig entfernt **3 failed**,
Klammerhälfte entfernt **1 failed**, `members` entfernt **3 failed**, `members` verengt
**1 failed**, sauber und zurückgesetzt je **4 passed**.

### R2-B3 — die EVD-Zeile zeigte aus dem Repo hinaus

`--artifact-ref` auf `_round-scratch/…` macht
`tools/test_repo_hygiene.py::test_every_artifact_ref_still_resolves_where_it_points` rot (vom Prüfer mit einer Probe-EVD
gemessen), und das Runden-Scratch wird beim Rundenabschluss aufgeräumt. Die Laufprotokolle liegen
jetzt neben diesem Protokoll — der einen Stelle, in die diese Runde schreiben darf —, und die
EVD-Zeile in Abschnitt 11 nennt sie zustands-relativ.

### R2-M2 — der Kommentar sagt jetzt, wie weit der Leser trägt

`_test_citations` trägt die zuletzt genannte Suitendatei über die GANZE Datei, nicht über „dieselbe
Aussage". Der Kommentar sagt das, nennt die Kosten in beide Richtungen (meist Über-Verweigerung; ein
falsches Grün ist möglich, wenn die mitgetragene Datei denselben Namen definiert) und die Regel für
ausgelieferte Texte: die Fortsetzung steht neben dem Zitat, das sie fortsetzt.

### R2-M3 — `radar/decided.md`

`git diff --numstat HEAD -- radar/decided.md` = **9/0**. Inhalt und Zeitstempel weisen es als
Radar-Triage des **Leads** aus (eine der neun Zeilen kündigt die Prüfrunde an), nicht als
Schreibvorgang dieser Runde; ebenso die beiden untracked `radar/*.md`. Sie fahren im selben Commit
mit — der Lead entscheidet, ob sie hineingehören. Vom Merge geschrieben ist ausserhalb des
`allowed_scope` nichts ausser den zwei Zeilenenden-Reparaturen aus Z6.

---

## 12c. Nacharbeit nach Merge-Prüfrunde 3

Ein blockierender Befund, zwei Sätze gross; alle Befunde der Runde 2 hat der Prüfer als behoben
nachgemessen (die stärkste Einzelmessung: ein Rückbau auf den Runde-2-Bestandsleser macht die Suite
rot, 3 failed — der Defekt kann nicht still zurückkommen).

### R3-B1 — die fail-closed Verweigerung sagt jetzt, WARUM sie fragt

`DEC-0079` (4) versprach den Grund „stated in the remedy"; gemessen druckte der Code in **allen
drei** unlesbaren Fällen die gewöhnliche Verweigerung — also `capture SR` und „the architect", die
zwei Wörter, deretwegen `H163` überhaupt existiert. Und der Store-Pfad kommt aus
`presets.staging_root()`, dem **laufenden** HOME: eine zweite Maschine, ein anderes Konto, ein
CI-Runner genügt.

**Gebaut**: `_the_kit_delivery_of_the_architect_step(state)` gibt `(owed, why_it_could_not_be_read)`
zurück — ein Leser, zwei Aufrufer, eine Antwort. `architect_step_owed` nimmt die erste Hälfte, die
Verweigerung die zweite und wählt danach ihren Satz. Der fail-closed Satz nennt **welchen der drei
Fälle** (kein lesbarer Scaffold-Datensatz / das Kit liegt nicht im erreichbaren Store, mit Pfad /
die Vorlage fehlt dort), dass gefragt wird, weil die Auslieferung nicht gelesen werden konnte, dass
der Store der des laufenden Heimatverzeichnisses ist, und als Abhilfe „stelle Datensatz oder Store
wieder her" — plus ausdrücklich: **nicht** eine technische Anforderung erfassen, denn ob dieses Kit
den Typ überhaupt führt, ist genau das, was nicht gelesen werden konnte.

**Gemessen als Prozesse an gescaffoldeten Piloten** (`_round-scratch/TSK-0126/probe_r3b1.py`):

| Fall | Verdikt | Satz | `scripts/harness.py capture` im Text |
|---|---|---|---|
| office, Store unter HOME | not asked | — | — |
| office, Datensatz nennt ein Kit, das der Store nicht hat | REFUSED | **fail-closed** | **nein** |
| office, kein Scaffold-Datensatz | REFUSED | **fail-closed** | **nein** |
| office, Store **nicht** unter dem laufenden HOME | REFUSED | **fail-closed** | **nein** |
| dev, Store unter HOME | REFUSED | gewöhnlich | ja (richtig, die Pflicht selbst) |

**Rot zuerst** (`redfirst_r3b1.py`, `.git`-lose Kopie ausserhalb des Repos): sauber 3 passed →
fail-closed-Zweig aus der Verweigerung entfernt **1 failed / 2 passed** → der Grund für den
unerreichbaren Store auf `None` gesetzt **1 failed / 2 passed** → zurückgesetzt 3 passed.
**Eine untaugliche Mutation protokolliert**: der erste Versuch für (2) erzeugte einen SyntaxError
(rc 4, „1 error") und misst damit nichts; mit der gültigen Fassung wiederholt.

**In der Suite**: der neue Knoten
`::test_a_project_whose_kit_delivery_cannot_be_read_says_so` misst beide Sätze gegeneinander (zwei
unlesbare Projekte ohne die gewöhnliche Abhilfe, ein lesbares mit ihr).
`::test_a_goal_of_an_unknown_class_is_asked_for_the_architect_step` prüfte den Text der
gewöhnlichen Verweigerung, obwohl sein eigener Fixture-Baum seit `DEC-0079` der fail-closed Fall
ist — die Zusicherung nimmt jetzt beide Sätze und sagt im Kommentar, dass die MESSUNG die Frage ist
und nicht ihr Wortlaut. Suite: **197 passed**.

`H163`s Begrenzung sagt es jetzt genauso: auf einer Maschine, deren HOME den Kit-Store nicht trägt,
wird in einem Kit ohne `SR` **jeder** Auftrag verweigert und die Frage ist in den eigenen Kit-Texten
nicht beantwortbar — die Reparatur ist der Store, nicht der Dispatcher. „Eine Frage, die einen
Schritt kostet" war zu freundlich.

### R3-M1 — der Grund für eine Klammergruppe ohne Top-Level-Komma

Der Satz nannte sie „einen Bereich". Gemessen mit der echten Shell: Git Bash lässt
`tools/{test_*}.py` **literal** stehen (1 Positional), `{1..9}` expandiert wirklich (9). Beides
bleibt fail-closed und ist in `H165` benannt; der Satz sagt jetzt, dass der Leser zwischen den
beiden nicht entscheidet, statt eines von beiden zu behaupten. Docstring des Lesers ebenso.

### R3-M2 — `radar/decided.md`

Vom Prüfer als Notiz für die Abnahme geführt, nicht als offener Befund; steht in Abschnitt 8 und
in 12b als Änderung des **Leads**.

---

## 12d. Nachtrag zur Nacharbeit 3 — die Migration wird ein KERNEL-Kommando

**Anlass und Abweichung.** Der Nutzer ist entfernt und kann keine Shell ausserhalb von Claude Code
öffnen. Der Lead hat entschieden, dass die erwartete Ausgabe 2 (5) — „der schreibende Lauf wird dem
Lead als EINE exakte Kommandozeile übergeben" — damit eine **Kernel**-Zeile wird. Das ist eine
Abweichung vom Auftragstext („aus einer Shell ausserhalb von Claude Code") und steht hier und in der
Rückschau als solche.

**Gebaut.** `team-kits/kernel/holes.py` trägt die Migration (der Rumpf ist unverändert übernommen —
er importierte ohnehin nur aus `kernel.*`), `kernel/cli.py` bekommt `migrate-holes` mit
`--related-pr`, `--apply`, `--reindex`, `--doc`, `--holes-dir` und dem Vertrag in `--help`, und
`tools/migrate_holes.py` ist ein dünner Aufrufer, der dieselbe Tür ruft und jeden Namen
weiterexportiert, den die Suite von ihm liest. **Eine Tür, zwei Kommandozeilen.** Die vier Bolzen,
die Kollisionsverweigerung und die Idempotenz liegen unverändert in der Tür.

**Gemessen als Prozess gegen eine Kopie ausserhalb des Repos**
(`_round-scratch/TSK-0126/probe_migrate_holes_cli.py`, alles über
`python -B -m kernel.cli --root <Kopie> migrate-holes`):

| Lauf | Ergebnis |
|---|---|
| Probelauf | rc 0, **155 written, 0 prose files**, Dokument unverändert |
| `--apply` | rc 0, **155 Items, 155 Prosadateien**, 805 946 → **192 003 B**, sha **`61988c1592b26a1a`** |
| `--apply` erneut | rc 0, **0 written**, byte-gleich |
| `--reindex` | rc 0, „index rewritten from the store: 155 hole(s)", byte-gleich |
| `--apply` ohne `--related-pr` | **rc 2** mit eigenem Satz |
| Index / Prosa am Ende | **155 / 155** |

Das sind exakt die Zahlen der Tabelle in Abschnitt 4 — dieselbe Tür, dieselbe Wirkung.

**Rot zuerst** (`redfirst_cli_holes.py`, `.git`-lose Kopie): sauber 2 passed → CLI-Zweig entfernt
**2 failed** → die Tür in `kernel/state.py` umbenannt **2 failed** → die `--related-pr`-Wache
entfernt **1 failed / 1 passed** → zurückgesetzt 2 passed. Gehalten von
`tools/test_migrate_holes.py::test_the_kernel_command_migrates_the_holes_and_is_idempotent` und
`::test_the_kernel_command_asks_for_the_goal_unless_it_writes_no_item`.

**Zwei eigene Zwischenfehler, gemessen und behoben:** ein lokales `report = …` im CLI-Zweig
verdeckte das gleichnamige Modul (`UnboundLocalError` in `capture`, von der Suite sofort gefunden),
und die Suite las vier Namen vom Werkzeug, die beim Umzug mitgehen mussten.

**Der Stolperdraht auf der Kommandofläche hat ausgelöst**, was hier als Beleg gehört und nicht als
Ärgernis: `tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`
wurde in dem Moment rot, in dem das Kommando existierte, und nannte alle vier Texte, die die Fläche
aufzählen (drei Verfassungen + `README.md`). Sie nennen `migrate-holes` jetzt; Paket-Ratsche
(+17 B je Kit) und Abschnitts-Pins sind einmal nachgezogen.

### Was dabei gemessen wurde und der Erwartung widerspricht

Der Auftrag erwartete, dass Gate 1 die Kernel-Zeile durchlässt (**rc 0**) und die Werkzeug-Zeile
verweigert (**rc 2**). Gemessen — zweimal, als Prozess mit JSON auf stdin
(`probe_gate1_migrate.py`) **und** live in dieser Sitzung mit dem echten Haken, je als Probelauf,
der nichts schreibt:

| Zeile | Gate 1 als Prozess | live in dieser Sitzung |
|---|---|---|
| `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory migrate-holes …` | **rc 0** | **rc 0**, Lauf meldet „155 written, 0 prose files" |
| `python -B tools/migrate_holes.py --root project_memory --related-pr PR-0003` | **rc 0** | **rc 0**, gleiche Meldung |

**Beide Schreibweisen kommen durch.** Gate 1 verweigert einen Schreibzugriff auf `project_memory/`
nur dort, wo es die Zeile als schreibend LIEST; ein Interpreter mit einem Skript-Argument ist ihm
kein Schreibverb. Das ist die Klasse, die dieses Repo als **`H11`** führt („ein selbst geschriebenes
Skript prägt weiter"), und es heisst: der Satz aus G4-2s Protokoll §7 — „dieselbe Zeile aus einer
Sitzung heraus ist rc 2" — beschreibt nicht, was dieses Gate baut. Der schreibende Lauf war die
ganze Zeit von innen nehmbar; was ihn nach draussen verwies, war eine Behauptung und keine
Durchsetzung. Ich habe **keine neue Loch-Nummer** vergeben (die Runde hat H163–H165 und alle drei
sind belegt) — der Sachverhalt gehört zu `H11` und steht hier für die Rückschau. Am Gebauten ändert
er nichts: das Kernel-Kommando ist trotzdem die richtige Tür, weil es die einzige ist, die der
Kernel selbst führt.

---

## 13. Zeigertabelle (Ausgabe 7)

Jeder Zeiger, den der gemergte Baum schreibt, und was ihn hält:

| Zeigerklasse | Wo | Schiedsrichter | Stand |
|---|---|---|---|
| Testknoten `datei.py::name` in Kit-Texten | `team-kits/**/*.md` | `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` | grün; 49 Zitate, 0 unaufgelöst (Prüfermessung) |
| Testknoten in der FORTSETZUNGSform `::name` | dieselben Dateien | derselbe Test, seit M1 | grün, rot unter der Mutation des Prüfers |
| Testnamen in ausgeliefertem CODE | `team-kits/**/*.py` | `tools/test_migrate.py::test_every_test_the_shipped_code_cites_by_name_is_a_test_that_exists` | grün (M8 der Erstrunde korrigierte `test_surface`) |
| Testnamen in den Rollentexten | `.claude/agents/*.md` | `tools/test_review_procedure.py::test_every_test_pointer_the_harness_role_texts_write_resolves` | grün |
| Testnamen in `.claude/hooks/` | Docstrings der Gates | `.claude/hooks/test_gates.py::test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists` | grün |
| Testnamen in der Löcherliste | `docs/POST_V2_WISHLIST.md` | `.claude/hooks/test_gates.py::test_every_test_a_hole_names_is_one_that_exists` | rot bis zum schreibenden Migrationslauf, danach grün (an der Kopie gemessen) |
| `regression_tests` der migrierten Loch-Items | `project_memory/bugs/active/` | derselbe Richter | 179 Einträge, jeder löst auf genau einen Test auf (Prüfermessung) |
| Ankerzeiger der Paritätsmatrix | `docs/reviews/phase0-disposition.md` | `tools/test_parity_sources.py::test_every_pointer_resolves_to_a_location_its_file_declares` | grün, seit M10 der Erstrunde eindeutig |
| Abschnittspins | `tools/constitution_section_pins.json` | `tools/test_shortening_net.py` | grün, einmal neu geschrieben |
| `DEC`/`H`-Nummern in Code und Prosa | überall | `.claude/hooks/test_gates.py::test_every_reference_to_a_measurement_leads_to_one` | rot bis zum Migrationslauf (dieselben sieben), danach grün |

---

## 14. Urteil je Produktziel (die Zeilen, die in die Abnahme gehören)

| Ziel | AC | Stand nach dieser Runde |
|---|---|---|
| **PR-0004** | AC-1 Gate 5 | **erfüllt**, als Prozess gemessen; beide Expansionen, die eine Shell auf ein positionales Pfadwort anwendet, sind geschlossen (Glob in Prüfrunde 1, Klammer in Prüfrunde 2), `H165` trägt die zwei benannten Über-Verweigerungen (Bereich `{1..9}`, quotierter Glob) |
| | AC-2 Fristen | **ABWEICHUNG, vom Lead angenommen** — wörtlich verlangt AC-2 „ein ausgelieferter Test wird rot, wenn ein Haken-Eintrag keine Frist nennt"; gemessen nennen dev 1/31, **office 0/30**, research 1/28 Kit-Einträge eine Frist, und `_kernel.start_the_deadline` verweigert einen Eintrag ohne Fenster nicht. Gebaut ist stattdessen die Eigenschaft „ein Eintrag nennt ein Fenster genau dann, wenn sein Gate das Standardfenster überleben kann". Das ist eine Abweichung, keine Erfüllung. **Auch auf der Codex-Seite**, vom Prüfer an der ERZEUGTEN `.codex/hooks.json` eines frischen dev-Piloten gemessen: Gate 5 ist dort registriert (`PreToolUse`, Matcher `Bash`, über `_gate.py`) und trägt keine Frist — wie 25 der 26 Überlagerungseinträge; die einzige Frist hat `gate_pipeline` (1800), genau wie auf der Claude-Seite. Die Überlagerung erfindet also keine Frist und verschluckt keine, und dieselbe Abweichung gilt für Codex mit |
| | AC-3 Design-Checks | in dieser Runde **nicht gemessen** (kein dev-Pilot mit gebauter App); der Strom hat sie gemessen |
| | AC-4 Kostenseite | erfüllt — die Schwelle ist Daten (`tools/test_surface.json`), im Gate-Kopf begründet |
| **PR-0005** | AC-1..AC-5 | erfüllt im gemergten Baum. Die Reichweite, die AC-3 (`FR-0085`) über die Kits hinweg offenliess, ist mit **`DEC-0074`** entschieden (aus dem Kit ableiten, nicht nach Namen ausnehmen) und mit **`DEC-0079`** präzisiert: gelesen wird die AUSLIEFERUNG des Kits, nicht der Bestand des Projekts — ein `mkdir` oder ein `capture SR` schaltet die Pflicht nicht mehr ein, gemessen an Piloten aller drei Kits (Abschnitt 12b) |
| **PR-0006** | AC-1..AC-4 | erfüllt; `H158` bleibt offen und ist gemessen bestätigt (Abschnitt 6) |
| **PR-0007** | AC-1 CI | **OFFEN** — die Nachher-Richtung ist der nächste gehostete Lauf, und der braucht den **Push**. Kein lokales Rig ist der Runner; in dieser Runde nicht entscheidbar |
| | AC-2 Zeilenenden | erfüllt: 52 normalisiert, alle byte-gleich zu HEAD, 0 CR ausser dem einen unerreichbaren Auditlog |
| | AC-3 Kit-Update | erfüllt |
| | AC-4 Zeitmesstest | erfüllt für die gemessene Lastklasse, Rest in `H162` |
