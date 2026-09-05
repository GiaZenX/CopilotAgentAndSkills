# TSK-0126 — Merge-Prüfung Runde 2 (harness-verifier), Nacharbeit 1

Gemessen am Arbeitsbaum `C:/Offline Repos/AgentAndSkills` (read-only) in einer FRISCHEN `.git`-losen
Kopie `verify/merged2` mit eigenem Index, und an DREI frisch gescaffoldeten Piloten
(`verify/pilots2/{dev,office,research}`, Kit-Store als Kopie unter `verify/home2/.claude/team-kits`
— der globale Store wurde nicht angefasst). Rig unter `verify/rig/` (`_rig2.refuse_outside_rig()`,
ausschliesslich binäres I/O, `DEC-0070`).

**URTEIL: FAIL** — alle sechs Befunde der Runde 1 sind behoben und nachgemessen. Vier neue
blockierende Befunde, drei mittlere. Drei der vier sind billig (Sätze, eine Zeile, ein Pfad); einer
ist eine Zeile Code.

---

## Befunde, blockierend zuerst

### R2-B1 — BLOCKIEREND: die `DEC-0074`-Ableitung schaltet sich in office/research WIEDER EIN, und ein Befehl der Kit-eigenen CLI tut genau das

Die Ableitung liest den BESTAND (`dispatch.py:2069`
`os.path.isdir(state.root / ACTIVE_DIRS["SR"])`). Ein Verzeichnis auf der Platte kann entstehen —
und das Kit bietet den Weg selbst an.

Gemessen als Prozess am gescaffoldeten office-Piloten (`verify/rig/r2_office_cli2.py`, die
**Kit-eigene** `scripts/harness.py`):

```
root: PROC-0001 | system/active before: False
capture SR (office CLI): rc 0 | SR-0001 PROPOSED
system/active after: True | items ['SR-0001.yaml']
```

`capture SR` steht in der Typenliste der office-CLI (`{BUG,CR,DEC,EVD,EXP,FR,HYP,INV,MST,PR,PROC,RQ,SR,TSK}`)
— und war bis `DEC-0074` genau das Wort, das die Verweigerung als Abhilfe ausdruckte. Danach
(`verify/rig/r2_b1.py`, echter Kernel, gescaffoldete Piloten):

```
office, PROC root, no system/active                  -> GRANTED (not asked)
office, system/active CREATED BY HAND (empty)        -> REFUSED DispatchError
office AFTER one capture SR (PROPOSED, not accepted) -> REFUSED DispatchError
      TSK-0001 hangs from PROC-0001 (class 'feature'), and no SR in status ACCEPTED hangs from that goal
research, RQ root, system/active CREATED BY HAND     -> REFUSED DispatchError
```

Und der Spawn zieht mit (`verify/rig/r2_spawn.py`, Kit-Haken `gate_dispatch.py` als Prozess,
derselbe Header vorher/nachher):

```
office: create_lease GRANTED, spawn rc 2 (nur acceptance_refs -- Fixture, nicht die Pflicht)
office nach mkdir system/active, SAME header -> rc 2
      TSK-0001 hangs from PROC-0001 ... no SR in status ACCEPTED hangs from that goal
```

`docs/POST_V2_WISHLIST.md:9750` nennt als Rest **nur die Gegenrichtung** („Ein dev-Projekt, dem
`system/active` fehlt, wird still nicht mehr gefragt") und begrenzt sie mit „das Verzeichnis gehoert
zum Scaffold; in einem echten Projekt verschwindet es nicht von selbst". Für die hier gemessene
Richtung ist genau das Gegenteil wahr: das Verzeichnis **entsteht** von selbst, aus einem Befehl,
den die CLI des Kits anbietet, rc 0, in einer Sitzung. Das ist die Sackgasse, die `DEC-0074`
geschlossen hat, in dem Kit, für das die Entscheidung getroffen wurde — ungenannt.

**Minimalfix (eine von zwei):** (a) `H163`s Rest um diese Richtung erweitern (Mechanismus, obige
Kette, Begrenzung: fail-closed, aber ohne Abhilfe im Kit-Text), oder (b) die Ableitung an den
VERTRAG hängen statt an den Bestand — dann gibt es die Richtung nicht (siehe R2-B2).

### R2-B2 — BLOCKIEREND: `DEC-0074`s Beschlusstext und die gebaute Ableitung sind zwei verschiedene Regeln, und der Beschlusstext widerspricht sich selbst

`project_memory/decisions/active/DEC-0074.yaml`, `decision` (1): *„a kit whose contract (kernel
backlog_types, read per kit) declares the type `SR` AND whose root type (`ROOT_TYPE_BY_KIT`) does
not carry the acceptance criteria itself; today that is dev-team alone."*

Gebaut ist `team-kits/kernel/dispatch.py:2069` — der **Bestand** des Projektverzeichnisses. Zwei
Lücken, beide gemessen:

1. **„contract … read per kit" hat im Code keinen Adressaten.** `backlog_types` ist EIN geteilter
   Vertrag; `ACTIVE_DIRS["SR"]` existiert für jedes Kit. Das einzige kit-spezifische Artefakt ist
   der Vorlagenbaum — also der Bestand. Gemessen: `ls */templates/project_memory` → nur `dev-team`
   liefert `system/`. Der Kommentar im Code sagt das ehrlich („die project's own stock"); der
   Beschlusstext sagt etwas anderes.
2. **Die zweite Klausel ist invertiert.** `_carries_its_own_criteria` ist für `PR` **wahr**
   (H163s eigene Tabelle: `PR`, `RQ`, `BUG`, `CR`, `EXP` → wahr). Wörtlich gelesen wäre dev-team
   damit ebenfalls ausgenommen — die Pflicht träfe **kein** Kit, während der nächste Satz derselben
   Zeile „today that is dev-team alone" sagt.

Das ist der Datensatz, aus dem ein späterer Leser die Regel neu ableitet, und er ist die
Aufzeichnung einer NUTZERENTSCHEIDUNG. `project_memory/` liegt ausserhalb des Umsetzer-Scopes —
dieser Befund gehört dem Lead. **Minimalfix:** `decision` (1) auf das umschreiben, was gebaut ist
(„ein Projekt, dessen Bestand eine Heimat für den Typ `SR` führt"), oder die Ableitung auf einen
wirklich vertraglichen Diskriminator umstellen und beides gleich schreiben.

### R2-B3 — BLOCKIEREND: die EVD-Zeile in Abschnitt 11 macht einen ausgelieferten Test rot, sobald der Lead sie fährt

`project_memory/staging/TSK-0126/merge-protocol.md:346 ff.`:
`--artifact-ref "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0126/full-run-4.txt"`.

Gemessen (`verify/rig/r2_evd.py`, Probe-EVD mit genau dieser Zeile in einer Kopie des Bestands):

```
baseline (no probe)                                    rc 0 | 1 passed
EVD with the artifact-ref the protocol hands the lead  rc 1 | 1 failed
      AssertionError: artifact_refs that resolve nowhere in this repo:
      project_memory/evidence/EVD-9999.yaml -> C:/Offline Repos/v2-testbed/_round-scratch/TSK-0126/full-run-4.txt
the same EVD with a state-relative ref                 rc 0 | 1 passed
```

Der Grund steht im laufenden Code: `tools/test_repo_hygiene._ref_candidates` liefert eine Wurzel nur,
solange der aufgelöste Pfad INNERHALB des Repos bleibt. Dazu kommt: das Runden-Scratch wird beim
Rundenabschluss aufgeräumt (CLAUDE.md), der Verweis zeigt danach ohnehin ins Leere.
**Minimalfix:** `full-run-4.txt` und `gates-run-3.txt` nach `project_memory/staging/TSK-0126/`
kopieren — die eine Stelle, in die diese Runde schreiben darf — und
`--artifact-ref staging/TSK-0126/full-run-4.txt` schreiben.

### R2-B4 — BLOCKIEREND für Ausgabe (3): der Glob-Fix lässt dieselbe Klasse als KLAMMER-Expansion offen, und `H165` urteilt „GESCHLOSSEN"

Mit der echten Shell gemessen — Git Bash, ein `python`-Shim auf `PATH`, der sein `argv` in eine
DATEI schreibt (`verify/rig/r2_shell.py`, `shim.log`):

```
python -m pytest tools/test_*.py -q             -> 43 words, 40 .py paths handed to the runner
python -m pytest tools/{test_*,conftest}.py -q  -> 44 words, 41 .py paths handed to the runner
python -m pytest tools/test_{board,state}.py -q ->  5 words,  2 .py paths
python -m pytest "tools/test_*.py" -q           ->  4 words,  1 .py path (literal, pytest globbt nicht)
```

Das Gate dazu (`verify/rig/r2_b2.py`, ausgelieferter Haken als Prozess):

```
rc 2 REFUSED | python -m pytest tools/test_*.py -q
rc 0 allowed | python -m pytest tools/{test_*,conftest}.py -q
```

41 von 40 Mitgliedern plus `conftest.py` — die ganze Fläche, 56 Minuten, rc 0. Die Ursache ist eine
Aufzählung an der Stelle, an der der Kopf der Datei eine Eigenschaft behauptet: `glob.has_magic`
kennt `*`, `?`, `[` und **nicht** `{`. `H165`s eigener Mechanismus-Satz („die Shell ersetzt ihn durch
alles, was er trifft") deckt die Klammer mit; sein Urteil „GESCHLOSSEN für die erklärte Fläche" tut
es nicht.

**Minimalfix:** vor dem Globben klammer-expandieren, oder — die Definition statt der Liste — ein
Wort, dessen Expansion dieses Gate nicht bestimmen kann, ist **keine** Auswahl und fällt in den
fail-closed Zweig, den `_expansion_covers` für „keine `members`" schon hat.

### R2-M1 — Über-Verweigerung: ein QUOTIERTER Glob

`python -m pytest "tools/test_*.py" -q` ist rc 2, während die Shell dem Läufer EIN literales Wort
übergibt (oben gemessen) und pytest nicht globbt — die Zeile fährt **nichts**. Das Gate kann die
Quotierungssemantik nicht kennen; die Richtung ist sicher, aber sie steht in keinem Loch.
`H165`s benannte Über-Verweigerung nennt nur „eine Fläche ohne `members`".

### R2-M2 — der Zeigerleser trägt die Datei weiter als sein Kommentar sagt

`tools/test_repo_hygiene.py:1015` sagt „every further one in the **same statement**". Gemessen
(`verify/rig/r2_m1.py`, `_test_citations` direkt):

```
same statement          : [(…office_duties.py, test_a_project…), (…office_duties.py, test_somewhere_else)]
a LATER, unrelated para : [(…office_duties.py, test_a_project…), (…office_duties.py, test_somewhere_else)]
no file before it       : []
```

`carried` gilt über die GANZE Datei. Meistens Über-Verweigerung (falsches Rot), aber ein falsches
GRÜN ist möglich, wenn die mitgetragene Datei den Namen zufällig definiert. **Minimalfix:** ein Wort
im Kommentar, oder eine Absatzgrenze im Leser.

### R2-M3 — `radar/decided.md` ist inhaltlich geändert und liegt ausserhalb `allowed_scope`

`git diff --numstat HEAD -- radar/decided.md` = **9 / 0**, mtime 10:49. Inhalt und Zeitstempel
weisen es als Radar-Triage des Leads aus (eine der neun Zeilen kündigt diese Prüfrunde an), nicht
als Schreibvorgang des Merges — es fährt aber im selben Commit mit, und das Item deckt es nicht.
Ebenfalls ausserhalb, ohne Inhaltsänderung: `.gitignore`, `user/claude/statusline.py` (beide Z6),
`radar/2026-09-04-claude.md`, `radar/2026-09-05-codex.md` (untracked, Lead).

---

## Die Frage des Nutzers: trägt die GENERIERTE Codex-Überlagerung Gate 5?

Gemessen an einem frisch gescaffoldeten dev-Piloten, gelesen wird die **erzeugte Datei**, nicht die
Prosa des Generators (`verify/rig/r2_codex2.py`, `.codex/hooks.json`):

```
event=PreToolUse  matcher='Bash'  timeout=NONE   gate=gate_test_scope.py
   command: … TEAM_KIT_PROVIDER=codex … "$py" -B "$root/.claude/hooks/_gate.py" gate_test_scope.py
event=PreToolUse  matcher='Bash'  timeout=1800   gate=gate_pipeline.py
overlay entries with a timeout: {False: 25, True: 1}
```

**Antwort: Gate 5 ist da, nicht weggefallen** — `PreToolUse`, Matcher `Bash`, über `_gate.py`, mit
demselben Bundle-Hash wie die anderen. **Ohne `timeout`** — genau wie 25 der 26 Überlagerungs-
Einträge; die einzige Frist trägt `gate_pipeline` (1800), und das spiegelt die Claude-Seite des
Kits eins zu eins (dort ebenfalls nur `gate_pipeline`). Die Überlagerung erfindet also keine Frist
und verschluckt keine. Der Matcher ist `Bash` statt `Bash|PowerShell`, weil Codex kein
PowerShell-Werkzeug führt; aus demselben Grund fehlen `gate_approval` und `guard_question_context`
(beide `AskUserQuestion`). `.codex/config.toml` nennt keine Frist. Das ist damit dieselbe
angenommene AC-2-Abweichung wie auf der Claude-Seite — und sie gilt für Codex mit.

---

## Ergebnis je erwarteter Ausgabe

| # | Ausgabe | Urteil |
|---|---|---|
| 1 | vier Patches in Nahtreihenfolge | **PASS** |
| 2 | zehn Nähte + Schiedsrichter | **PASS** (M1 der Erstrunde behoben, Zeigertabelle ergänzt) |
| 3 | Löcherliste H151–H165 | **FAIL** (R2-B1 ungenannte Richtung; R2-B4 `H165` urteilt „geschlossen"; R2-M1 nicht benannt) |
| 4 | Merge-Befunde behoben oder benannt; Zuschnitt tabelliert | **PASS** |
| 5 | EIN Stempel, Läufe, Gate 5 als Prozess | **PASS** |
| 6 | Hostregel | **PASS** |
| 7 | Protokoll mit allen Tabellen | **PASS mit Befund** (R2-B3: die EVD-Zeile) |

## Ergebnis je Ziel

| Ziel | AC | Urteil |
|---|---|---|
| **PR-0004** | AC-1 Gate 5 | **PASS mit offener Restklasse** (R2-B4 Klammer, R2-M1 quotierter Glob) |
| | AC-2 Fristen | **ABWEICHUNG, vom Lead angenommen** — gemessen dev 1/31, office **0/30**, research 1/28 Kit-Einträge mit `timeout`; Codex-Überlagerung 1/26. Wörtlich nicht erfüllt, korrekt so im Protokoll §14 benannt |
| | AC-3 Design-Checks | in dieser Runde **nicht gemessen** |
| | AC-4 Kostenseite | **PASS** |
| **PR-0005** | AC-1..AC-5 | **PASS** für die gebaute Regel an allen drei gescaffoldeten Kits; R2-B1/R2-B2 treffen die AUFZEICHNUNG (DEC-0074, H163-Rest), nicht das Verhalten der drei Vorlagen |
| **PR-0006** | AC-1..AC-4 | **PASS** |
| **PR-0007** | AC-1 CI | **OFFEN** — braucht den Push |
| | AC-2 Zeilenenden | **PASS** (52 byte-gleich zu HEAD, 0 CR ausser dem Auditlog) |
| | AC-3 / AC-4 | **PASS** |

---

## Ausdrückliche Negativbefunde — GEMESSEN (die Angriffe der Runde 1, neu gefahren)

* **B1 der Runde 1 ist behoben.** Frischer research-Pilot: `TSK` aus der `RQ`-Wurzel → GRANTED, aus
  einem `HYP` → GRANTED, aus einem `EXP` → GRANTED. dev mit LEEREM `system/active` → REFUSED
  (richtig: die Heimat existiert). dev mit gelöschtem `system/active` → GRANTED = **genau** `H163`s
  benannter Rest und nichts darüber hinaus.
* **Die Verengung misst beide Richtungen.** Mutation von `_the_project_keeps_the_architect_step`:
  immer `True` → **1 failed** (`test_a_project_with_no_home_for_the_architect_step_is_not_asked`);
  immer `False` → **3 failed** (derselbe Knoten plus die beiden, die `H163` jetzt nennt); ausgeliefert
  **195 passed**; `dispatch.py` byte-gleich zurückgesetzt.
* **B2 der Runde 1 ist behoben** für jede Stern-Schreibweise: `tools/test_*.py`,
  `tools/test_[a-z]*.py`, `tools/*`, `tools/*.py`, `**/test_*.py`, `*/test_*.py`, quotiert und
  absolut alle **rc 2**; echte Auswahlen (`tools/test_x*.py`, `tools/test_re*.py`,
  `tools/**/test_*.py`) **rc 0**; mit `DELIVERY_RUN` **rc 0**; ein Glob unter der DATEI-Wurzel
  (`.claude/hooks/test_g*.py`) **rc 2**, einer, der sie verfehlt, **rc 0**.
* **Der `members`-Stolperdraht ist wirklich rot.** Eine neue Datei `tools/probe_stale_test.py`, die
  pytest sammelt und der Glob verfehlt → `test_the_declared_members_are_the_files_the_runner_really_collects`
  **1 failed** („misses 1 file(s) the runner really runs"); eine neue `tools/test_zzz_probe.py`, die
  der Glob trifft → 1 passed; sauber 1 passed.
* **M1 ist behoben.** Meine Mutation der Erstrunde (`…through` → `…throughX` in der dev-Verfassung):
  `test_every_test_pointer_this_repo_writes_resolves` **1 failed** mit `file:line`
  (`team-kits/dev-team/constitution/AGENTS.md:237`), zurückgesetzt 1 passed. Eine Fortsetzung ohne
  vorangehende Dateinennung bleibt ungelesen — und der Boden misst genau das.
* **M2 ist behoben**: `H163` nennt jetzt die beiden Tests, die unter der Mutation rot werden, plus
  den neuen Knoten.
* **M3 ist behoben, unabhängig nachgemessen** (`verify/rig/r2_migrate.py`, frische
  `project_memory`-Kopie ausserhalb des Repos): Probelauf **155 written, 0 already in the store, 0
  Kollisionen**; Lauf 1 **155 Items / 155 Prosadateien**, Dokument **800 589 → 192 003 B**, sha
  **`61988c1592b26a1a`**; Lauf 2 **0 written**, sha identisch; **155 Indexzeilen**, `H165`-Zeile und
  `docs/holes/H165.md` vorhanden, 0 CR. Genau die drei Zahlen des Protokolls. Naht 4 jetzt **40/2**;
  der Kit-Haken-Hash steht nur noch an einer Stelle und stimmt: `68886e7eb882` ×3.
* **Die sieben migrierten Richter**: an einer migrierten Kopie des gemergten Baums **7 passed**.
* **Spawn und Lease stimmen überein** (Kit-Haken `gate_dispatch.py` als Prozess): in dev mit
  ACCEPTED `SR` läuft beides, nach dem Entfernen des `SR` verweigert derselbe Header den Spawn mit
  dem Architektenschritt-Satz.
* **Stempel**: `2026.09.05-3` ×3 (mtime 12:40), `bump_kit_version.py --check` „unchanged" ×3; der
  Lieferlauf liegt DANACH (13:37), und **keine** Datei im `allowed_scope` trägt eine spätere mtime —
  die einzige spätere Schreibung ist `staging/generation-4-streams.md` (14:00, Lead).
* **Läufe**: `full-run-4.txt` **4683 passed / 14 skipped / 0 failed, 56:02**;
  `gates-run-3.txt` **7 failed / 540 passed**, und die sieben sind namentlich die migrierten Richter.
  `ruff check .` in der Kopie **All checks passed** (auch ausserhalb des `allowed_scope`);
  `validate.py` grün.
* **Baum**: 82 inhaltlich geänderte Dateien, 52 im Arbeitsbaum berührte ohne Inhaltsänderung, **alle
  byte-gleich zu HEAD**; 0 CR ausser `project_memory/.audit/hook_events.jsonl` (609).
* **Protokoll**: Abschnitt 12 (Nacharbeit), 13 (Zeigertabelle, 10 Zeilen) und 14 (Urteil je Ziel mit
  der ausdrücklich benannten AC-2-Abweichung) sind vorhanden und vollständig.

## Ausdrücklich NICHT gemessen

* Die volle `tools/`-Suite (`DEC-0050`) — `full-run-4.txt` gelesen und die Reihenfolge nachgerechnet.
* Ob der Lieferlauf das Präfix `DELIVERY_RUN=TSK-0126` wirklich trug: das Log echot keine Umgebung,
  Gate 5 bindet erst beim nächsten Sitzungsstart, und es existiert noch kein `EVD` mit
  `run_scope: full` für `TSK-0126`.
* `PR-0004` AC-3 (Browser-Checks an einer gebauten App).
* `PR-0007` AC-1 (gehosteter CI-Lauf) und die härtere Lastklasse von `H162`.
* Die Klammer-Lücke aus R2-B4 in einem KIT-Projekt: die Kits liefern keine `test_surface`-Erklärung
  aus, also urteilt Gate 5 dort erst, wenn ein Projekt selbst eine schreibt (`H165`).

## Eigene Fehlgriffe

* Mein erster Shim-Lauf startete WSL-`bash` statt Git Bash und meldete „der Shim wurde nicht
  erreicht"; mit `C:/Program Files/Git/bin/bash.exe` misst er. Rig-Fehler, kein Befund.
* Aus Runde 1 stehen zwei eigene Fehlgriffe im dortigen Bericht (zu schmale Auswahl bei der
  Timeout-Mutation, ein abgeschnittener Testname als vermeintlicher Befund); beide bleiben
  eingestanden.

---

## Was blockiert, was Rest ist

* **R2-B1** und **R2-B4** blockieren Ausgabe (3): beide sind gemessene, offene Klassen, deren Kette
  in einer Sitzung durchläuft, und beide stehen in keinem Eintrag. Geschlossen ODER benannt — ein
  dritter Zustand existiert nicht.
* **R2-B2** blockiert als Aufzeichnungsfehler in einer NUTZERentscheidung; er gehört dem Lead.
* **R2-B3** blockiert den Rundenabschluss: die Zeile, die der Lead fahren soll, macht einen
  ausgelieferten Test rot.
* **R2-M1, R2-M2, R2-M3** sind Nacharbeiten an Text, Kommentar und Scope-Notiz.
