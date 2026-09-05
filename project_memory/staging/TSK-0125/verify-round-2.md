# TSK-0125 — Prüfbericht Runde 2 (`harness-verifier`)

Gegen den laufenden Code gemessen, read-only auf Repo und Worktree. Frische Kopien unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0125\verify\r2\`:
`base` = pristine `75a00d1` (Klon des Worktree-Branches, nie des Repos), `applied` = `base` + Patch,
`tree` = Worktree-Kopie **ohne** `.git` (mit Stempel), `base-nogit` = `75a00d1` ohne `.git`.
Das Lastfenster ist **geschlossen geblieben**: keine Brenner gestartet, keine Fensterdatei im
Verzeichnis des Umsetzers angelegt; die Verweigerungen sind an einer **eigenen Kopie** des Rigs
gemessen, in der zusätzlich eine PID-Datei als Sicherheitsnetz lag, damit auch eine gültige
Kommandozeile vor dem ersten Brenner abbricht.

**Urteil: FAIL (zweite Nacharbeit, klein).** Alle neun Befunde aus Runde 1 sind geschlossen und von
mir nachgemessen. Drei neue Befunde stammen aus den Fixes selbst — einer davon ist ein echter
Widerspruch zwischen zwei ausgelieferten Prüfungen. **Keiner ist blockierend**; alle drei sind
Sätze bzw. eine Fensterbreite, zusammen deutlich unter einer halben Stunde Arbeit.

---

## Urteil je Kriterium

| Kriterium | Urteil | Grundlage |
|---|---|---|
| AC-1 (BUG-0069) | **PASS** | Code unverändert gegenüber Runde 1 (nur der F9-Docstring kam dazu); die drei Knoten auf Windows, Linux und über einen echten zweiten Mount erneut grün |
| AC-2 (BUG-0025) | **PASS mit Befunden** (R2-1, R2-2) | F1/F2/F3/F5 geschlossen und nachgemessen; **aber** die beiden Binär-Prüfungen widersprechen sich für genau die Klasse, für die die `binary`-Zeilen da sind |
| AC-3 (BUG-0088) | **PASS** | `kitupdate.py` unverändert; die vier Gedächtnis-Knoten erneut grün (19,4 s) |
| AC-4 Solo-Hälfte | **PASS** | Knoten erneut grün; Ableitung unverändert |
| AC-4 Rig-Entwurf | **PASS** | F4/F6/F7/F8 geschlossen; sechs Verweigerungen gemessen, nichts geschrieben, kein Brenner |
| AC-4 Last-Hälfte | **ausstehend im Fenster des Leads** — kein Befund | nicht gemessen, Fenster zu |
| Pflicht 5 | **PASS mit Befund R2-3** | jeder neue Test einzeln mutiert und rot gesehen; ein genannter Test kann für seine Aussage aber nicht fallen |
| Pflicht 6 | **PASS** | per AST erneut **genau eine** geänderte Definition in `test_gates.py` |
| Pflicht 7 | **PASS** | Patch 10 Dateien, 82 987 B, 0 CR, keine VERSION-Hunks, `git apply --check` rc 0 auf frischem `75a00d1` |
| Pflicht 8 | **PASS** | kein Brenner, ein pytest zur Zeit, kurze Fenster |

---

## Runde-1-Befunde: Status, jeder nachgemessen

| Befund | Status | Messung |
|---|---|---|
| **F1** Pin ohne roten Test | **GESCHLOSSEN** | Pin gelöscht → `AssertionError: 1278 tracked file(s) carry no NUL in their first 8000 bytes … The line that pins them is `* text=auto eol=lf`` (`tools/test_repo_hygiene.py:185`); die zwei `binary`-Zeilen durch `* binary` ersetzt → **dieselbe** Zusicherung rot, 1278 Dateien; zurückgesetzt → grün |
| **F2** falscher Verweigerungsgrund | **GESCHLOSSEN** (öffnet R2-2) | dritter Zweig vorhanden; Test `test_a_crlf_blob_in_head_is_not_reported_as_an_uncommitted_change` mutiert (`if CRLF in committed:` → `if False:`) → rot |
| **F3** Prädikat nur in der Prüfung | **GESCHLOSSEN** | `def repairable` existiert **einmal** (im Werkzeug), `tools/test_repo_hygiene.py:49` importiert es; kein zweites Prädikat und kein eingebauter Pfadtest im Testfile |
| **F4** PID-Satz | **GESCHLOSSEN** | `under_load.py:31` sagt jetzt „immediately AFTER its start … at most the LAST start unrecorded" — das ist genau das, was der Code baut |
| **F5** vier Zahlenkopien | **GESCHLOSSEN** | `grep -c` über die vier ausgelieferten Dateien: **0 / 0 / 0 / 0**; jede nennt stattdessen `test_git_decides_binary_by_bytes_and_pins_every_text_file_to_lf`; die Zahlen stehen nur noch im Protokoll (3 Treffer), in der Löcherliste keiner |
| **F6** „a wider setting is refused" | **GESCHLOSSEN** | gemessen: `refused: exactly <workdir> <label> <cap-seconds> stand before `--`, and ['x','y','60','--burners','16'] is 5 word(s)` |
| **F7** Deckel + Anlauf | **GESCHLOSSEN** | `under_load.py:107` `left = cap - (time.monotonic() - started)`, `started` steht vor dem ersten Brenner; der Anlauf liegt im Deckel |
| **F8** Kill nach Nummer | **GESCHLOSSEN** | kein `os.kill` mehr im Modul; ein stehengebliebener Eintrag **verweigert** |
| **F9** POSIX-Docstring | **GESCHLOSSEN** | `tools/test_office_duties.py:689-694` nennt „Both ends here" ausdrücklich als Windows-Aussage und zitiert die Messung aus Runde 1 |

**Beide selbst gefundenen Gegenlücken des Umsetzers:**

* **Stub-Trennzeichen** — geschlossen und von mir gegen eine **echte** git-Zeile geprüft:
  `git ls-files --eol README.md` liefert `'i/lf    w/lf    attr/text=auto eol=lf \tREADME.md'`
  (Leerzeichen zwischen den Spalten, **ein** Tabulator vor dem Pfad) — dieselbe Form wie der Stub.
  Mit dieser echten Zeile gefüttert liefert `drifted_files()` `['README.md'] []` und für die echte
  Zeile eines kanonischen Pfades `[] ['project_memory/.audit/hook_events.jsonl']`.
* **`sys.dont_write_bytecode`** — aus dem Code entfernt, richtig; die **Begründung** dafür ist aber
  falsch, siehe **R2-3**.

---

## Neue Befunde aus den Fixes

### R2-1 — die beiden Binär-Prüfungen widersprechen sich für genau die Klasse, für die die `binary`-Zeilen da sind
**Schwere: mittel. Nacharbeit, nicht blockierend (die Klasse ist im Baum heute leer).**

`tools/test_repo_hygiene.py:130` liest `handle.read(NUL_WINDOW)` — **die ersten 8000 Bytes**.
Git entscheidet in `ls-files --eol` aber über die **ganze** Datei. Für eine Datei, deren NUL hinter
Byte 8000 steht, fallen die beiden Leser auseinander — und das ist wörtlich die Klasse, für die der
Kommentar in `.gitattributes` die `binary`-Zeilen vorsieht („a binary whose first 8000 bytes happen
to hold no NUL").

Gemessen mit `assets/wide.bin` (8500 Füllbytes, dann ein NUL, dann `tail`), in `r2/applied`
in den Index gelegt:

```
$ git ls-files --eol assets/wide.bin
i/-text w/-text attr/text=auto eol=lf   assets/wide.bin

OHNE Pin:
E AssertionError: git reads these files as binary by their bytes, but no `binary` line in
  .gitattributes covers them ... : ['assets/wide.bin']
  tools\test_repo_hygiene.py:381

MIT dem vorgesehenen Pin `assets/wide.bin binary`:
$ git check-attr text eol -- assets/wide.bin
assets/wide.bin: text: unset
assets/wide.bin: eol: lf
E AssertionError: 1 tracked file(s) carry no NUL in their first 8000 bytes -- text by the rule this
  repo took from git -- and git resolves them to something other than `text: auto` / `eol: lf` ...
  ['assets/wide.bin']
  tools\test_repo_hygiene.py:185
```

Es gibt also **keinen** Zustand von `.gitattributes`, in dem beide Prüfungen für so eine Datei grün
sind: ohne Pin fordert die alte ihn, mit Pin verbietet ihn die neue.

Dazu kommt die Aussage im Docstring der neuen Prüfung (`tools/test_repo_hygiene.py:174-176`):

> „the reverse -- a file git calls binary although its first bytes carry no NUL -- is exactly what
> the `binary` lines are FOR, and it is reported, not failed."

Gemessen wird es **gefailt**, von der Zusicherung neun Zeilen darüber; der Melde-Zweig (`:197`,
`warnings.warn`) feuert zwar wirklich — ich habe ihn für die ungepinnte Fixture gesehen (`1 warning`
im pytest-Kopf) —, aber nur solange die **alte** Prüfung für dieselbe Datei rot ist.

**Minimaler Fix:** die Textseite um das nehmen, was git selbst als binär liest, bevor die erste
Zusicherung greift — z. B. `plain = {p for p in plain if endings.get(p) != "-text"}`. Beide von mir
gemessenen Mutationen (Pin gelöscht, `* binary`) bleiben damit rot, weil Textdateien dort `w/lf`
tragen; die Melde-Zeile bekommt genau die Klasse, die sie laut Docstring melden soll.

### R2-2 — der neue F2-Zweig antwortet auf den Doppelfall mit einem Satz, den `git status` widerlegt
**Schwere: mittel. Nacharbeit, nicht blockierend (Klasse im Repo leer).**

`tools/normalise_line_endings.py:129` prüft `CRLF in committed` **vor** `normalised != committed`.
Sind beide wahr — der Blob trägt CRLF **und** die Arbeitskopie ist zusätzlich von Hand geändert —,
gewinnt der neue Satz, und er ist dann falsch.

Gemessen (`verify/r2attacks.py`, Blob `b"one\r\ntwo\r\n"`, Datei
`b"one\r\ntwo\r\nTHREE-a-real-edit\r\n"`):

```
verdict: the blob HEAD holds carries CRLF itself, so the working tree is not what is wrong here and
`git status` says nothing about this file. The index is what needs rewriting:
`git add --renormalize -- both.md`
```

Der Arbeitsbaum ist sehr wohl (auch) das Problem, `git status` meldet die Datei, und der genannte
Befehl würde die fremde Änderung mit in den Index nehmen. `docs/line-endings.md:70-74` trägt
denselben Fehler und stellt die beiden Fälle ausdrücklich als „welchen der **beiden** Fälle"
gegenüber — als schlössen sie einander aus. Der neue Test (`tools/test_repo_hygiene.py:279`) stellt
die Zweige nur **einzeln** her und kann die Kombination darum nicht sehen.

**Minimaler Fix:** `normalised` gegen `committed.replace(CRLF, LF)` vergleichen; wo auch das
abweicht, beide Gründe nennen und **keinen** der zwei Befehle allein empfehlen. Plus ein vierter
Monkeypatch im genannten Test.

### R2-3 — die Begründung für das entfernte `sys.dont_write_bytecode` nennt einen Test, der dafür nicht rot werden kann
**Schwere: niedrig-mittel. Nacharbeit am Satz; die Entfernung selbst ist richtig.**

`tools/normalise_line_endings.py:45-53` sagt, der Import des Werkzeugs durch die Suite „would set it
inside the pytest process, where `tools/test_hooks.py::test_the_suite_leaves_no_bytecode_in_the_kit_tree`
watches for exactly that."

Gemessen — Flag zurück ins Werkzeug gesetzt:

```
before import: False
after  import: True
$ pytest -q tools/test_hooks.py tools/test_repo_hygiene.py -k "leaves_no_bytecode or line_ending_sweep"
2 passed, 986 deselected in 4.15s
```

Der genannte Test sichert `sys.pycache_prefix == conftest.PYCACHE_DIR` und die **Abwesenheit** von
`__pycache__` unter `team-kits/`. Ein gesetztes `dont_write_bytecode` unterdrückt Bytecode
vollständig — es macht diese Zusicherung also **leichter**, nie rot. Der Satz behauptet einen
Stolperdraht, den es für diese Eigenschaft nicht gibt (Hausregel: eine genannte Prüfung muss fallen
können).

**Minimaler Fix:** entweder die Klausel streichen (das Werkzeug importiert nur die Standardbibliothek,
das Flag kauft nichts — das allein trägt die Entscheidung), oder dem genannten Test eine Zeile
`assert not sys.dont_write_bytecode` geben, dann stimmt der Satz.

---

## Ausdrückliche Negativ-Befunde

### Gemessen

**Patch / Übergabe.** 10 Dateien, alle im `allowed_scope`; **keine** VERSION-Hunks; 82 987 B,
**0** CR; `git apply --check` gegen einen frischen `75a00d1`-Klon → `rc=0`; alle 13 geänderten
Worktree-Dateien CR-frei. `test_gates.py` per `ast`: `added: []`, `removed: []`, `changed:
['test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge']`. Löchernummern
im Patch: **nur** `H160`, `H161`, `H162`.

**AC-1.** Der ausführbare Teil beider Fixes ist unverändert (nur der F9-Docstring kam dazu). Drei
Knoten erneut gefahren: Windows `2 passed`; Linux (WSL, Windows-`pytest` über `PYTHONPATH`)
`1 passed`; über einen echten zweiten Mount (`--basetemp=//localhost/C$/…`) `1 passed`.

**AC-2, F1-Fix.** Beide vom Umsetzer genannten roten Zeilen selbst gesehen (oben). Zusätzlich:
* Ein gewöhnlicher Textbaustein binär gepinnt (`README.md binary`) → **beide** Prüfungen rot
  (`:185` mit 13 `README.md`-Pfaden, `:388` „drop them: ['README.md']"). Richtiges Verhalten.
* Die alte Zweiender-Falle hält auf dem neuen Paket weiterhin in beiden Richtungen:
  `*.png binary` entfernt → 496 ungedeckte Dateien; `*.zzz binary` ergänzt → `['*.zzz']`.
* **Arbeitsbaum-Abhängigkeit geprüft:** ein CRLF-Arbeitsbaum (`README.md` auf `w/crlf`) lässt die
  neue Prüfung **grün** — sie liest Attribute, nicht den Baum. Ein NUL in einer verfolgten
  Textdatei lässt die neue Prüfung grün und macht die **alte** rot (die bekannte Klasse aus
  Runde 1, unverändert).
* Ein Pfad, der auf ein Text- **und** ein Binärmuster passt (`*.png` gegen `*`), ist der heutige
  Normalfall und grün.

**AC-2, F3-Fix.** `repairable` ist einmal definiert; die Auflistung der unerreichbaren Dateien
erscheint in **beiden** Pfaden. Gemessen in `r2/applied` mit CRLF in zwei verfolgten Dateien:

```
=== CHECK PATH (dry run):
1 file(s) are NOT this tool's to repair -- canonical state, which no tool write reaches (gate 1) ...
  project_memory/.audit/hook_events.jsonl
1 file(s) would be normalised (run with --apply):
  docs/backlog-structure-and-dedup.md

=== APPLY PATH:  (dieselbe Auflistung) 1 file(s) normalised: docs/backlog-structure-and-dedup.md
--- danach noch w/crlf: project_memory/.audit/hook_events.jsonl
```

Die kanonische Datei bleibt unangetastet, die Prüfung wird grün mit Warnung. Damit ist der
Runde-1-Befund F3 nicht nur im Satz, sondern im Verhalten geschlossen.

**Rot-Zuerst für die beiden neuen Tests, von mir hergestellt.** `if CRLF in committed:` → `if False:`
und die Aufteilung in `drifted_files` entfernt:
`test_a_crlf_blob_in_head_is_not_reported_as_an_uncommitted_change` rot (`:301`),
`test_the_remedy_leaves_canonical_state_to_the_place_that_writes_it` rot (`:336`); zurückgesetzt
`5 passed`.

**AC-3.** `team-kits/kernel/kitupdate.py` ist gegenüber Runde 1 unverändert; die vier
Gedächtnis-Knoten inkl. echtem Piloten `4 passed` (19,4 s).

**AC-4.** Der Gate-3-Knoten und der Namensprüf-Knoten `2 passed` (29,6 s). Sechs Rig-Verweigerungen,
alle an einer eigenen Kopie und mit PID-Sicherheitsnetz, kein Brenner, keine Berichtsdatei:
kein Fenster; kein `--`; überzähliges Wort vor `--`; `cap 300`; gültige Argumente aber
stehengebliebene PID-Datei; falsches Arbeitsverzeichnis. Die Fensterdatei des Leads unter
`_round-scratch/TSK-0125/` blieb die ganze Runde **abwesend** (geprüft).

**Zur F8-Frage nach einer toten PID:** eine PID-Datei mit `9999999` (existiert nicht) wird
**verweigert**, nicht bereinigt — und genau das sagt der Docstring („does NOT kill what it finds
there. It REFUSES, prints the pids and stops"). Eine **leere** PID-Datei verweigert ebenfalls, mit
„pid(s) (none recorded)". Satz und Code stimmen überein. Preis, benannt und gewollt: ein
abgeschnittener Lauf blockiert das Rig, bis ein Mensch die Datei löscht.

**F5-Ersatz kann rot werden.** Die beiden Eigenschaftstests, die die vier Zahlenkopien ersetzen,
sind je einmal mutiert und rot gesehen (oben: Pin gelöscht bzw. `* binary`; `*.png`-Pin entfernt bzw.
`*.zzz` ergänzt).

**Suiten (nachgerechnet, nicht wiederholt).** `tools/test_repo_hygiene.py` in einem Klon **mit**
`.git`: **31 passed** (112,8 s) — deckt sich mit der Meldung. `ruff check .` → `All checks passed!`;
`tools/validate.py` → `all structural checks passed`; `tools/bump_kit_version.py` → alle drei
`unchanged`.

**Die Beobachtung des Koordinators bestätigt und eingeordnet.** In einer Kopie **ohne** `.git`
fallen `test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom` und
`test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at` hart. Ich habe das an
`base-nogit` gemessen — **pristine `75a00d1`, ohne eine Zeile dieses Stroms** — mit demselben
Ergebnis (`2 failed`). Es ist geerbt. Die drei **neuen** git-abhängigen Knoten dieses Stroms rufen
`_require_git()` und überspringen sauber: `SKIPPED [3] tools\test_repo_hygiene.py:1356: not a git
work tree`.

### Nicht gemessen

* **Die Last-Hälfte von AC-4 (`H162`).** Fenster geschlossen; kein Brenner gestartet. Damit sind
  auch die Zahlen eines echten Lastlaufs weiter unbekannt.
* `tools/test_kitupdate.py` als Ganzes (gemeldet `86 passed, 1 skipped`) — nur die vier
  Gedächtnis-Knoten gefahren.
* Die weiteren gemeldeten Suitenläufe (`+ test_reference_skills 49`,
  `test_office_duties + test_ci_lint_pinned + test_context_budget 85`, `Linux 68`) — je nur die
  betroffenen Knoten gefahren.
* `.claude/hooks/test_gates.py` als Ganzes.
* Die **Nachher-Richtung von AC-1**: der nächste gehostete Lauf, Push des Nutzers.
* Der Merge-Schritt `--apply` im Haupt-Checkout (in einem Klon gemessen, nicht im Repo).
* Die volle Suite (DEC-0050 — gehört dem Merge).

---

## Was in die Nacharbeit gehört

**Nacharbeit vor dem Merge, klein:** R2-1 (eine Zeile in `_binary_by_bytes` bzw. vor der ersten
Zusicherung, damit die `binary`-Zeilen wieder legbar sind, plus der Satz in `:174-176`),
R2-2 (ein Vergleich gegen den normalisierten Blob und ein vierter Monkeypatch im Test, plus
`docs/line-endings.md:70-74`), R2-3 (Klausel streichen oder dem genannten Test eine Zeile geben).

**Keine neue Löchernummer nötig:** R2-1 und R2-2 sind Nacharbeit, keine offenen Lücken; H160–H162
bleiben wie sie sind.

**Merge-Vorbedingung, unverändert:** `python tools/normalise_line_endings.py --apply` im
Haupt-Checkout, sonst ist die Prüfung dort rot.

---

## Urteil

**FAIL — zweite Nacharbeit, klein, nichts blockierend.** Die Nacharbeit 1 hat gehalten, was sie
sagt: alle neun Befunde aus Runde 1 sind geschlossen, und ich habe jeden davon selbst nachgemessen
statt ihn abzuhaken — die tragende `.gitattributes`-Zeile fällt jetzt mit 1278 benannten Dateien,
wenn man sie löscht; Prüfung und Abhilfe teilen ein Prädikat, und `--apply` lässt die kanonische
Auditdatei nachweislich liegen statt sie nur zufällig zu verfehlen; das Rig verweigert ein
Knob-Wort, einen zu großen Deckel, ein fremdes Verzeichnis und eine stehengebliebene PID-Liste, ohne
je einen Brenner zu starten. Drei Sätze sind bei der Reparatur neu entstanden oder stehen geblieben,
und einer davon ist mehr als ein Satz: die neue Prüfung liest 8000 Bytes, git liest die ganze Datei,
und für eine Binärdatei, deren NUL dahinter liegt, fordert die eine ausgelieferte Prüfung genau die
`binary`-Zeile, die die andere verbietet — gemessen an einer Fixture, in beiden Richtungen, mit
`file:line`. Heute trägt der Baum keine solche Datei, deshalb ist es Nacharbeit und kein Blocker;
aber es ist der Fall, für den die Zeilen überhaupt existieren, und der Docstring sagt darüber
„reported, not failed", während der Code failt. Eine Zeile Code, zwei Sätze, ein vierter
Monkeypatch — dann ist das Paket abnahmefähig, und die Last-Hälfte bleibt `H162` und wartet auf das
Fenster des Leads.
