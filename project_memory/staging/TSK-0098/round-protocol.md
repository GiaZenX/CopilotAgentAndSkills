# TSK-0098 / FR-0058 — Rundenprotokoll (Umsetzer): H80 schliessen

Datum: 2026-08-31 · Rolle: `harness-implementer` · Arbeitsverzeichnis ausserhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0098\`

Auftrag: H80 schliessen (Haerten von `gate_lead_write_scope` plus Registrierung des
Freigabe-Hakens), H80/H39 ehrlich nachfuehren, die `/cd`-Frage so weit messen, wie sie ohne
interaktive Sitzung messbar ist. `team-kits/**` unberuehrt — kein Kit-Stempel.

Dieses Protokoll ist die Fassung NACH zwei Pruefrunden. Die erste Fassung der Haertung war zu
klein: zwei unabhaengige Pruefer haben sie mit je eigenen Ketten bis `APPROVED` widerlegt, und eine
dritte Luecke habe ich beim Nachmessen selbst gefunden. Kapitel 4 fuehrt jede einzeln.

## 1. Der Schnitt, und warum er nicht der Kit-Schnitt ist (gemessen)

Der benannte Schluss aus H80 lautete: eine Stufe, die eine Datei aus einem GESCHUETZTEN Baum
ausfuehrt, ist schreibfaehig. Wortwoertlich uebernommen ist das hier eine Stilllegung. Gemessen
(`probe_lines.py`, echte Hook-Prozesse, Wegwerf-Projekt, dieselbe Zeile gegen `gate_write_scope`
der Kits und gegen `gate_lead_write_scope`):

| Zeile dieses Repos | Kit-Regel | Gate 1 vorher | Gate 1 nachher |
|---|---|---|---|
| `python tools/bump_kit_version.py` | rc 0 | rc 0 | **rc 0** |
| `python tools/validate.py` | rc 0 | rc 0 | **rc 0** |
| `python -m ruff check .` | rc 0 | rc 0 | **rc 0** |
| `python -B -m pytest tools/ -q` | rc 0 | rc 0 | **rc 0** |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **rc 2** | rc 0 | **rc 0** |
| `PYTHONPATH=team-kits python -B -m kernel.cli … generate-index` | **rc 2** | rc 0 | **rc 0** |
| dieselbe Zeile in PowerShell-Schreibweise | **rc 2** | rc 0 | **rc 0** |
| `… kernel.cli … request-approval scope BUG-0001` | **rc 2** | rc 0 | **rc 0** |
| `git status --short` | rc 0 | rc 0 | **rc 0** |

Die Spalte „Kit-Regel" ist die Messung, aus der der Schnitt folgt; die Zahl, die H80 daraus nennt,
steht dort und nicht ein zweites Mal hier.

> Eine Befehlszeile hat eine **START-Position** — die Datei, die eine Stufe ausfuehrt. Sie ist ein
> eigener Gegenstand (`_harness.Executed`), und `ProtectedArea.hand_driven` beurteilt sie gegen die
> **Haken-Verzeichnisse**: den Provider-Baum dieses Repos plus das `hooks/`-Verzeichnis jedes Kits,
> abgeleitet ueber `_harness.kit_hooks_directories` (Kit-Begriff aus `kernel.hashing.is_kit_dir`,
> Haken-Verzeichnis = „liefert `_compat.py`", dieselbe Ableitung, die `_kit_hooks_dir` schon nutzte
> und die dabei von einer Aufzaehlung-von-einem befreit wurde).

Verweigert wird die Position **jedem Aufrufer**. Begruendung, die auch im Code steht: wer
Durchsetzungscode AENDERN darf, ist die Frage des Aenderungskreises (ein Subagent darf es); wer den
**Provider spielen** darf, ist keine Rollenfrage. TSK-0097 hatte den Selbst-Mint fuer beide
Aufrufer rc 0 gemessen.

Was die Position **nicht** liest, und das ist der Kern des Schnitts: was ein gestartetes Programm
schreibt. Das steht seit je als H11 und gilt weiter — `python tools/bump_kit_version.py` startet
eine Datei, die Gate 1 SCHUETZT, und bleibt rc 0.

## 2. Wo in einer Zeile ein Programm anfaengt — die Antworten, die heute im Code stehen

`_harness._executed_words` und `_command_positions`:

1. **Der Verb-Platz, aber nur mit Trennzeichen** (`_verb_as_a_file`). Ein trennzeichenloses Verb
   sucht eine Shell ueber `PATH`, nie gegen das Arbeitsverzeichnis.
2. **Die Operanden eines Interpreters**, gefragt an seinem OPTIONSTEIL statt an allem dahinter
   (`_option_part`).
3. **Der Interpreter, den ein Wrapper oder eine zweite Shell startet** — nur in einer Stufe, die
   der Leser nicht als lesend einstuft (`_command_positions`); genau diese Bedingung laesst
   `grep -rn python .claude/hooks/` frei.
4. **Jeder Operand einer Stufe, deren Verb der Leser gar nicht benennen kann** — der fail-closed
   Rest, und die Antwort auf PowerShells Aufrufoperator.
5. **Ein Interpreter, dem ein anderes Programm sein Programm aus einer Datei reicht**
   (`_handed_a_program_from_elsewhere`), begrenzt auf den Fall, in dem der Interpreter NICHT das
   Verb der Stufe ist — steht er vorn, liest er sein Programm von stdin, und dann ist der Kanal
   belegt, den der Haken fuer seine Nutzlast braucht (gemessen: `cat <hook> | python` praegt nicht).
6. **Ein Verb, das erst zur Laufzeit feststeht** (`_resolves_the_verb_at_runtime`).
7. **Die Woerter hinter einer schliessenden Klammer, die diese Stufe nie geoeffnet hat**
   (`_after_an_unopened_closer`) — eine Ersetzung mit einem `;` darin wird mittendurch geschnitten,
   und das letzte Stueck traegt dann den Schluss plus die Woerter der aeusseren Stufe, mit dem Verb
   der INNEREN davor.

Daneben zwei Antworten, die **nicht** in der START-Position sitzen und **beide Richtungen** treffen:

* **Ein Wort, das die Shell erst baut, ist unplatzierbar** (`_UNRESOLVED` = `$ * ? [ {`) — dieselbe
  fail-closed-Antwort wie beim Tilde-Praefix, **aber nur gefragt, wo das Wort ueberhaupt einen Pfad
  benennen koennte** (`_could_name_a_path`: mit Trennzeichen, oder an einer Programmstelle). Ohne
  diese zweite Haelfte war `[ $i -ge 3 ]` rc 2 — also jede Warteschleife, mit der diese Runde ihre
  eigenen Hintergrundlaeufe abgefragt hat, und die der Auftrag selbst vorschreibt. Selbst getroffen
  und selbst gemessen.
* **Eine Bewegung INNERHALB einer Zeile, die an eine zweite Shell geht, kostet die Position**
  (`_moves_inside_an_inline_program`).

**Drei Zweige wurden durch Ablation gemessen statt geglaubt, und zwei davon sind raus:** die
Sonderbehandlung „Interpreter hinter einem `-c`-Buendel" (sie feuerte nur noch auf LESENDE Stufen
und erzeugte dort ausschliesslich Ueber-Verweigerungen wie `grep -c python <hook>`) und „ein Wort
von einem Zeichen ist Satzzeichen, keine Konstruktion" (unerreichbar, seit `_could_name_a_path`
davorsteht). Der dritte, „Verb ist eine Kommandoersetzung", war nach der ersten Ablation ebenfalls
raus — und musste zurueck, als `_unresolved_at` aufhoerte, fuer ein einzelnes `$` zu antworten.
Das ist die Lehre, die im Docstring steht: ein Zweig ist nur gegenueber dem Leser NEBEN ihm
unerreichbar, und wenn einer von beiden sich bewegt, sind beide neu zu messen.

## 3. Die Kette jetzt (gemessen, `battery.py`, 63 Formen × Bash/PowerShell × Lead/Subagent)

Alles, was den Haken startet, ist **rc 2 in allen vier Spalten**. Die Formen, die vorher
durchliefen, nach Befund geordnet:

| Befund | Form | vorher | jetzt |
|---|---|---|---|
| B1 | `python <hook> -c` / `-m` / `-abc` / `-M` (Kontrolle `-x`: schon vorher 2) | 0 | **2** |
| B2/Z1 | `"$PWD/<hook>"`, `"${PWD}/<hook>"`, `"$(pwd)/<hook>"`, `H=…; python $H` | 0 | **2** |
| Z1 | `te*m-kits/…`, `.cla*de/…`, `…gate_approva?.py`, `…[l].py`, `{dev-team,office-team}` | 0 | **2** |
| B3 | `timeout 60 python <hook>`, `nohup …`, `stdbuf -o0 …`, `echo <hook> \| xargs python` | 0 | **2** |
| B3 | `echo <hook> > list.txt; xargs -a list.txt python` (**hat gepraegt**) | 0 | **2** |
| B3-Rest | `sh -c "cd <hooks> && python gate_approval.py"` (**hat gepraegt**) | 0 (sub) | **2** |
| selbst | `& ('pyt'+'hon') <hook>` (PowerShell-Aufrufoperator) | 0 (sub) | **2** |
| B2 (Schreiben) | `sed -i "s/a/b/" "$PWD/team-kits/kernel/state.py"` | 0 (**auch Lead**) | **2** |
| selbst | `$(printf 'pyt'; printf 'hon') <hook>` (Ersetzung mit `;`, mittendurch geschnitten) | 0 | **2** |
| Kontrolle | `find -exec`, `eval`, `HOOK=… python $HOOK` | 2 | **2** |

Und die Gegenrichtung, alles rc 0 geblieben oder rc 0 GEWORDEN: die neun Tageszeilen aus Kapitel 1,
dazu `cat`/`diff`/`grep -rn`/`ruff` auf Haken, `git add -A`, `python probe.py`,
`python -W ignore tools/validate.py`, `python - <<'PY'`, `python --version`,
`cat probe.py | python`, `ls team-kits/dev-team/hooks`, `git add .claude/settings.json` und die drei
Zeilen aus einem Haken-Verzeichnis heraus (`cd .claude/hooks && cat _harness.py`, `&& ls`,
`cd team-kits/dev-team/hooks && grep -rn python .`), die die erste Fassung faelschlich verweigert
hatte.

## 4. Die drei Luecken der ersten Fassung, jede mit ihrer Ursache

**B1 — die Optionsfrage lief ueber die Argumente des Skripts.** „Faehrt diese Stufe ein Modul?"
wurde an ALLES hinter dem Interpreter gestellt, also auch an die Argumente des gestarteten Skripts.
Ein einziges Ein-Strich-Wort mit `c` oder `m` dahinter loeschte den Operanden-Scan. Der Haken liest
kein `sys.argv`, das Zusatzwort war also folgenlos. Gebaut: `_option_part` — alles bis zum ersten
Operanden. Die Fehlrichtung, die bleibt, ist die sichere: ein Flag mit eigenem Wert
(`python -W ignore -m pytest x`) beendet den Optionsteil am WERT, ein `-m` dahinter wird nicht
gesehen, und dann wird eine Refusal zu viel erzeugt statt eine zu wenig.

**B2/Z1 — ein Wort, das die Shell erst baut.** `_PATHISH` traegt keines der Zeichen `$ * ? [ {`,
also war der pfadartige Teil von `$PWD/team-kits/x` die Zeichenkette HINTER der Expansion — und die
beginnt mit einem Trennzeichen, las sich also absolut und landete unter keinem geschuetzten Baum.
Gebaut: `_unresolved_at` + `_cannot_resolve_the_word`, dieselbe `Unplaceable`-Antwort wie beim
Tilde-Praefix, **im `_candidates`**, durch das beide Positionen laufen. Damit ist die
**Schreib-Haelfte mit geschlossen**, die seit dem Bau der Shell-Haelfte offen war. Quotierung wird
hier bewusst NICHT gelesen: die vier Konstruktionen werden verschieden quotiert (`$` erweitert auch
in doppelten Anfuehrungszeichen, die anderen nicht), und ein Leser, der das in einer Richtung falsch
hat, ist teurer als eine Refusal zu viel.

**B3 — ein Wrapper-Verb versteckte den Interpreter.** Gebaut: `_command_positions` mit der
Lesend-Bedingung. Das frueher hier stehende Argument („nur hinter einem `-c`-Buendel, sonst wuerde
`grep -rn python …` verweigert") war falsch begruendet: was einen Lesebefehl frei laesst, ist die
Einstufung des VERBS, nicht die Stelle des Wortes. Nachgezogen.

**Selbst gefunden, nicht gemeldet — PowerShells Aufrufoperator.** `& ('pyt'+'hon') <hook>`: der
Leser errechnet als Verb `pyt+hon`, kein Wort der Stufe ist ein Interpreter, die Stufe ist nicht
lesend. Mit echtem `powershell.exe` als Schiedsrichter gemessen: die Zeile startet das Programm
wirklich (waehrend `@('pyt'+'hon') x`, `$(('pyt'+'hon')) x` und `@(python) x` auf diesem Host
**Syntaxfehler** sind und gar nichts starten — deshalb steht keine von ihnen in einer Tabelle).
Gebaut: Punkt 4 aus Kapitel 2.

## 4a. Die dritte Pruefrunde: die native Subshell

Der Pruefer fand EINE Ursache mit zwei Loechern. `( … )` erhoeht die Gruppentiefe;
`_runs_in_the_shell_itself` folgt einem `cd` bei Tiefe > 0 bewusst nicht — richtig fuer den
ELTERNPROZESS —, aber die Befehle INNERHALB derselben Klammer wurden weiter gegen die unbewegte
Elternbasis aufgeloest. Gemessen, jede Zeile flach rc 2 und in Klammern rc 0:

| Richtung | Form | vorher | jetzt |
|---|---|---|---|
| START | `(cd <hooks> && python gate_approval.py)` (**hat gepraegt**) | 0 | **2** |
| START | dasselbe mit `;`, mit Leerzeichen, mit stdin-Umleitung | 0 | **2** |
| START | geschachtelt `(cd team-kits && (cd dev-team/hooks && python …))` | 0 | **2** |
| START | hinter einer Pipe `true \| (cd <hooks> && python …)` | 0 | **2** |
| START | im Hintergrund `(cd <hooks> && python …) &` | 0 | **2** |
| SCHREIBEN | `(cd .claude/hooks && rm gate_todo_items.py)` | 0 (**jeder** Aufrufer) | **2** |
| SCHREIBEN | `(cd .claude/hooks && sed -i … gate_todo_items.py)` | 0 | **2** |
| SCHREIBEN | `(cd project_memory && sed -i … bugs/active/BUG-nnnn.yaml)` | 0 | **2** |
| SCHREIBEN | `(cd team-kits && sed -i … kernel/state.py)` | 0 (Lead) | **2** (Lead), 0 (Sub, wie flach) |

Die Schreib-Haelfte war **vorbestehend**: gegen `HEAD` gemessen ebenfalls rc 0, also nicht von
dieser Runde eingefuehrt. Sie ist die duale Kehrseite von **H27** (der Schreibzugriff AUSSERHALB
der Klammer) und steht dort jetzt mit Kette, Datum und Urteil.

**Gebaut ist ein SCOPE, keine Verweigerung.** `WorkingDirectory.follow` geht in die Gruppe mit
(`_open_scope`), `settle` bringt die Basis zurueck, sobald eine spaetere Pipeline auf kleinerer
Tiefe steht. Der vom Pruefer vorgeschlagene Minimalfix — die Position verlieren wie bei einer
Bewegung in einer fremden Shell — haette `(cd tools && python bump_kit_version.py)` verweigert,
also eine Lieferzeile dieses Repos; gemessen, deshalb der Scope.

Zwei weitere Leser mussten dafuer mit, beide beim Messen gefunden:

* `_walk` bekommt die Pipeline **ab dem Verb**. Mit der Klammer davor las es `cd` selbst als Ziel
  (`<basis>/cd`), konnte das nicht betreten und gab die Position auf — der Grund, warum die erste
  Fassung des Scopes die Subshell-Zeilen zwar verweigerte, aber aus dem falschen Grund.
* `_after_an_unopened_closer` antwortet nicht mehr fuer eine schliessende Klammer, hinter der
  **nichts** steht. Die letzte Pipeline einer Subshell endet genau so
  (`['python', 'gate_approval.py', ')']`), und die Antwort lieferte eine leere Operandenliste — der
  Haken stand danach in gar keiner Position.
* `_the_move_in_a_later_stage` findet ein `cd`, das in der EMPFANGENDEN Stufe einer Pipe steht.

**Reihenfolge-Befund beim Bauen, selbst gemessen:** die Suche nach einem Verb in einer spaeteren
Stufe stand zuerst VOR der Frage, ob die Zeile ueberhaupt an eine fremde Shell geht — und nahm
damit dem `sh -c "cd <hooks> && …"`-Fix seinen Zweig weg (2 → 0 fuer den Subagenten). Die Frage
nach der fremden Shell steht jetzt zuerst.

**Gegenrichtung, alles rc 0 geblieben:** `(cd docs && cat note.md)`,
`(cd tools && python bump_kit_version.py)`, `(cd .claude/hooks && cat _harness.py)`,
`(cd /c/tmp && ls)`, die Kernel- und Suite-Zeile in einer Gruppe, `(ls && cat docs/note.md)`,
eine Warteschleife in einer Gruppe — und die beiden Zeilen, die zeigen, dass die Gruppe wieder
VERLASSEN wird: `(cd <hooks> && ls) && cat docs/note.md` und
`(cd team-kits && ls) && sed -i "s/a/b/" docs/note.md`.

**Befund 3 (m18), messend entschieden: der Zweig ist NICHT tot.** Er wird nur nicht von der
PowerShell-Zeile erreicht — die kommt ueber `_after_an_unopened_closer` in die Position. Ablation
ueber beide Batterien: ohne den Zweig fallen `sed -i … <hook-datei>`, `rm <hook-datei>` und die
Subshell-Formen davon von 2/2 auf **2/0**, also die Aussage „keine Shell-Zeile pflegt eine
Haken-Datei". Sein Subjekt ist die SCHREIB-Haelfte, und m18 zeigt seit dieser Runde dorthin
(`test_gate1_refuses_maintaining_a_hook_file_from_a_shell`).

## 5. Die zweite Haelfte: der ehrliche Weg existiert

`.claude/settings.json` registriert den Freigabe-Haken der Kits auf **beiden**
`AskUserQuestion`-Ereignissen (die Kits paaren sie; `PreToolUse` verhindert, `PostToolUse` muenzt),
mit `timeout: 120`, ueber `${CLAUDE_PROJECT_DIR}` gebildet.

**Messend entschieden — Kit-Datei statt Kopie oder Wrapper.** `approvals._assert_minting_caller`
nimmt den Haken nur an, wenn er als er selbst neben seinem eigenen `_kernel.py` laeuft. Gemessen
(`probe_approval.py`): der Haken der Kits laeuft aus der Kit-Ablage dieses Repos heraus fehlerfrei,
markerlose Fragen rc 0 ohne Ausgabe, direkt gestartet wie ueber `_gate.py`. Eine Kopie unter
`.claude/hooks/` muesste `_kernel.py` mitbringen, ein Wrapper muesste nachbauen, was `_gate.py`
schon kann. Die eine Kit-Nennung, die eine statische JSON-Datei nicht ableiten kann, traegt einen
Stolperdraht: `test_the_approval_hook_is_the_kits_own_file_where_it_ships` haelt den registrierten
Pfad gegen `_harness.kit_hooks_directories`.

**Ende zu Ende in einer Wegwerf-Kopie** (`probe_mint.py`):

| Stufe | vorher | nachher |
|---|---|---|
| `report.approval_mint_is_wired` | `False` | **`True`** |
| `request-approval scope BUG-0001` | rc 0 **+ Warnung auf stderr** | rc 0, **keine Warnung** |
| wortgleiche Weiterreichung, `PreToolUse` | — | **rc 0** |
| umformulierte Weiterreichung, `PreToolUse` | — | **rc 2**, „question differs" |
| Antwort der Plattform, `PostToolUse` | — | `approval APR-0001 recorded for BUG-0001` |
| Item danach | `TRIAGED` | **`APPROVED`, `approval_ref: APR-0001`** |
| `transition BUG-0001 APPROVED` von Hand | rc 1 + „nichts liest hier die Antwort" | rc 1, „illegal transition APPROVED → APPROVED" — die Antwort ist die Kante schon gegangen |

**Nicht gemessen und nicht behauptet:** ein echter Klick eines echten Nutzers. Die `answers`
schreibt in einer Sitzung die Plattform; die Sonde hat sie in der Kopie selbst gesetzt. Belegt ist
der MECHANISMUS.

Gegen den echten Speicher dieses Repos: `report.approval_mint_is_wired` = **`True`** (H81-relevant:
der Projektpfad hat ein Leerzeichen, die Registrierungszeile nicht).

## 6. Die `/cd`-Frage: was messbar war und was nicht

* **Gemessen:** eine frische kopflose Sitzung startet mit der neuen Registrierung sauber —
  `claude -p` (CLI **2.1.251**), `subtype: success`, `permission_denials: []`, kein
  Hook-Konfigurationsfehler.
* **Gemessen:** `approval_mint_is_wired` = `True`, und die Registrierung parst
  (`test_the_registration_is_the_one_the_contract_asks_for` liest die Datei, die der Provider liest).
* **Nicht messbar, und gemessen WARUM:** `AskUserQuestion` steht in einer `claude -p`-Sitzung
  **nicht zur Verfuegung** (`ask_probe.py`: „weder in der Werkzeugliste noch unter den nachladbaren
  Werkzeugen"). Ohne Nutzer gibt es das Ereignis nicht, das der Haken liest.
* **Offene Haelfte:** ob `/cd` eine laufende Sitzung an die neue Registrierung bindet, ist von hier
  aus nicht messbar. **Der sichere Weg ist der Neustart**; der Versuchsaufbau steht in Kapitel 9.

## 7. Rote Tests (Mutation im Klon **ausserhalb** des Repos, `mut/`, `mutate.py`)

Jede Mutation wird gesetzt, die Auswahl gefahren, zurueckgesetzt.

| Defekt wiederhergestellt | Testauswahl | Lauf |
|---|---|---|
| **m0**: beide Hook-Dateien auf `HEAD` | `starting_a_hook or minted_an_approval` | **1 error** (das Modul sammelt nicht mehr) |
| **m1**: START-Position entfernt | die neuen Tests | **79 failed**, 46 passed |
| **m4**: Audienz `SESSION_ONLY` statt `EVERYONE` | `starting_a_hook and subagent` | **40 failed** |
| **m5**: `-m`/`-c`-Ausnahme entfernt (Gegenrichtung) | `startable` | **1 failed** |
| **m6**: Registrierung entfernt | Registrierung/Mint/Kit-Datei | **3 failed** |
| **m7**: Registrierung zeigt auf eine Kopie unter `.claude/hooks/` | `approval_hook_is_the_kits` | **1 failed** |
| **m8**: tote Startform in `START_SHAPES` | `start_shape` | **1 failed** |
| **m9**: Optionsfrage ueber alles hinter dem Interpreter (B1) | `option-looking` | **8 failed** |
| **m10**: Unplatzierbarkeit der Shell-gebauten Woerter entfernt (B2/Z1) | `cannot_resolve` | **20 failed** |
| **m11**: Wrapper-Zweig entfernt (B3, Gegenrichtung) | `wrapped_module` | **1 failed** |
| **m12**: jedes Verb ist eine Datei im cwd (N1) | `bare_verb` | **4 failed** |
| **m13**: Gleichheit zaehlt als „inside" (Z3) | `directory_as_a_started_file` | **1 failed** |
| **m14**: Bewegung in einer inneren Zeile unsichtbar | `moves` | **4 failed** |
| **m15**: Interpreter ohne Programm ist kein Gegenstand | `built` | **8 failed** |
| **m16**: `PreToolUse`-Haelfte der Registrierung geloescht (N3) | `registration_is_the_one` | **1 failed** |
| **m17**: tote Form in `UNRESOLVED_WORDS` | `unresolved_word_really_changes` | **1 failed** |
| **m18**: „Verb nicht benennbar" ist kein Start (die Schreib-Haelfte, s. Kapitel 4a) | `maintaining_a_hook` | **5 failed** |
| **m19**: eine mittendurch geschnittene Ersetzung versteckt die aeusseren Woerter | `cut` | **8 failed** |
| **m20**: die Unplatzierbarkeit wird jedem Wort gestellt (die Warteschleifen-Sperre) | `variable_that_names_no_path` | **2 failed** |
| **m22**: eine Bewegung in einer Gruppe bewegt den Leser nicht | `starting_a_hook and subshell` | **40 failed** |
| **m23**: `_walk` bekommt die Pipeline mitsamt der Klammer (Gegenrichtung) | `comes_back_out` | **1 failed** |
| **m24**: eine schliessende Klammer am Zeilenende verschluckt die Operanden | `starting_a_hook and subshell` | **32 failed** |
| **m25**: eine Gruppe hinter einer Pipe versteckt ihr eigenes `cd` | `starting_a_hook and receiving` | **8 failed** |
| zurueckgesetzt | alle | **184 passed** |

**m3 und m21 sind ausgelaufen und das ist ein Befund, kein Versehen:** beide Zweige wurden als
unerreichbar entfernt (Kapitel 2, letzter Absatz). Eine Mutation, die nichts mehr rot macht, ist ein
Zeiger auf toten Code. **m2 ist der Gegenfall:** ausgelaufen, entfernt — und zurueckgeholt, als der
Leser daneben sich bewegte.

## 8. Laufzeit von Gate 1: vorher/nachher

`probe_timing.py`, zwei Stand-ins aus demselben Bauplan, der eine mit den Hook-Dateien aus `HEAD`
(`git show`, nur lesend), 12 Laeufe je Nutzlast, derselbe Hostzustand — nach der ganzen Nacharbeit:

| Nutzlast | HEAD min/mittel/max | Arbeitsbaum min/mittel/max |
|---|---|---|
| `Write`-Nutzlast | 0.21 / 0.23 / 0.30 s | 0.21 / 0.23 / 0.29 s |
| `python tools/bump_kit_version.py` | 0.20 / 0.23 / 0.31 s | 0.20 / 0.23 / 0.35 s |
| Kernel-Zeile | 0.21 / 0.22 / 0.25 s | 0.21 / 0.22 / 0.26 s |
| `pytest .claude/hooks/test_gates.py` | 0.21 / 0.23 / 0.28 s | 0.21 / 0.24 / 0.32 s |
| lange Zeile (drei Stufen) | 0.20 / 0.33 / 0.74 s | 0.20 / 0.23 / 0.24 s |

Kein messbarer Aufschlag; die Mittelwerte liegen innerhalb von 0.01 s. Die Registrierung gibt Gate 1
120 s, die Reserve ist `max(0.2·120, 1.5) = 24 s`.

## 9. Was der Nutzer tun muss (und was er pruefen kann)

**Neustart der Sitzung.** Hook-DATEIEN liest der Provider bei jedem Aufruf frisch (in dieser Runde
selbst erlebt — die neue Verweigerung traf eine eigene Messzeile, bevor irgendetwas neu gestartet
war), die **REGISTRIERUNG** bindet beim Sitzungsstart. Bis zum Neustart gilt: die Haertung wirkt
bereits, der Freigabe-Haken noch nicht.

Wer statt eines Neustarts `/cd` versuchen will:

1. In der laufenden Sitzung `/cd` in ein anderes Verzeichnis und wieder zurueck in
   `C:\Offline Repos\AgentAndSkills`.
2. `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory request-approval scope
   BUG-0075`, die gedruckte Frage **wortgleich** weiterreichen.
3. Auf die Frage die Option `Freigeben [<code>]` waehlen.
4. Ergebnis lesen: entsteht **`project_memory/approvals/APR-nnnn.yaml`** (dort schreibt der Kernel
   sie — ein `active/` gibt es unter `approvals/` nicht) und steht BUG-0075 danach auf `APPROVED`,
   hat `/cd` die Registrierung nachgezogen. Sonst: Neustart.

Beides ist ungefaehrlich: der `Aendern`/`Ablehnen`-Ausgang muenzt nichts, und eine unbeantwortete
Anfrage laeuft ab.

## 10. Ausdruecklich NICHT geschlossen, aber benannt — jeder Rest mit Shell-Zeugen

`residues.py`, Wegwerf-Projekt, echte Shell, echter Kernel. „praegt" heisst: das Item stand danach
auf `APPROVED`.

| Rest | Gate lead/sub | Shell | praegt? |
|---|---|---|---|
| **R1** selbst geschriebenes Skript startet den Haken | 0 / 0 | rc 0 | **ja** |
| **R2** `python -m runpy <hook>` | 0 / 0 | rc 1 | **nein** (`-m` nimmt einen Modulnamen) |
| **R3** `python -c "…runpy.run_path(<hook>)"` | 2 / 0 | rc 0 | **nein** (`_assert_minting_caller`) |
| **R4** Kit-Haken*verzeichnis* rekursiv kopieren, Kopie starten | 2 / 0 | rc 0 | **ja** |
| **R5** `sh <<'EOF' … python <hook> … EOF` | 0 / 0 | rc 2 | **nein** (Heredoc belegt die stdin) |
| **R6** `python <(cat <hook>)` (Prozessersetzung) | 0 / 0 | rc 2 | **nein** (der Haken laeuft unter dem Namen der Ersetzung) |

1. **R1 ist die Klasse H11** und trifft jeden — und ist zugleich der Weg, auf dem dieses Repo seine
   Haken misst (`tools/test_hooks.py::run_hook_process`). Die Kits tragen sie gleichermassen. H11 ist
   um genau diese Messung erweitert worden: die Klasse reicht seit dieser Messung bis zu einer
   Freigabe, nicht nur bis zu einer geschriebenen Datei.
2. **R4 trifft nur einen Subagenten und nur die Verzeichnisform.** Eine Haken-DATEI zu kopieren ist
   jedem verweigert (`cp <hook-datei> x` 2/2, `cp -r .claude/hooks copy` 2/2); offen ist
   `cp -r team-kits/<kit>/hooks copy` (2/0), weil das Wort das Haken-Verzeichnis SELBST nennt und
   ein Verzeichnis in der START-Position kein gestartetes Programm ist (das ist die Z3-Korrektur).
   Es gibt einem Subagenten nichts, was R1 ihm nicht ohnehin gibt.
3. **R2 stand in der ersten Fassung als offener Startweg — das war falsch.** Ein Rest, der ein Loch
   behauptet, das es nicht gibt, ist derselbe Defekt wie ein verschwiegenes. Seither hat jeder Rest
   dieser Liste seinen Shell-Zeugen.
4. **Ueber-Verweigerungen, in Kauf genommen und gemessen:** ein Haken-Pfad als **Argument** eines
   Skripts ist rc 2; `python .claude/hooks/test_gates.py` ist rc 2 (der dokumentierte `-m
   pytest`-Weg bleibt rc 0); **keine Shell-Zeile pflegt mehr eine Haken-Datei** (kopieren,
   verschieben, loeschen, `sed -i` sind jedem verweigert, waehrend `Edit`/`Write` dieselbe Datei
   einem Subagenten offenhalten); und ein Wort mit `$ * ? [ {` ist unplatzierbar, ohne dass
   Quotierung gelesen wird — **aber nur dort, wo es ueberhaupt einen Pfad benennen koennte**, sonst
   waere jede Warteschleife mit `[ $i … ]` verweigert.
5. **Nicht mehr in dieser Liste**, weil die Nacharbeit sie beseitigt hat: `grep -c python <hook>`
   (war eine Ueber-Verweigerung der ersten Fassung) und „nach einem `cd` in ein noch nicht
   existierendes Verzeichnis ist jeder Befehl rc 2" (das kam vom Verb-Platz, nicht von der
   Bewegung — H20 ist entsprechend korrigiert).
6. **Die `TSK`-Haelfte von H39 bleibt.** `DONE`/`VALIDATED` haengen am Dispatch-Lease; DEC-0041 gilt
   unveraendert. Aufgeloest ist nur die Freigabe-Haelfte, und die erst nach dem Neustart.
7. **H81 ist nicht geschlossen**, nur nicht mehr getroffen.
8. **Kein `_gate.py` vor dem Freigabe-Haken.** Dieses Repo registriert seine Gates direkt und traegt
   denselben Rest schon fuer die eigenen; eine Aenderung waere fuer alle Eintraege auf einmal.
9. **Der Audit-Schreibweg des Kit-Hakens (N5) — gemessen, und die befuerchtete Folge tritt NICHT
   ein.** Der Haken haengt bei jeder Freigabefrage eine Zeile an
   `project_memory/.audit/hook_events.jsonl`, und die Datei ist git-getrackt (H37 Rest 2). Gate 3
   ist davon aber nicht betroffen: `working_tree_digest` schliesst `project_memory/` aus — das ist
   der Fixpunkt, ohne den kein Beweismittel je den Baum decken koennte, in den es geschrieben wird.
   Selbst gemessen (`probe_audit_commit.py`, echter Gate-3-Prozess): Digest vor und nach dem Anhaengen
   **identisch**, Gate-3-Urteil unveraendert. Was bleibt, ist die Sichtbarkeit im Commit, also H37
   Rest 2 mit einem Schreiber mehr.

## 11. Was der Lead in `CLAUDE.md` nachziehen muss (die Datei ist seine Flaeche)

Der vierte Ausnahme-Absatz nennt heute Startformen als OFFEN, die diese Nacharbeit geschlossen hat
(`$p`, `$(pwd)/…`, `te*m-kits/…`, `nohup`), und schliesst mit „H80 ist deshalb **nicht**
geschlossen". Beides ist nach der Nacharbeit falsch. Gebrauchte Fassung:

> Die vierte ist seit TSK-0098 keine Ueber-Verweigerung, sondern der Punkt: eine Befehlszeile, die
> eine **Haken-Datei startet** — Provider-Baum oder ein `hooks/`-Verzeichnis der Kits, als
> Ableitung, nicht als Liste —, wird **jedem** Aufrufer verweigert, auch dem, der sonst schreiben
> darf. Wer den Haken von Hand faehrt, spielt den Provider und praegt eine Freigabe, die niemand
> erteilt hat; genau diese Zeile war bis dahin rc 0 und ist die gemessene Kette von H80. Was als
> „starten" zaehlt, sagt `_harness._executed_words`, nicht dieser Absatz, und dazu gehoeren seit den
> zwei Pruefrunden vom 2026-08-31 auch ein Wort, dessen Pfad die Shell erst herstellt
> (`$p`, `$(pwd)/…`, `te*m-kits/…`), ein Starter vor dem Interpreter (`nohup`, `timeout`,
> `xargs -a`) und PowerShells Aufrufoperator mit einem Ausdruck. **Zwei Folgen treffen auch, wer
> nichts Boeses vorhat:** ein Wort mit `$`, `*`, `?`, `[` oder `{` ist unplatzierbar und wird
> verweigert, egal wohin es zeigt, und **keine Shell-Zeile pflegt mehr eine Haken-Datei** —
> kopieren, verschieben, loeschen, `sed -i` sind jedem verweigert, waehrend `Edit`/`Write` dieselbe
> Datei einem Subagenten offenhalten. H80 ist damit geschlossen fuer den Unterschied, den es
> benennt; was bleibt, ist H11 (ein selbst geschriebenes Skript praegt weiter), dort mit Messung.

Und zur doppelten Zaehlung: die Zahl „vier gemessene Ausnahmen" gehoert **raus**, nicht auf fuenf
erhoeht. H80 zaehlt daneben eine andere Partition, und zwei Zaehlungen ueber dieselbe Sache sind
genau die Drift, die SR-0008 meint. Vorschlag: „mit gemessenen Ausnahmen, und die ersten beiden
stehen hier, weil sie einen treffen, der nur liest."

## 12. Fuer die Kit-Runde (Z6, kein Auftrag an mich — `team-kits/**` ist verboten)

Der zweite Pruefer hat gemessen, dass die GLOB-Form auch `gate_write_scope` der Kits umgeht. Die
Form, die sich sauber spiegeln laesst, ist **nicht** die START-Position (die Kits brauchen sie
nicht, ihre Regel ist breiter), sondern der Wort-Leser: `_harness._UNRESOLVED` +
`_unresolved_at` + der Positionsvergleich in `_candidates` (ein pfadartiger Teil, der AN ODER NACH
der Stelle beginnt, an der die Shell zu bauen anfaengt, ist `Unplaceable`). Das sind rund
20 Zeilen, sie haengen an nichts aus diesem Repo, und die Kits haben mit `_compat.shell_readings`
denselben Unterbau. Der Gegenprobe-Zeuge dazu ist
`test_gates.UNRESOLVED_WORDS` + `test_an_unresolved_word_really_changes_in_a_shell`.

## 13. Geaenderte Dateien

* `.claude/hooks/_harness.py` — `kit_hooks_directories`, `Executed`, `_started`, `_executed_words`,
  `_command_positions`, `_option_part`, `_operands`, `_verb_as_a_file`, `_program_name`,
  `_carries_flag`/`_flag_words`, `_MODULE_FLAG`, `_UNRESOLVED` + `_unresolved_at` +
  `_cannot_resolve_the_word`, `_handed_a_program_from_elsewhere`,
  `_moves_inside_an_inline_program`, `_shown`, `ProtectedArea.hand_driven` + `hook_directories`,
  `verdict` beantwortet `Executed` zuerst, `written_paths` um die START-Position erweitert
* `.claude/hooks/gate_lead_write_scope.py` — eigener Verweigerungszweig fuer die START-Position
* `.claude/settings.json` — `gate_approval.py` auf `PreToolUse`+`PostToolUse` von
  `AskUserQuestion`, `timeout: 120`, Pfad ueber `${CLAUDE_PROJECT_DIR}`; `_comment` nachgefuehrt
* `.claude/hooks/test_gates.py` — `_script_path`, `_reader` nach oben, `START_SHAPES` (13 Formen)
  + `UNRESOLVED_WORDS` (7) + `POWERSHELL_START`, `_hook_directories`/`HOOK_SUBJECTS`, zwoelf neue
  Tests, `EXPECTED_TOOLS` traegt jetzt (Ereignis, Werkzeug), `_refusable` um `gate_approval.py`,
  `_audit_journals` (die Journal-DATEI, nicht ihr Verzeichnis)
* `docs/POST_V2_WISHLIST.md` — H27 um seine duale Haelfte (der Schreibzugriff INNERHALB der
  Klammer, vorbestehend, mit Kette und Datum), H33 um den Nachtrag zur zweiten Unplatzierbarkeit,
  H80 neu gefasst (Kette, Schnitt, Reste mit Zeugen,
  Ueber-Verweigerungen, Schreib-Haelfte), H39 halb aufgeloest, H11 um die Freigabe-Messung
  erweitert, H20 um den zweiten Ausloeser korrigiert, H81 nachgefuehrt, Tabellenzeilen und
  Herkunftszeile
* `project_memory/staging/TSK-0098/round-protocol.md` — dieses Protokoll

**`team-kits/**` ist unberuehrt** (`git status`), also **kein Kit-Stempel** und kein Spiegel-Lauf.

**Ein eigener Defekt aus der ersten Runde, selbst gefunden:** eine Bearbeitung hatte `_harness.py`
komplett auf CRLF umgestellt, waehrend `HEAD` LF speichert — der Diff zeigte 2346 geaenderte Zeilen
statt 208. Zurueckgestellt (`fix_eol.py`, Pfad im Skript statt als Argument), Inhalt unveraendert.

## 14. Laeufe

* `python -m ruff check .` → All checks passed
* `python tools/validate.py` → all structural checks passed (kein Kit geaendert)
* `python -B -m pytest tools/test_repo_hygiene.py tools/test_disposition.py
  tools/test_shortening_net.py -q` → 52 passed (die Suiten, die `docs/` lesen)
* Volle Gate-Suite: siehe Kapitel 15
* Volle `tools/`-Suite: **nicht** gefahren — Lieferschritt des Leads (DEC-0050). Beruehrt sind
  `.claude/**` (eigene Suite) und `docs/**` (die drei Suiten oben).

## 15. Die Gate-Suite-Laeufe

* **Lauf 1** (erste Fassung): 318 passed, 1 failed in 31:14 — der Stolperdraht auf die
  Loecherliste; meine H39-Tabellenzeile begann mit einem Fettwort, das im `**Urteil**`-Satz nicht
  vorkam. Korrigiert.
* **Lauf 2**: 318 passed, 1 failed in 31:18 —
  `test_every_span_the_kits_prose_removal_takes_out_is_named_where_it_is_documented`, und die
  Ursache war mein eigener Fehler: ich habe waehrend des Laufs Kommentare in `_harness.py`
  ergaenzt, und dieser Test liest die Funktion ueber `inspect.getsource`. Einzeln danach: 1 passed.
  **Waehrend eines Laufs wird an diesem Baum nicht geschrieben.**
* **Lauf 3** (endgueltiger Baum der ersten Fassung): 318 passed, 1 failed in 32:07 —
  `test_gate1_answers_before_its_registration_gives_up`, gefallen an seinem **eigenen
  Rauschwaechter** („band 0.35s, noise 0.68s"), also an „hier wurde nichts gemessen", nicht an „das
  Gate war zu langsam". Drei Einzellaeufe danach: 3× gruen.
* **Lauf 4** (nach der Nacharbeit, vor der letzten Testkorrektur): 425 passed, 1 failed in 34:13 —
  `test_gate1_answers_for_a_tilde_that_does_not_start_its_word`. Kein Gate-Defekt, sondern eine
  echte Wechselwirkung, die dieser Test aufgedeckt hat: einige der Vorsaetze, die er vor eine Tilde
  setzt, SIND die Zeichen, aus denen eine Shell ein Wort baut (`*`, `[`, `{`, `?`), also ist ein
  solches Wort seit dieser Runde auch ohne fuehrende Tilde unplatzierbar. Der Test stellte die Frage
  als „rc 2 genau dann, wenn ein Tilde-Praefix da ist"; er fragt jetzt beide Leser
  (`_could_name_a_path` + `_unresolved_at`) statt einen Satz zu wiederholen. H33 traegt den
  Nachtrag.
* **Lauf 5** (endgueltiger Baum, keine Aenderung waehrenddessen): **426 passed, 0 failed** in
  36:27 — inklusive der beiden Frist-Tests, die in frueheren Laeufen an ihrem eigenen
  Rauschwaechter gefallen waren.
* **Lauf 6** (nach der Subshell-Runde, endgueltiger Baum, keine Aenderung waehrenddessen):
  **489 passed, 0 failed** in 38:58.
