# TSK-0125 — Strom G4-4 „Repo hygiene" (PR-0007, AC-1..AC-4)

Umsetzer: `harness-implementer` (Opus). Arbeitsbaum: `C:\Offline Repos\v2-testbed\_worktrees\g4-hygiene`,
Branch `g4/hygiene`, Basis `75a00d1`. Rundenverzeichnis außerhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0125\`.

Nachfolger von **TSK-0124** (für den Neuschnitt storniert). Worktree, Patch und Protokoll sind unter
der neuen Id übernommen; die Arbeit selbst ist dieselbe.

Kein Commit, kein Push, keine Installation. Der Stempel ist **vorläufig** (Abschnitt 8).

**Der verworfene Weg dieses Plans, in einer Zeile (FR-0084-Form):** die CRLF-Prüfung in
`tools/validate.py` einbauen statt in die Testsuite — verworfen, weil `install.sh` `validate.py`
**vor** der Installation fährt und bei rot `exit 1` macht: ein Nutzer mit einem CRLF-Arbeitsbaum
hätte dann gar keinen Haken mehr installiert bekommen, und genau das ist der Schaden von BUG-0025.

---

## 0. Vorgefunden (gemessen, nicht erinnert)

Diese Runde wurde **dreimal** durch harte Abschaltungen des Hosts unterbrochen und jedes Mal aus
dem Plattenstand fortgesetzt. Stand bei der letzten Fortsetzung:

```
git -C _worktrees/g4-hygiene rev-parse HEAD    -> 75a00d1
git status --short                             -> 10 M, 2 A (die zwei neuen Dateien, `git add -N`)
git ls-files --eol | grep -c 'w/crlf|w/mixed'  -> 0   (der Worktree ist LF)
_round-scratch/TSK-0125/                       -> Rigs + Messberichte vollständig erhalten
_round-scratch/TSK-0125/load-gate3-fixed.txt   -> NUR der Kopf: der Lauf startete 23:12:39 und der
                                                  Host schaltete um 23:14 ab -- kein Messwert
project_memory/staging/TSK-0125/               -> Protokoll übernommen
```

Ausgangsmessungen im **Haupt-Checkout** (`C:\Offline Repos\AgentAndSkills`, nur gelesen), Rigs
`_round-scratch/TSK-0125/measure_bytes.py` und `measure_exts.py` (beide verweigern den Lauf
außerhalb ihres eigenen Verzeichnisses und schreiben ihren Bericht **binär**):

| Größe | Zahl |
|---|---|
| verfolgte Dateien auf der Platte | 1794 |
| binär **nach Bytes** (NUL in den ersten 8000) | 516 |
| davon mit `\r\n`-Bytepaaren im Inhalt | **499** |
| von git selbst als binär gelesen (`w/-text`) | 516 |
| Dateien, bei denen NUL-Scan und `git ls-files --eol` **abweichen** | **0** |
| verfolgte Textdateien mit CRLF im Arbeitsbaum | **53** (33 außerhalb `project_memory/`, 19 unter `staging/`, 1 kanonisch) |
| Binärarten nach Endung | `.png` 496, `.woff2` 20 |

Git-Konfiguration, die BUG-0025 verursacht:

```
git config --get core.autocrlf            -> true    (lokal)
git config --system --get core.autocrlf   -> true    (Host)
git config --global --get core.autocrlf   -> nicht gesetzt
```

Gehostete CI, vorgefunden: die drei Läufe vom 08-31 waren **grün**, die drei danach (09-02, 09-02,
09-03) **rot**. Der Lauf auf **meinem Basis-Commit** `75a00d1` (`33835146802`) war ebenfalls rot,
mit **je Plattform genau EINEM** Fehlschlag — die ~100 ERRORs, mit denen BUG-0069 aufgenommen
wurde, sind seit Generation 3 weg.

---

## 1. Nahttabelle

| Naht | Wer sonst | Empfangen | Erwartet am Merge |
|---|---|---|---|
| `.claude/hooks/test_gates.py` | G4-1, G4-2 | `75a00d1` | **EIN** geänderter Test: `test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`. Sonst keine Zeile. Der Schwestertest `test_gate1_answers_before_its_registration_however_long_the_line_takes_to_read` trägt dieselbe Klasse und ist **absichtlich unberührt** (`H161`) |
| `tools/**` | alle Ströme | `75a00d1` | vier geänderte Dateien: `test_repo_hygiene.py` (+3 Tests), `test_kitupdate.py` (+4 Tests, +2 Helfer), `test_office_duties.py` (1 Test + 1 Helfer), `test_reference_skills.py` (`_route_mentions` + 1 Zusicherung); **neu** `tools/normalise_line_endings.py` |
| `docs/**` | alle Ströme | `75a00d1` | **neu** `docs/line-endings.md`; `docs/POST_V2_WISHLIST.md` nur `H160`–`H162` (drei Tabellenzeilen nach `H150`, drei Abschnitte am Dateiende) |
| `team-kits/*/VERSION` | alle Ströme | `2026.09.04-1 / -3 / -1` | **vorläufig** `-2 / -4 / -2`. Der Patch trägt **keine** VERSION-Hunks; der Merge stempelt einmal neu |
| `team-kits/kernel/kitupdate.py` | **niemand** | `75a00d1` | gehört diesem Strom **allein** und ist **G4-2 (Kernel-Verträge) verboten** |
| `team-kits/kernel/cli.py` | G4-2 | nur gelesen | **nicht geändert.** Aber: der Satz aus AC-3 reist im Schlüssel `pending_templates`, den `cli.py` im Zweig `update-kit` druckt. Wird er dort umbenannt, wird `tools/test_kitupdate.py::test_the_update_report_names_a_memory_tree_no_installed_role_declares` rot — die Naht ist gemessen statt vereinbart |
| `.github/workflows/ci.yml` | niemand | `75a00d1` | **nicht geändert** — die beiden Roten waren Testfehler, keine Workflow-Fehler |
| Verfassungssatz | — | — | keiner erwartet, keiner geschrieben |

---

## 2. AC-1 (BUG-0069) — die gehostete CI

**Abnahmezeile:** die beiden Roten des gehosteten Laufs **auf meinem Basis-Commit** sind lokal
reproduziert, behoben und auf **beiden** Plattformen grün nachgemessen; keiner von beiden war ein
Fehler, den die lokale Suite nicht reproduzieren kann — sie waren es nur auf dem jeweils **anderen**
Betriebssystem, und genau dafür sind die zwei Rigs gebaut.

Lauf `33835146802` (Push `75a00d1`, 2026-09-04):

| Plattform | Ergebnis | Test | Klasse |
|---|---|---|---|
| ubuntu-latest | `1 failed, 4465 passed, 105 skipped` (19:01) | `tools/test_office_duties.py::test_a_filing_plan_that_resolves_to_the_project_ROOT_is_not_walked` | E1 — host-abhängige Erwartung in host-unabhängiger Tabelle |
| windows-latest | `1 failed, 4500 passed, 70 skipped` (42:21) | `tools/test_reference_skills.py:236` in `_route_mentions` → `ValueError: path is on mount 'C:', start on mount 'D:'` | B — zwei Laufwerke |

Beide standen identisch schon im Lauf `33717432166` (Push `46eaaf2`).

**Ursachen, gemessen:**

* `....//<year>/` fällt **nur auf Windows** auf die Wurzel zusammen: dort werden Punkte am Ende
  einer Pfadkomponente verworfen, bevor der Aufruf das Dateisystem erreicht. Sonde
  `_round-scratch/TSK-0125/probe_dots.py`, beide Hosts:

  | Host | `abspath(base+'/....')` | `makedirs` + `samefile` | `listdir(base)` |
  |---|---|---|---|
  | Windows | `base` (mit Trennzeichen) | **True** | `[]` |
  | Linux | `base/....` | **False** | `['....']` |

  Auf POSIX benennt `....` also ein **echtes** Unterverzeichnis, und die Verweigerung als „die
  Wurzel" wäre ein Übergriff des Wächters.
* `_route_mentions` benannte Treffer mit `os.path.relpath(path, ROOT)`. Auf dem gehosteten
  Windows-Runner liegt der Workspace auf `D:` und `tmp_path` auf `C:`.

**Die Fixes:**

* `tools/test_office_duties.py`: neuer Helfer `_the_filesystem_puts_this_on_the_root(root, prefix)`
  fragt das **Dateisystem** (`os.makedirs` + `os.path.samefile`) und **nicht** `os.path.abspath` —
  letzteres ist genau das Primitiv, mit dem `_duties._same_place` antwortet, eine daraus abgeleitete
  Erwartung wäre mit dem Prüfling per Konstruktion einig und keine Mutation des Wächters könnte rot
  werden. **Beide** Antworten sind jetzt Zusicherungen: eine Schreibweise, die auf der Wurzel landet,
  muss verweigert werden; eine, die es nicht tut, muss auflösen.
* `tools/test_reference_skills.py`: `_route_mentions` benennt Treffer relativ zum **Kit**, unter dem
  sie gefunden wurden — ein Start, der per Konstruktion ausdrückbar ist (der Glob beginnt dort).
  Dieselbe Entscheidung, die Generation 3 für `_pinned_files` getroffen hat.

**Rot ohne den Fix (Rigs außerhalb des Repos, Kopien ohne `.git`):**

| Rig | Vorher | Nachher |
|---|---|---|
| POSIX (WSL Ubuntu 24.04, CPython 3.12.3, Windows-`pytest` über `PYTHONPATH`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`), `rig-base` | `AssertionError: '....//<year>/' was placed at the project root`, `tools/test_office_duties.py:669` — Zeile für Zeile der ubuntu-Fehlschlag | `54 passed, 1 skipped` (150,2 s) |
| Cross-Mount auf einem Ein-Laufwerk-Host über einen echten zweiten Mount (`--basetemp=//localhost/C$/…`) | `ValueError: path is on mount '\\localhost\C$', start on mount 'C:'` | `1 passed` |
| Windows, dieselben zwei Suiten | — | `55 passed` (187,9 s), Nachlauf `55 passed` (69,4 s) |

Der Cross-Mount-Fix ist zusätzlich **auf jedem Host** rot-fähig gemacht: der Bodentest sichert jetzt
die **Namen** zu (`{"alpha": ["agents/one.md"], "ghost": ["agents/two.md"]}`) und nicht nur die
Schlüssel — mit dem alten Leser kommt dort ein Aufstieg aus dem Repo heraus, also ungleich.

**Nicht geschlossen, benannt:** der eigentliche Beweis ist der **nächste Push**. Kein lokales Rig
**ist** der gehostete Runner (WSL fährt CPython 3.12 statt der Runner-Version; für den
Windows-Runner mit Workspace auf `D:` gibt es hier nur den UNC-Ersatz). Der Lead pusht auf
Nutzerwort; erst der Lauf danach ist AC-1s „gemessen an einem echten Lauf" in der Nachher-Richtung.

---

## 3. AC-2 (BUG-0025) — Zeilenenden

**Abnahmezeile:** `.gitattributes` pinnt jede Textklasse als **Ableitung** (`* text=auto eol=lf`),
eine ausgelieferte Prüfung verweigert eine verfolgte Textdatei mit CRLF **und nennt sie**, das
Werkzeug für die einmalige Normalisierung entscheidet binär **nach Bytes** und hat Byte-Gleichheit
gegen `HEAD` als Vorbedingung, und `core.autocrlf` steht als Ursache in `docs/line-endings.md` mit
dem Satz, dass dieses Repo sie nicht repariert.

**Gebaut:**

* `.gitattributes`: die Behauptung „The one binary kind in the tree" war **falsch** — 496 `.png`
  standen neben 20 `.woff2`. Ein Kommentar, der Schutz behauptet, den der Baum nicht trägt. Ersetzt
  durch die Messung plus `*.png binary`; weil das eine **Aufzählung** ist, hängt ein Stolperdraht
  daran, der **beide** Enden misst.
* `tools/test_repo_hygiene.py::test_no_tracked_text_file_checks_out_with_crlf` — Subjekt ist
  `git ls-files --eol`, also gits eigene Auflösung; „binär" ist dort die NUL-Heuristik von
  `text=auto` (gemessen: 0 Abweichungen gegen einen NUL-Scan über 1794 Dateien). Ausgenommen ist
  allein der **kanonische** Teil von `project_memory/` — dorthin reicht kein Werkzeugschreibzugriff
  (Gate 1) —, und **was ausgenommen wird, wird gemeldet** (`warnings.warn`, dieselbe fail-open-Form
  wie `_report_stale` eine Sektion tiefer).
* `tools/test_repo_hygiene.py::test_the_line_ending_sweep_excuses_canonical_state_and_nothing_else`
  — Boden unter `_repairable`, ausdrücklich **keine** Behauptung, die Ausnahme werde noch gebraucht:
  ob gerade eine kanonische Datei CRLF trägt, hängt vom Checkout ab (frischer Klon: keine, dieser
  Entwicklerhost: eine).
* `tools/test_repo_hygiene.py::test_every_binary_pin_names_a_kind_the_tree_has_and_every_kind_is_pinned`
  — die **Wirkung** wird `git check-attr --stdin binary` gefragt (die Auflösung, die der Checkout
  fährt); aus der Datei gelesen wird nur, **welche** Muster zu halten sind. Dieselbe Teilung, die
  `tools/test_ci_lint_pinned.py` zwischen „`ruff.toml` parsen" und „ruff laufen lassen" macht.
* `tools/normalise_line_endings.py` — Trockenlauf als Standard, `--apply` schreibt. Vorbedingung je
  Datei: die CRLF-normalisierten Bytes müssen dem Blob in `HEAD` **byteweise** gleichen; sonst
  Verweigerung **mit Namen und Grund**.
* `docs/line-endings.md` — Ursache, Wirkungskette bis `install.sh`, die Byte-Entscheidung, und der
  Satz, dass dieses Repo die Git-Konfiguration des Nutzers nicht anfasst.

**Gemessen** (Rig: frischer `git clone` des Worktrees nach `_round-scratch/TSK-0125/clone-eol`, also
außerhalb des Repos, mit eigenem `HEAD`):

| Messung | Ergebnis |
|---|---|
| frischer Klon auf einem Host mit `core.autocrlf=true` | **0** CRLF-Dateien — `eol=lf` schlägt `autocrlf`, gemessen statt angenommen |
| `plant_crlf.py --clean docs/office-kit-from-field.md` (nur CRLF) + `--edited docs/backlog-structure-and-dedup.md` (CRLF **und** eine zusätzliche Zeile) | Prüfung **rot**, nennt beide Dateien |
| `normalise_line_endings.py` (Trockenlauf) | 1 würde normalisiert; 1 **REFUSED**: „normalised it is 5534 bytes and HEAD holds 5510 — it carries a real uncommitted change" |
| `--apply` | die saubere Datei repariert, `git status` für sie **leer** (byte-identisch zu `HEAD`), `git ls-files --eol` → `w/lf`; die bearbeitete Datei unangetastet auf `w/crlf` |
| `*.png binary` entfernt | **rot**: 496 Dateien, die git nach Bytes als binär liest, deckt kein Pin |
| `*.zzz binary` hinzugefügt | **rot**: ein Pin, der nichts trifft |

**Rot ohne den Fix:** die drei genannten `tools/test_repo_hygiene.py`-Knoten, im Klon außerhalb des
Repos, Defekt eingesetzt, rot gesehen, zurückgesetzt.

**Merge-Zeile — der Schritt, den diese Runde VORBEREITET und nicht ausführt:**

> Im Haupt-Checkout `C:\Offline Repos\AgentAndSkills` vor dem Commit einmal
> `python tools/normalise_line_endings.py` fahren (lesen, was es sagt), dann `--apply`.
> Erwartung nach der Messung vom 2026-09-04: **52** Dateien werden normalisiert (33 außerhalb
> `project_memory/`, 19 unter `project_memory/staging/`), **eine** wird gar nicht erst angeboten —
> `project_memory/.audit/hook_events.jsonl`. Seit der Nacharbeit ist das keine Behauptung mehr,
> sondern gebaut: `drifted_files()` teilt die driftenden Pfade mit **demselben** Prädikat
> (`normalise_line_endings.repairable`), mit dem die Prüfung sie ausnimmt, und listet die
> unerreichbaren getrennt auf. Vorher hielt diese Datei nur die Byte-Vorbedingung auf, weil sie
> zufällig auch inhaltlich abwich — ein Schutz, den das Protokoll behauptete und das Werkzeug nicht
> baute (Prüfbefund F3). Jede Datei, die die Byte-Gleichheit gegen `HEAD` nicht besteht, wird vom
> Werkzeug benannt und ist **von Hand** zu entscheiden, nicht durchzuwinken; trägt der Blob in
> `HEAD` selbst CRLF, nennt es diesen Grund und schickt zu `git add --renormalize` statt eine
> Änderung zu behaupten, die `git status` nicht kennt (F2).
>
> **Bis dieser Schritt gelaufen ist, ist `test_no_tracked_text_file_checks_out_with_crlf` im
> Haupt-Checkout ROT** — das ist der Zweck der Prüfung und keine Überraschung, und es ist der Grund,
> warum sie in der Suite steht und nicht in `validate.py` (siehe den verworfenen Weg oben).

---

## 4. AC-3 (BUG-0088) — Rollengedächtnis nach einem Kit-Update

**Abnahmezeile:** `update-kit` **listet** dem Nutzer jeden Gedächtnisbaum, den keine installierte
Rolle mehr deklariert, mit Pfad, Dateizahl und Grund — am echten Piloten gemessen, rot zuerst.
Entfernt wird nichts; warum, steht als Satz im Code und als `H160` in der Löcherliste.

**Gebaut** (`team-kits/kernel/kitupdate.py`, meine einzige Kernel-Datei):

* `MEMORY_DIR` / `MEMORY_KEY` — der eine Name, den der Kernel dem Kit nicht abnehmen kann: die Kits
  liefern `guard_memory_budget.py` **neben** dem Kernel aus, nicht darunter, und die Projektkopie
  davon ist genau das, was ein Update ersetzt.
* `memory_residue(root)` — **Eigenschaft, keine Rollenliste**: ein Verzeichnis unter
  `.claude/agent-memory/` ist Rest, wenn die **jetzt installierte** Rollendefinition kein `memory:`
  deklariert — weil keine Definition dieses Namens mehr installiert ist, oder weil aus der
  vorhandenen keine gelesen werden konnte. Dritte Antwort `read: False` für einen Baum, der
  **existiert** und nicht gelistet werden konnte (`pending_entries`' Grund eine Etage höher); ein
  **abwesender** Baum ist `read: True` mit leerer Liste und ist nicht dieselbe Antwort.
* `_memory_residue_note(root)` — der Satz, und der Grund, warum er nur ein Satz ist.
* `_follow_up(root)` — führt ihn mit `_pending_templates` zusammen und reist im Schlüssel
  `pending_templates`, weil `kernel/cli.py` ihn druckt und diese Datei mir nicht gehört (Naht).

**Warum gelistet und nicht entfernt** (der Satz, den der Code trägt, und `H160`): ob ein Provider
einen vorhandenen Baum für eine Rolle **ohne** den Schlüssel noch lädt, ist **nicht gemessen**
(BUG-0088 AC-2) — ein Entfernen wäre ein unumkehrbarer Schritt auf einer ungemessenen Prämisse,
genau die Richtung, für die `DEC-0056 (c)` die Sorgfalt reserviert; der Inhalt ist das
Handwerkswissen des Nutzers; und die einzige wiederherstellbare Quarantäne ist der Schnappschuss
unter `.claude/backups/`, dessen `RESTORE_SET` die beiden `scaffold_team`-Zwillinge schreiben — die
dieser Strom nicht anfassen darf. Ein dorthin verschobener Baum stünde **außerhalb** dieser Menge
und käme bei einem Rollback nicht zurück.

**Tests** (`tools/test_kitupdate.py`):

* `test_the_memory_directory_this_command_reads_is_the_one_the_kit_hook_polices` — importiert
  `guard_memory_budget` je Kit als **Modul** und vergleicht `MEMORY_DIR` mit dem des Kernels.
* `test_a_memory_tree_is_residue_exactly_where_no_installed_role_declares_the_key` — alle vier
  Formen inklusive Gegenende: eine Rolle, die `memory:` **noch** deklariert, bleibt still.
* `test_a_memory_tree_that_cannot_be_listed_is_never_reported_as_nothing` — `read: False`.
* `test_the_update_report_names_a_memory_tree_no_installed_role_declares` — **der Pilot**: dieses
  Repos Kits in ein Schein-Heimatverzeichnis gestellt, echtes PowerShell-`scaffold_team`, echter
  Freigabe-Haken, echter Einstiegspunkt, `update-kit` als Prozess; gelesen wird die **Ausgabe**,
  also die ganze Kette einschließlich `cli.py`.

**Rot ohne den Fix** (Rig `_round-scratch/TSK-0125/rig-ac3`, Kopie **ohne** `.git`, Defekt
zurückgesetzt auf `"pending_templates": _pending_templates(root)`, neu gestempelt, Pilot gefahren):

```
AssertionError: the update left a memory tree no installed role declares and told nobody:
  dev-team kit: 2026.07.01-1 -> 2026.09.04-3
  installed: stamp 2026.09.04-3, and the enforcement bundle on disk is the STAGED kit's
  NOT re-read: ...
  RESTART REQUIRED: ...
```

Mit dem Fix `1 passed` (13,9 s); danach liegen **beide** gepflanzten Bäume noch da —
`quality-engineer` gemeldet, `backend-developer` nicht —, und die Prüfung hält beides fest.

---

## 5. AC-4 (BUG-0033) — der Zeitmess-Test von Gate 3

**Abnahmezeile, beide Hälften gemessen.** Solo grün nach dem Fix (vorher solo **rot**), und unter
der Lastklasse, die dieser Host verträgt, ebenfalls grün:

| Lauf | Ergebnis |
|---|---|
| solo, an `75a00d1`, **ohne** den Fix | `assert 4.622 < 4.5` → **FAILED** (der Prüfer unabhängig: 4,66 s) |
| solo, mit dem Fix | `1 passed` — 17,6 s / 18,9 s / 20,1 s Wanduhr in drei Läufen |
| **unter Last** (8 von 16 Brennern, unter-normal, Deckel 120 s), 2026-09-05 04:28 | `1 passed in 16.31s`; der Host war **20,1 s** belegt, danach kein Brenner übrig |

Der Knoten hat unter Last den neuen Zweig also **nicht gebraucht**: `elapsed` blieb unter der
Registrierung, es gab weder Skip noch Fail. Was das **nicht** zeigt, steht in `H162` — die
16-Brenner-Klasse mit Normalpriorität wird auf diesem Host nicht wieder gefahren, und der Skip-Zweig
hat hier noch nie gefeuert (der Fail-Zweig ist vom Prüfer durch Abschalten des Budget-Wächters
gemessen).

**Solo-Hälfte im Einzelnen:** der Knoten misst gegen ein Budget, das aus der
**registrierten** Frist abgeleitet ist; die gestoppte Größe ist jetzt die, die ihr Name sagt; und wo
die Startkosten des Hosts die Reserve auffressen, ist das Ergebnis ein **Skip mit den Zahlen** statt
eines Rots — „host too noisy" und „gate too slow" sind unterscheidbare Ausgänge (BUG-0033 AC-2).
**Last-Hälfte: nicht gemessen**, siehe Abschnitt 5a.

**Der Befund, und er ist größer als „flattert unter Last":** der Knoten war auf diesem Host
**solo rot**, an `75a00d1`, unverändert:

```
_round-scratch/TSK-0125/rig-base (Kopie ohne .git):  assert 4.622 < 4.5   -> FAILED
Arbeitsbaum, vor der Änderung:                       assert 4.54  < 4.5   -> FAILED
```

Ursache, gemessen statt vermutet: `_a_git_line_too_costly_to_judge_in(seconds)` stand **innerhalb**
der gestoppten Spanne. Diese Funktion liest 1500 Aufrufungen durch den echten Leser, um die Zeile zu
dimensionieren — Arbeit, die **kein** Gate-Prozess je tut, die dem Gate aber auf seine Frist
geschrieben wurde.

| Sonde (`_round-scratch/TSK-0125/`) | Ergebnis |
|---|---|
| `probe_sizing.py`, 5 Läufe | Gate-3-Dimensionierung **1,03–1,19 s**; die Schwester bei Gate 1 **0,03–0,04 s** |
| `probe_gate3.py`, 4 Läufe, Zeile **außerhalb** der Spanne gebaut | `elapsed` **3,26–3,31 s** gegen eine Registrierung von 4,50 s, jedes Mal `rc 2` mit „registration allows" |
| dieselbe Größe **innerhalb** der Spanne (der alte Stand) | 4,54–4,62 s → rot |
| Startkosten des Hosts | `bare` 0,32 s, Rauschen 0,13 s, Reserve 1,50 s |

**Geändert wurde genau EIN Test**
(`.claude/hooks/test_gates.py::test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`):

1. die Zeile wird **vor** dem Start der Uhr gebaut — die Größe bewegt sich, nicht die Marge. Eine
   Größe, die nicht das ist, was ihr Name sagt, wird von einer breiteren Marge nicht ehrlich;
2. auf einem Überlauf werden die Sichtkosten des Hosts **in diesem Moment** gemessen
   (`_cost_of_a_gate_that_answers_at_once`, derselbe Boden, den der Gate-1-Schwestertest benutzt).
   Frisst `bare + noise` die Reserve, ist das Ergebnis ein `pytest.skip` mit allen Zahlen; sonst ein
   `pytest.fail`, das sagt, dass der Überlauf dem Gate gehört und nicht der Maschine.

Keine Zahl steht getippt da: `seconds` und `reserve` kommen aus der Registrierung und aus
`_harness._SPENDABLE_SHARE` / `_RESERVE_FLOOR`.

**Solo nach dem Fix:** `1 passed` (17,6 s bzw. 18,9 s in zwei Läufen).

### 5a. Die Last-Hälfte: **gemessen** am 2026-09-05 im Fenster des Leads (`H162`)

Ein Lauf, wie im Auftrag beschrieben, und danach vom mir geschlossenes Fenster:

```
Fenster:      LOAD_WINDOW_OPEN, 04:27:18 vom Lead angelegt ("nothing else runs")
Host vorher:  4 python.exe, keine LOAD_BURNER_PIDS
Lauf:         == gate3-under-load | 8 burners of 16 CPUs, below normal | cap 120s incl. 2s warm-up
              1 passed in 16.31s
              == completed | host held 20.1s | rc 0 | ended 04:28:20
Host nachher: 4 python.exe, keine LOAD_BURNER_PIDS, LOAD_WINDOW_OPEN von mir gelöscht
```

Der Knoten ist unter dieser Lastklasse **grün**. Der Rest ist in `H162` benannt: die 16-Brenner-Klasse
mit Normalpriorität ist damit **nicht** gemessen und wird auf diesem Host nicht wieder gefahren, und
der Skip-Zweig hat hier noch nie gefeuert.

**Wie das Rig gebaut ist, unverändert seit der ersten Nacharbeit:**

Der Host hatte am 2026-09-04 **vier harte Abschaltungen** (Windows Kernel-Power 41 um 17:38, 22:58,
23:06, 23:14, gemessen in `staging/generation-4-streams.md`). Zwei davon folgten einem Start meines
ersten Lastrigs um **3 min 27 s** bzw. **1 min 21 s**, während drei andere Ströme Suiten fuhren. Das
ist **kein** Kausalitätsbeweis und wird hier nicht als einer geführt — es ist der Grund für den
Umbau. Drei Läufe wurden abgeschnitten; `load-gate3-defect.txt`, `load-gate3-quantities.txt` und
`load-gate3-fixed.txt` tragen jeweils **nur ihren Kopf**, also keinen Messwert.

**Das umgebaute Rig** `_round-scratch/TSK-0125/under_load.py`, dessen Parameter **vor** seinem
ersten Lauf hier stehen. Jede der vier Zahlen ist eine **Verweigerung**, keine Voreinstellung:

| Parameter | Wert | Wie durchgesetzt |
|---|---|---|
| Brennerzahl | höchstens die **Hälfte** der logischen CPUs — hier **8 von 16**, `os.cpu_count() // 2`, abgeleitet und nicht getippt | die Breite ist kein Argument, und ein Wort, das wie ein Knopf aussieht, wird jetzt **abgelehnt statt ignoriert** (F6). Gemessen: `refused: exactly <workdir> <label> <cap-seconds> stand before '--', and ['a','b','60','--burners','16'] is 5 word(s)` |
| Priorität | **unter normal**: Windows `BELOW_NORMAL_PRIORITY_CLASS` (`creationflags=0x4000`), POSIX `nice(+10)` | pro Kindprozess beim Start gesetzt |
| Deckel | **≤ 120 s**, gerechnet **ab dem ersten Brenner** — die Anlaufzeit liegt seit der Nacharbeit im Deckel (vorher hielt er den Host bis `cap + 2 s`, F7). Wer nicht hineinpasst, wird ABGESCHNITTEN und als „nicht gemessen" gemeldet, nie verlängert | gemessen: `refused: cap 300s is over the 120s this rig may hold the host for` |
| Fenster | startet **gar nicht**, solange `LOAD_WINDOW_OPEN` nicht daneben liegt | gemessen: `refused: no load window is open. … never beside another stream's suite` |
| Liegengebliebene PID-Liste | startet **gar nicht**, solange `LOAD_BURNER_PIDS` von einem abgeschnittenen Lauf dasteht | gemessen mit einer erfundenen Nummer: `refused: … pid(s) 4711. This rig does not kill by a recorded number …` |

**Tötungspfade, drei** — die, auf die es ankommt, laufen, wenn schon etwas schiefgegangen ist:

1. die Brenner sind **Kindprozesse** dieses Prozesses und werden in einem `finally` getötet; Deckel,
   Fehler und Abbruch nehmen die Last mit;
2. jede PID wird **unmittelbar nach** ihrem Start an `LOAD_BURNER_PIDS` angehängt. Der erste Satz
   hier lautete „bevor der erste startet" — das war nicht nur unscharf, sondern als Satz unmöglich:
   eine PID existiert vor ihrem Prozess nicht. Die ehrliche Schranke ist: ein Abbruch genau
   zwischen einem Start und seinem Eintrag lässt höchstens den **letzten** Start unverzeichnet
   (Prüfbefund F4);
3. der **nächste** Start tötet dort **nicht**. Er **verweigert**, nennt die Nummern und die
   Abhilfe. Eine liegengebliebene Liste überlebt nur einen harten Abbruch, also einen Neustart des
   Hosts — und danach gehört die Nummer dem, dem das Betriebssystem sie seither gegeben hat; ein
   `SIGTERM` darauf wäre eine Handlung auf einer ungeprüften Prämisse (F8). Der Rest ist benannt:
   ein zurückgebliebener Brenner wird von Hand beendet.

**Was das Rig ausdrücklich NICHT prüft:** ob gerade ein anderer Strom eine Suite fährt. Der Prozess
sieht keine anderen Agenten und tut nicht so — die Fensterdatei ist das Wort eines Menschen, und das
Rig sorgt nur dafür, dass es jemand sagen musste.

**Der Lauf, der noch aussteht** (im Fenster des Leads, nach dem Bericht jedes anderen G4-Stroms):

```
cd C:/Offline Repos/v2-testbed/_round-scratch/TSK-0125
echo "<Fenster des Leads>" > LOAD_WINDOW_OPEN
python -B under_load.py <rig-base|worktree> gate3-fixed 120 -- \
    <python> -B -m pytest -q -p no:cacheprovider \n      ".claude/hooks/test_gates.py::test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge"
rm LOAD_WINDOW_OPEN
```

Erwartet wird **grün oder ein Skip mit den Zahlen** — beides erfüllt AC-4; ein `pytest.fail` mit
„the overrun is the gate's" wäre der Befund, der eine weitere Runde nach sich zöge.

---

## 6. Läufe — nur die LESENDEN Suiten (DEC-0050)

Stand **nach** der Nacharbeit zur Prüfrunde 2 (jeweils ein pytest zur Zeit, keine Brenner):

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | `All checks passed!` |
| `python tools/bump_kit_version.py` | alle drei `unchanged` (Stempel steht) |
| `python tools/validate.py` | `all structural checks passed` |
| `tools/test_repo_hygiene.py` (ganz) | **31 passed** (1:54) |
| `tools/test_ci_lint_pinned.py` + `tools/test_context_budget.py` | **48 passed** (43,3 s) |
| `tools/test_repo_hygiene.py` + `tools/test_reference_skills.py` | **49 passed** (2:07) |
| `tools/test_office_duties.py` + `tools/test_ci_lint_pinned.py` + `tools/test_context_budget.py` | **85 passed** (24,2 s) |
| `tools/test_kitupdate.py` | **86 passed, 1 skipped** (8:35) — der Skip ist der POSIX-Installer-Zwilling |
| `.claude/hooks/test_gates.py::test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge` + der Namens-Prüfknoten | **2 passed** (20,1 s) |
| **Linux**, im echten Klon `clone-eol` (`core.autocrlf=true` gesetzt): `tools/test_repo_hygiene.py` + `tools/test_office_duties.py` | **68 passed** (6:31) |
| **Linux**, derselbe Klon nach der zweiten Nacharbeit: `tools/test_repo_hygiene.py` | **31 passed** (5:56) |

**Beobachtung, kein Befund und nicht meine Änderung:** in einer Kopie **ohne** `.git` fallen zwei
Knoten von `tools/test_repo_hygiene.py` hart, statt zu überspringen —
`test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom` und
`test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at` rufen `_tracked_files()`
ohne `_require_git()`. An `75a00d1` (Kopie `rig-base`) fallen dieselben zwei auf dieselbe Weise, also
Altbestand; in einem echten Klon sind sie grün. Nicht angefasst, weil `tools/**` eine Naht ist und
die beiden Knoten nicht zu diesem Auftrag gehören.

Die **volle** Suite gehört dem Merge (DEC-0050). `.claude/hooks/test_gates.py` als Ganzes ist nicht
gefahren: geändert ist dort **ein** Knoten, und der ist einzeln gefahren.

---

## 7. Bewusst nicht geschlossen, benannt

1. **`H160`** — `update-kit` meldet den Gedächtnisbaum und entfernt ihn nicht; die Provider-Frage
   (lädt eine Rolle ohne den Schlüssel einen vorhandenen Baum?) braucht eine echte CLI-Sitzung und
   ist aus einer Testsuite nicht herstellbar.
2. **`H161`** — der Gate-1-Schwestertest trägt dieselbe „eigene Dimensionierung in der gestoppten
   Spanne"-Klasse; nicht mitgeändert, weil dieser Strom **einen** Test in `test_gates.py` ändern
   darf. Gemessen begrenzt: 0,03–0,04 s gegen 1,03–1,19 s.
3. **`H162`** — die Last-Hälfte von AC-4 ist ungemessen; Rig umgebaut, wartet auf das Fenster.
4. **AC-1s Nachher-Richtung** braucht den nächsten Push; kein lokales Rig **ist** der gehostete
   Runner. Kein Loch, sondern ein Schritt, der dem Nutzer gehört.
5. **Der kanonische Teil von `project_memory/`** bleibt außerhalb der CRLF-Prüfung, weil dorthin
   kein Werkzeugschreibzugriff reicht (Gate 1); die betroffenen Dateien werden **gemeldet**. Das ist
   der bestehende Rest von `H37`, keine neue Nummer.
6. **Der Workflow ist unverändert.** Die zwei Roten waren Testfehler; eine Änderung an `ci.yml`
   hätte nichts davon behoben und wäre eine Behauptung ohne Messung gewesen.

---

## 8. Stempel

`python tools/bump_kit_version.py` im Worktree: dev `2026.09.04-1 → -2`, office `-3 → -4`,
research `-1 → -2`. **Vorläufig**, weil `team-kits/kernel/kitupdate.py` in den Kit-Hash **aller
drei** Kits eingeht und die Merge-Runde ohnehin einmal neu stempelt. Der Patch unter
`_round-scratch/TSK-0125/stream-hygiene.patch` trägt **keine** VERSION-Hunks (DEC-0070) und **keine**
CR-Bytes (gemessen: 0 von 65 388).

---

## 9. (g) — Runden, Dauer, Aufwand, Nähte, Löcher

### Runden

| | |
|---|---|
| Berichte des Umsetzers | **1** Erstbericht + **2** Nacharbeitsberichte + dieser Abschluss |
| Prüfungen | **3**: Runde 1 **FAIL** (9 Befunde), Runde 2 **FAIL** (3 Befunde, alle aus den Fixes), Runde 3 **PASS** (R2-1/R2-2/R2-3 geschlossen; ein Wortlaut-Kratzer N1, hier mitgenommen) |
| Auftrags-Neuschnitt | **1** (TSK-0124 → TSK-0125, wegen der Host-Regel; Worktree, Patch und Protokoll übernommen) |
| Fortsetzungen vom Plattenstand nach harter Abschaltung | **3** |

### Wanduhr — die Anker sind Dateizeitstempel, nicht Erinnerung

| Fenster | Von → bis | Inhalt |
|---|---|---|
| Bau | 09-04 06:12 → ~07:00 | die vier Kriterien, sechs Rigs, alle Rot-zuerst-Messungen außer der Last |
| Fortsetzung 1 | 09-04 ~17:45 → 17:49 | Protokollgerüst, dann harte Abschaltung |
| Fortsetzung 2 | 09-04 ~22:00 → 23:14 | drei abgeschnittene Lastläufe, zwei harte Abschaltungen |
| Erstbericht (nach dem Neuschnitt 23:29) | 09-04 23:30 → 09-05 00:24 | Rig-Umbau, `H160`–`H162`, Protokoll, Patch |
| Nacharbeit 1 (F1–F9) | 09-05 00:24 → 01:28 | |
| Nacharbeit 2 (R2-1..R2-3) | 09-05 01:28 → 01:57 | |
| Abschluss (N1 + diese Zeile) | 09-05 01:57 → ~02:15 | |
| Lastmessung im Fenster des Leads | 09-05 04:27 → 04:35 | ein Lauf, 20,1 s Hostbelegung, Fenster geschlossen |

**Gearbeitet ≈ 4 h 40; Spanne 09-04 06:12 → 09-05 ~02:15 ≈ 20 h.** Die Differenz ist **nicht**
Leerlauf dieses Stroms: zwischen den Fenstern lagen Wartezeiten auf Nachrichten des Koordinators und
die Prüfrunden, die ich nicht abrechne. Was ich **als eigene Kosten benenne**, ist der Wiederanlauf
nach jeder Abschaltung — dreimal die vollständige Neuaufnahme des Standes von der Platte — und der
einzige verlorene Arbeitsinhalt: die **drei abgeschnittenen Lastläufe** (Abschnitt 5a), deren
Berichtsdateien nur ihren Kopf tragen. Alles andere lag auf der Platte und wurde von dort übernommen;
kein Befund und keine Änderung ging verloren.

### Token — Schätzung, ausdrücklich keine Messung

Dieser Prozess kann seinen eigenen Verbrauch nicht lesen. Nach Umfang geschätzt, und als Schätzung
gekennzeichnet, damit die (g)-Tabelle keine erfundene Messung aufnimmt:

| Runde | Schätzung |
|---|---|
| Bau + Erstbericht (inkl. drei Fortsetzungen) | ~600–700 k |
| Nacharbeit 1 (F1–F9) | ~180–220 k |
| Nacharbeit 2 (R2-1..R2-3) | ~90–120 k |
| Abschluss | ~30 k |
| **Summe** | **~900 k–1,07 M** Umsetzer-Token |

### Rot-Messungen dieser Runde (je Kriterium, alle in einer Kopie außerhalb des Repos)

| Kriterium | Rot ohne den Fix |
|---|---|
| AC-1 | ubuntu-Rot im POSIX-Rig (WSL) Zeile für Zeile reproduziert; windows-Rot über einen echten zweiten Mount (`--basetemp=//localhost/C$/…`); der Namens-Fix ist zusätzlich auf **jedem** Host rot-fähig |
| AC-2 | Sweep rot mit Dateinamen; Stolperdraht in **beiden** Richtungen (Pin `*.png` entfernt → 496; `*.zzz` ergänzt → toter Pin); Pin-Zeile gelöscht → **1278**; `* binary` → **1278**; Doppelfall des Werkzeugs → falscher Satz; kanonischer Zustand ohne Prädikat → mitgenommen; `wide.bin` gepinnt → Widerspruch der zwei Prüfungen |
| AC-3 | Pilot am echten Prozess: „the update left a memory tree no installed role declares and told nobody" |
| AC-4 solo | `assert 4.622 < 4.5` an `75a00d1`, unverändert, **solo** |
| AC-4 Last | **grün** unter 8 unter-normalen Brennern (`1 passed in 16.31s`, Host 20,1 s belegt); der Knoten brauchte den Lastzweig nicht. Rest in `H162`: die 16-Brenner-Klasse und der Skip-Zweig bleiben ungemessen |

### Nähte — empfangen / am Merge erwartet

Die Tabelle steht vollständig in Abschnitt 1. Zusammengefasst: **empfangen** überall der Stand
`75a00d1`; **erwartet** ein geänderter Test in `.claude/hooks/test_gates.py` (Naht mit G4-1 und
G4-2), vier geänderte plus eine neue Datei unter `tools/**`, eine neue plus eine erweiterte Datei
unter `docs/**`, `team-kits/kernel/kitupdate.py` **allein** diesem Strom (G4-2 verboten), und drei
`VERSION`-Stempel, die der Merge neu setzt. `team-kits/kernel/cli.py` ist **nicht** geändert, aber
der AC-3-Satz reist in seinem Druckzweig — benannt und durch einen Test gehalten.

### Löcher

`H160` (Gedächtnisbaum wird gemeldet, nicht entfernt — die Provider-Frage ist ungemessen),
`H161` (der Gate-1-Schwestertest trägt dieselbe Klasse, ein Test pro Strom),
`H162` (Last-Hälfte ungemessen; Rig umgebaut, vier Verweigerungen gemessen, drei Rig-Eigenschaften
aus Prüfrunde 1 als Sätze darin). Keine vierte Nummer; die reservierte Spanne ist ausgeschöpft und
nicht überschritten.

---

## 12. Was die Merge-Runde ausführen muss

Drei Zeilen, in dieser Reihenfolge, und keine davon gehört in diesen Strom:

1. **Zeilenenden im Haupt-Checkout normalisieren.** In `C:\Offline Repos\AgentAndSkills`:
   `python tools/normalise_line_endings.py` (lesen, was es sagt), dann `--apply`. Erwartung nach der
   Messung vom 2026-09-04: **52** Dateien werden normalisiert, **eine** wird gar nicht erst
   angeboten (`project_memory/.audit/hook_events.jsonl`, kanonischer Zustand). Ohne diesen Schritt
   ist `tools/test_repo_hygiene.py::test_no_tracked_text_file_checks_out_with_crlf` dort **rot** —
   das ist der Zweck der Prüfung, keine Überraschung. Jede Datei, die das Werkzeug **verweigert**,
   ist von Hand zu entscheiden.
2. **Push für die Nachher-Richtung von AC-1.** Der gehostete Lauf auf `75a00d1` hatte je Plattform
   genau einen Fehlschlag, beide sind hier behoben und auf beiden Betriebssystemen grün nachgemessen
   — aber kein lokales Rig **ist** der Runner. Der Beweis ist der nächste Lauf, und der Push ist das
   Wort des Nutzers.
3. ~~Die Last-Hälfte von AC-4~~ — **erledigt am 2026-09-05 04:28** (Abschnitt 5a, `H162`): ein
   Lauf im Fenster des Leads, `1 passed in 16.31s`, Host 20,1 s belegt, Fenster geschlossen, kein
   Brenner übrig. **Kein** Befund für die Merge-Runde. Was offen bleibt, ist als Rest in `H162`
   benannt und braucht keinen Lauf: die 16-Brenner-Klasse mit Normalpriorität und der Skip-Zweig.


---

## 10. Nacharbeit nach Prüfrunde 1 (`verify-round-1.md`)

Urteil der Runde: **FAIL, nichts blockierend** — AC-1..AC-4 in der Sache erfüllt, fünf Sätze bzw.
eine Lücke zur Nacharbeit (F1–F5), drei Rig-Eigenschaften als Sätze in `H162` (F6–F8) und eine
Beobachtung (F9). Alle neun sind unten mit ihrer Messung erledigt.

### F1 — die Zeile, auf der AC-2 ruht, hatte keinen Test, der ohne sie rot wird

Der Prüfer maß: `* text=auto eol=lf` gelöscht → alle drei neuen Prüfungen **grün**, weil sie den
**Arbeitsbaum** lesen und der bleibt LF; und die zwei `binary`-Zeilen durch ein pauschales
`* binary` ersetzt → ebenfalls grün, während dann jede Textdatei `-text` wird.

**Gebaut:** `tools/test_repo_hygiene.py::test_git_decides_binary_by_bytes_and_pins_every_text_file_to_lf`.
Es fragt `git check-attr` nach der **Wirkung** — der Auflösung, die ein Checkout fährt — und hat
zwei Hälften über einem Subjekt, das als einziges in diesem Abschnitt **nicht** git's Antwort ist
(ein NUL in den ersten 8000 Bytes):

* jede Datei, die **nach Bytes Text** ist, muss `text: auto` **und** `eol: lf` auflösen;
* jede Datei, die **nach Bytes binär** ist, muss eine sein, die git ebenfalls nicht konvertiert
  (`-text`). Nur diese Richtung: die Gegenrichtung — git nennt etwas binär, obwohl kein NUL in den
  ersten Bytes steht — ist genau das, wofür die `binary`-Zeilen da sind, und wird **gemeldet**,
  nicht rot.

**Rot ohne den Fix** (Klon `clone-eol`, außerhalb des Repos, mit eigenem `HEAD`, Rig
`mutate_attrs.py`):

| Mutation | Ergebnis |
|---|---|
| `* text=auto eol=lf` gelöscht | `AssertionError: 1278 tracked file(s) carry no NUL in their first 8000 bytes … and git resolves them to something other than 'text: auto' / 'eol: lf', so a clone on a core.autocrlf=true host checks them out with CRLF and BUG-0025 is back` |
| die zwei `binary`-Zeilen durch `* binary` ersetzt | dieselbe Zusicherung rot (**1278**), während der ältere Stolperdraht wie vom Prüfer gemessen grün bleibt — genau deshalb brauchte es den neuen |
| zurückgesetzt | 4 passed |

### F2 — die Verweigerung nannte einen Grund, den `git status` widerlegt

Trägt der Blob in `HEAD` selbst CRLF, ist die Datei **unverändert**; „it carries a real uncommitted
change" schickt den Leser nach einer Änderung suchen, die es nicht gibt. Falsch ist dort der
**Index**, und der Befehl dafür ist `git add --renormalize`.

**Gebaut:** eine dritte Verzweigung in `normalise_line_endings._verdict`, die diesen Fall
**benennt** und den richtigen Befehl nennt; der Modul-Docstring und `docs/line-endings.md` sagen
dasselbe. **Rot ohne den Fix** (`clone-eol`, Zweig entfernt):
`tools/test_repo_hygiene.py::test_a_crlf_blob_in_head_is_not_reported_as_an_uncommitted_change` →
`AssertionError: normalised it is 8 bytes and HEAD holds 10 -- it carries a real uncommitted change`.
Die Klasse ist im Repo heute leer, deshalb steht der Test an `_committed`, der einen Tür zu `HEAD`,
und nicht am Baum.

### F3 — Prüfung und Abhilfe hatten nicht dasselbe Prädikat

`_repairable` stand nur im Test; `drifted_files()`/`judge()` nahmen jeden driftenden Pfad, und die
Protokollzeile über `project_memory/.audit/hook_events.jsonl` behauptete einen Schutz, den heute nur
die Größe dieser Datei hielt.

**Gebaut:** das Prädikat heißt `normalise_line_endings.repairable`, wohnt beim **Werkzeug** (der
Seite, die handelt), und `tools/test_repo_hygiene.py` importiert es. `drifted_files()` gibt
`(erreichbar, außer Reichweite)` zurück und das Werkzeug **listet** die zweite Menge auf, statt zu
schweigen. **Rot ohne den Fix:**
`tools/test_repo_hygiene.py::test_the_remedy_leaves_canonical_state_to_the_place_that_writes_it` →
`AssertionError: ['docs/note.md', 'project_memory/.audit/hook_events.jsonl', …]`. Die Merge-Zeile in
Abschnitt 3 ist entsprechend korrigiert.

Beim Bauen dieses Tests fiel eine eigene Gegenlücke auf und wurde geschlossen: die erste Fassung des
Stubs trennte die Spalten von `git ls-files --eol` mit Tabulatoren, während git **Leerzeichen**
benutzt und nur **einen** Tabulator vor den Pfad setzt. Der Parser fand damit nichts, und der Test
wäre über eine Form gelaufen, die das Werkzeug nie sieht. Die Form ist jetzt aus einer echten Zeile
dieses Repos abgeschrieben und der Kommentar sagt es.

### F4 / F6 / F7 / F8 — das Lastrig

In `H162` als Sätze eingetragen (keine vierte Nummer, die drei sind Eigenschaften **desselben**
Rigs) und im Rig gebaut: die PID-Zeile sagt jetzt, was der Code baut (F4); ein Wort vor `--`, das
wie ein Knopf aussieht, wird **abgelehnt statt ignoriert** (F6); der Deckel läuft **ab dem ersten
Brenner**, die Anlaufzeit liegt darin (F7); und eine liegengebliebene PID-Liste wird **verweigert
statt blind getötet** (F8). Alle vier Verweigerungen gemessen, **ohne** einen Brenner zu starten und
mit sofort wieder geschlossenem Fenster.

### F5 — dieselbe wachsende Zahl an vier ausgelieferten Stellen

`1794 / 516 / 499` stand in `.gitattributes`, `docs/line-endings.md`,
`tools/normalise_line_endings.py` und `tools/test_repo_hygiene.py`. Alle vier tragen jetzt die
**Eigenschaft** und den Test, der sie nachmisst; die Stückzahlen stehen nur noch hier im Protokoll
(Abschnitt 0) und in der Löcherliste. Nachgemessen: `grep` über die vier Dateien nach den Zahlen →
keine Treffer.

### F9 — die ROOT-Hälfte des Wächters ist auf POSIX nicht erreichbar

Der Prüfer hat gemessen, dass `_duties._project_directory` auf POSIX vor dem Wächter umkehrt
(`_literal_prefix` gibt für jede dort mögliche Schreibweise `''` zurück) — die alte Zusicherung war
deshalb dort falsch, und der Fix ist richtig. Offen war nur eine Docstring-Nuance: „Both ends here"
ist eine **Windows**-Aussage. Sie steht jetzt als eigener Absatz im Docstring von
`tools/test_office_duties.py::test_a_filing_plan_that_resolves_to_the_project_ROOT_is_not_walked`,
mit der Messung des Prüfers (Wächter-Hälfte entfernt → Windows rot, Linux grün).

### Eine Gegenlücke, die diese Nacharbeit selbst eingeführt hätte

`tools/normalise_line_endings.py` trug `sys.dont_write_bytecode = True`, aus `validate.py`
übernommen, ohne dass dessen Grund mitkam (dieses Werkzeug importiert nichts aus `team-kits/`).
Seit F3 **importiert die Testsuite dieses Modul**, also hätte das Flag im pytest-Prozess gestanden
— genau dort, wo `tools/test_hooks.py::test_the_suite_leaves_no_bytecode_in_the_kit_tree` misst. Ein
Test, der dann aus meinem Grund grün gewesen wäre statt aus seinem. Die Zeile ist entfernt und der
Kommentar an ihrer Stelle sagt, warum sie nicht wiederkommt.

---

## 11. Nacharbeit nach Prüfrunde 2 (`verify-round-2.md`)

Urteil der Runde: **FAIL, klein, nichts blockierend** — alle neun Befunde aus Runde 1 vom Prüfer
nachgemessen und geschlossen; drei neue Befunde, alle aus den Fixes selbst.

### R2-1 — die beiden Binär-Prüfungen widersprachen sich für genau ihre eigene Klasse

Die neue Prüfung liest `NUL_WINDOW` = 8000 Bytes, **git liest die ganze Datei**. Für eine
Binärdatei, deren erstes NUL dahinter liegt, gab es **keinen** Zustand von `.gitattributes`, in dem
beide ausgelieferten Prüfungen grün sind: ohne Pin forderte die alte ihn, mit Pin verbot ihn die
neue — und der Docstring sagte über diese Klasse „reported, not failed", während der Code failte.

**Selbst reproduziert** (Fixture `assets/wide.bin`: 709 × `filler-line\n` = 8508 Bytes, dann das
NUL, dann ein Rest; im Klon `clone-eol` in den Index gelegt, ohne Commit — Rig
`_round-scratch/TSK-0125/wide_fixture.py`):

| Zustand | mit dem alten Code | mit dem Fix |
|---|---|---|
| Datei **gepinnt** (`assets/wide.bin binary`) | `AssertionError: 1 tracked file(s) carry no NUL in their first 8000 bytes …` (`:185`) | **2 passed**, und der Melde-Zweig feuert: `UserWarning: git treats these as binary although their first 8000 bytes carry no NUL … ['assets/wide.bin']` |
| Datei **ungepinnt** | — | die **alte** Prüfung rot und fordert den Pin (`git reads these files as binary by their bytes, but no 'binary' line … covers them`), die neue grün |

**Gebaut:** git's eigene Lesung der **Inhalts**-Zeilenenden (`w/`-Spalte) kommt **vor** der ersten
Zusicherung von der Textseite herunter; die so entfernten Pfade sind genau die Melde-Menge am Ende.
Der Docstring sagt jetzt, dass die zwei Lesungen nicht dieselben Bytes sehen, und warum.

**Und eine Behauptung meines eigenen Fixes war falsch, gemessen und korrigiert:** ich hatte
geschrieben, ein pauschales `* binary` „leert das Subjekt". Es tut das **nicht** — `git ls-files
--eol` meldet dann `i/lf w/lf attr/-text`, weil die `w/`-Spalte den **Inhalt** liest und nicht das
Attribut. Was die Mutation fängt, ist die `text: auto`-Hälfte; `eol: lf` überlebt ein `binary`
(gemessen an `README.md`). Beide Mutationen von F1 bleiben rot — Pin gelöscht **1278** Dateien,
`* binary` **1278** Dateien —, und die Sätze sagen jetzt, welche Hälfte welche Mutation fängt.

### R2-2 — die beiden Verweigerungsgründe schließen einander nicht aus

`CRLF in committed` stand **vor** `normalised != committed`; sind beide wahr — CRLF-Blob **und**
Handänderung —, gewann der Renormalisierungs-Satz, und der ist dann falsch: `git status` meldet die
Datei sehr wohl, und `git add --renormalize` nähme die fremde Änderung mit in den Index.

**Gebaut:** die zwei Fragen werden getrennt gestellt, und der Vergleich läuft gegen den Blob **wie
normalisiert** (`committed.replace(CRLF, LF)`) — sonst sähe unter einem CRLF-Blob jede Datei
geändert aus. Für den Doppelfall nennt das Werkzeug **beide** Gründe und empfiehlt **keinen** der
zwei Befehle allein. `docs/line-endings.md` führt jetzt drei Fälle statt zweier sich ausschließender.

**Rot ohne den Fix** (Klon außerhalb des Repos, geordnetes Fragenpaar wiederhergestellt):
`tools/test_repo_hygiene.py::test_a_crlf_blob_in_head_is_not_reported_as_an_uncommitted_change` →
`AssertionError: the combination is answered with one of the two single reasons: the blob HEAD holds
carries CRLF itself, so the working tree is not what is wrong here and 'git status' says nothing
about this file …`. Der Test hat dafür einen **vierten** Fall bekommen (Blob `one/two` mit CRLF,
Datei zusätzlich `THREE-a-real-edit`).

### R2-3 — die Begründung nannte einen Test, der dafür nicht fallen kann

Der Satz behauptete, `tools/test_hooks.py::test_the_suite_leaves_no_bytecode_in_the_kit_tree` würde
ein gesetztes `sys.dont_write_bytecode` bemerken. **Selbst nachgemessen** im Klon, Flag zurück ins
Werkzeug gesetzt und die Suite so gefahren, dass sie es importiert:

```
pytest tools/test_hooks.py tools/test_repo_hygiene.py -k "leaves_no_bytecode or crlf_blob_in_head"
2 passed, 986 deselected in 5.72s
```

Ein gesetztes Flag unterdrückt Bytecode und macht die Zusicherung **leichter**, nie rot. Die Klausel
ist gestrichen; die Entscheidung trägt der Grund, der stimmt (das Werkzeug importiert nur die
Standardbibliothek, das Flag kauft nichts) plus der Satz, dass hier **absichtlich kein** Test als
Stolperdraht genannt wird — eine genannte Prüfung, die nicht fallen kann, ist teurer als keine.
Die zweite vom Prüfer angebotene Möglichkeit — dem genannten Test eine Zeile `assert not
sys.dont_write_bytecode` zu geben — ist bewusst **nicht** gewählt: `tools/test_hooks.py` ist eine
Naht dieses Generationsschnitts, und der Satz wird nicht wahrer, wenn man dafür in eine fremde,
gemeinsam genutzte Datei schreibt.