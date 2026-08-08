# Messprotokoll der vier Repo-Gates (TSK-0019, 2026-08-07)

Fortsetzung von `docs/reviews/2026-08-07-tsk0017-measurements.md`. Dieses Dokument trägt die Ketten
zu **H31**, **H20**, **H24**, **H29**, **H30** und **H32**, den neuen Stand des Kreuzes nach
`DEC-0018` und die Reste, die die Prüfung von TSK-0017 als F4–F6 gemeldet hat.

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht messbar war oder anders ausfiel als im
Auftrag beschrieben, steht das ausdrücklich da.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile ist ein `subprocess`-Start des registrierten Skripts mit
  JSON auf `stdin`, gegen ein Projekt **außerhalb** dieses Repos (`C:\tmp-harness-r19\dev`,
  gebaut mit `test_gates.build_project`). `2` = Verweigerung, `0` = Durchlass; alles andere liest
  der Provider als „hook error, carry on", also ebenfalls als Durchlass.
- **Die Shell als Schiedsrichter, und zwar über die DATEI.** Jede Zeile lief zusätzlich in einer
  echten `bash` (`C:\Program Files\Git\usr\bin\bash.exe`) im selben Baum, in dem
  `team-kits/kernel/state.py` den Inhalt `a` hatte; „schreibt" heißt: die Datei hat sich danach
  geändert. Für Gate 3 zusätzlich Ende zu Ende: Inhalt von `docs/note.md` und `git rev-parse HEAD`
  vor und nach der Zeile.
- **Vorher/Nachher aus zwei Hook-Verzeichnissen.** „vorher" ist der Stand nach TSK-0017, „nachher"
  der dieser Runde; beide liegen als Prozess vor, dasselbe Projekt, dieselbe Zeile.
- **Ablation statt Behauptung.** Jeder gebaute Zweig wurde einzeln in einem Klon **außerhalb** des
  Repos zurückgedreht und der zugehörige Test darin gefahren (Abschnitt 5).

## 1. F1 — eine Erweiterung, die die Quotierung unterdrückt (H31)

Jede Zeile endet auf `sed -i "s/a/b/" team-kits/kernel/state.py`, **relativ** geschrieben.

| Zeile davor | bash | vorher | nachher |
|---|---|---|---|
| `cd "~" ;` | **schreibt** | **rc 0** | **rc 2** |
| `cd '~' ;` | **schreibt** | **rc 0** | **rc 2** |
| `cd \~ ;` | **schreibt** | **rc 0** | **rc 2** |
| `cd "~/" ;` | **schreibt** | **rc 0** | **rc 2** |
| `cd ~ ;` (Gegenrichtung) | schreibt nicht | rc 0 | rc 0 |

Die Shell sagt in den ersten vier Zeilen `~: No such file or directory` und **bleibt stehen**; der
Leser war ins Heimatverzeichnis gegangen. Ende zu Ende, ein Werkzeugaufruf und ohne Vorbereitung:
`cd "~" ; python -c "…"` gegen `.claude/settings.json` — die Registrierung aller vier Gates —
ging von 2903 Byte auf 2 Byte; dieselbe Zeile ohne das `cd` ist rc 2.

Der Mechanismus ist die **Reihenfolge**: eine Shell erweitert das Wort und entfernt danach die
Quotierung, `_compat.shell_readings` gibt das Ergebnis des zweiten Schritts, und darauf zu
erweitern macht genau die Erweiterung, die die Quotierung verhindert hat. `_harness.readings` gibt
zu jeder Lesart jetzt mit an, ob sie erweiterbar ist.

## 2. F2 — die Richtung ist eine Eigenschaft der BASIS, nicht des Verbs (H20, H24, H29, H30)

Alle Zeilen: `cd "<außerhalb>" ; <bewegung> ; sed -i "s/a/b/" team-kits/kernel/state.py`, wobei
`<bewegung>` auf das Projekt zeigt. Die Shell steht am Ende **im** Baum und schreibt die geschützte
Datei wirklich.

| Bewegung | bash | vorher | nachher | Eintrag |
|---|---|---|---|---|
| `R="<hier>" ; cd "$R"` | **schreibt** | **rc 0** | **rc 2** | H16/H20 |
| `command cd "<hier>"` | **schreibt** | **rc 0** | **rc 2** | H30 |
| `time cd "<hier>"` | **schreibt** | **rc 0** | **rc 2** | H30 |
| `! cd "<hier>"` | **schreibt** | **rc 0** | **rc 2** | H30 |
| `x=1 cd "<hier>"` | **schreibt** | **rc 0** | **rc 2** | H24 |
| `cd -L "<hier>"` | **schreibt** | **rc 0** | **rc 2** | H29 |
| `cd "<hier>" 2>&1` | **schreibt** | **rc 0** | **rc 2** | H29 |
| `pushd "<hier>" ; popd -n` (Gegenprobe) | **schreibt** | rc 2 | rc 2 | H30, schon zu |
| `cd "<hier>"` (Gegenprobe) | **schreibt** | rc 2 | rc 2 | — |

**Und die Grenze ist nicht die des Repos.** Der Auftrag zu dieser Runde sagt, Stehenbleiben sei die
fail-closed-Richtung, „solange die Basis unter der geschützten Wurzel steht". Gemessen ist das
falsch — es kommt auf den **Teilbaum** an, nicht auf das Repo:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `cd docs ; command cd .. ; sed -i "s/a/b/" team-kits/kernel/state.py` | **schreibt** | **rc 0** | **rc 2** |

Die Basis hat das Repo nie verlassen; sie stand nur im falschen Teilbaum. Deshalb ist die Antwort
nicht an die Basis gebunden, sondern an die Bewegung: was der Leser nicht **ausrechnen** kann, macht
die Position unbekannt — unabhängig davon, wohin die Bewegung zeigt.

**Die Gegenrichtung, im selben Lauf** (Zeilen, die weiter durchgelassen werden müssen):

| Zeile | nachher |
|---|---|
| `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index` | rc 0 |
| `echo hi > docs/note.md` | rc 0 |
| `cd docs ; echo hi > note.md` | rc 0 |
| `cd ~ ; <relativ schreiben>` | rc 0 |
| `cd -- "<außerhalb>" ; <relativ schreiben>` | rc 0 |
| `cd "<außerhalb>" ; pushd "<hier>" ; popd ; <relativ schreiben>` | rc 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | rc 0 |
| `git commit -m wip` | rc 0 |
| `echo "$(git rev-parse HEAD)"` | rc 0 |
| `echo $(cat docs/note.md)` | rc 0 |

## 3. F3 — ein Befehl, den eine Ersetzung einführt (H32)

**Gate 1**, dieselbe geschützte Datei, `bash` als Schiedsrichter:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `echo $(sed -i "s/a/b/" team-kits/kernel/state.py)` | **schreibt** | **rc 0** | **rc 2** |
| dieselbe Zeile in Backticks | **schreibt** | **rc 0** | **rc 2** |
| `echo "$(sed -i …)"` | **schreibt** | **rc 0** | **rc 2** |
| `echo $(sed -i "s/a/)/" team-kits/kernel/state.py)` | **schreibt** | **rc 0** | **rc 2** |
| `git commit -m "wip $(sed -i s/a/b/ team-kits/kernel/state.py)"` | **schreibt** | **rc 0** | **rc 0** |

Die vierte Zeile ist die, die die ausbalancierte Lesart allein nicht sieht: der Zähler schließt am
`)` **im `sed`-Skript**. `_harness._closings` liest darum zwei Enden, die ausbalancierte und die
letzte Klammer der Zeile. Die fünfte bleibt offen und steht als benannte Hälfte in H32: die Kits
entfernen ein quotiertes Nachrichtenargument als Prosa, bevor irgendetwas den Text liest.

**Gate 3**, mit gültigem `EVD` (`result: pass`) auf den Diff-Hash des Baums, echter Gate-Prozess,
und für jede durchgelassene Zeile zusätzlich Ende zu Ende in einer echten `bash`:

| Zeile | vorher | Wirkung vorher | nachher |
|---|---|---|---|
| `git commit -am wip $(sed -i s/prose/POISON/ docs/note.md)` | **rc 0** | `docs/note.md` = `POISON`, **HEAD bewegt**, der Commit trägt es | **rc 2** |
| `git commit -am wip \`sed -i s/prose/POISON/ docs/note.md\`` | **rc 0** | Baum geändert, HEAD bewegt | **rc 2** |
| `echo "$(sed -i s/prose/POISON/ docs/note.md)" \| git commit -F -` | **rc 0** | Baum geändert | **rc 2** |
| `git commit -m "wip $(sed -i s/prose/POISON/ docs/note.md)"` | rc 0 | Baum geändert | **rc 0** (H32, offen) |
| `git commit -m "wip $(git rev-parse HEAD)"` (Gegenrichtung) | rc 0 | Baum unverändert | rc 0 |
| `git commit -m wip` (Gegenrichtung) | rc 0 | — | rc 0 |
| `git commit -m wip > /dev/null` (Gegenrichtung) | rc 0 | — | rc 0 |
| `git commit -am wip > docs/note.md` (schon zu, TSK-0017) | rc 2 | — | rc 2 |
| `git commit -m wip > <außerhalb>/log.txt` | rc 2 | — | rc 2 (Reibung, jetzt in H1 benannt) |

Die letzte Zeile bewegt nichts, was der Beleg von Gate 3 liest — sie ist Reibung und stand bis zu
dieser Runde in keinem Eintrag.

## 4. Das Kreuz nach DEC-0018 — 1440 Formen, die ACHSE erzeugt

| | vorher (TSK-0017) | nachher |
|---|---|---|
| Stellungen des Verbs | 19 | 19 |
| **Richtungen der Bewegung (Basis innen / außen)** | **1** | **2** |
| Bewegungen von Hand | 12 | 15 |
| Verbformen erzeugt aus `_harness.SHELLS` | 13 | 13 |
| Vorsatzformen erzeugt aus `_stage_verb` | 7 | **9** |
| Ersetzungsformen erzeugt aus `SHELLS[…]["substitutions"]` | 0 | 2 |
| Formen ohne Verzeichnisverb / mit zweien | 30 | 32 |
| **Zeilen gesamt** | **638** | **1440** |

Zwei Achsen sind neu, und beide sind das, was `DEC-0018` verlangt:

- **die Richtung.** Von den 32 erzeugten Bewegungen zielten 25 nach außen, 7 hatten kein Ziel und
  **keine einzige** nach innen — die Bedingung stand als Verzweigung im Code (`popd` hatte eine
  eigene Antwort) und hatte darum keine Achse. Jetzt wird jede Form in **beiden** Richtungen
  gekreuzt (`BASES`), und die erwartete Antwort wird aus der Landung des Akteurs abgeleitet
  (`_reaches_the_tree`).
- **der Zuweisungs-Vorsatz.** Der Erzeuger las die Wortliste der Kits; die zweite Verzweigung von
  `_stage_verb` (`"=" in low and not low.startswith("-")`) ist ein **Prädikat** und hatte keine
  Zelle. `_skip_branches` liest jetzt jede Verzweigung, deren Rumpf ein `continue` ist, bildet aus
  ihren eigenen Konstanten Kandidaten und **beweist** jeden an der laufenden Funktion. Ergebnis:
  `!`, `=`, `a=b`, `command`, `env`, `exec`, `nice`, `sudo`, `time`.

| Lauf | Formen | Shell ≠ behauptete Spalte | Loch (Shell schreibt, rc ≠ 2) | Über-Verweigerung |
|---|---|---|---|---|
| vorher (Stand TSK-0017) | 1440 | 0 | **11 Formen, 8 Ursachen** (Abschnitte 1–3) | 41 von 638 |
| nachher | 1440 | 0 | **0** | **64** |

Die zweite Spalte der Tabelle hat jetzt drei Werte statt zwei: `AT_TARGET`, `STAYS_PUT` und `LOST` —
und `LOST` ist der Wert, den die Verzweigung erzeugt hat, die vorher keine Achse war.

**Was der Rest F5 kostet und was daraus wurde:** die Invariante über die Zellen, für die die Tabelle
nichts über die Shell behauptet, konnte nicht feuern — deren zweite Spalte ist eine Konstante
(„verweigert"), also war der Zweig konstant falsch, und der Docstring nannte sie trotzdem „gebunden
durch die Invariante". 133 echte Shell-Prozesse je Lauf für eine Frage, die schon beantwortet war.
Gemessen wird jetzt genau dort, wo die Invariante feuern **kann**: bei den unbehaupteten Zellen,
deren Gate-Spalte ein Durchlass ist (99 von 342). Der Rest ist an den Gate-Prozess des anderen Tests
gebunden, und sobald eine dieser Zellen zum Durchlass wird, wird sie ohne jede Änderung wieder
gemessen.

## 5. Mutationen — jeder gebaute Zweig einzeln

Defekt in einem Klon **außerhalb** des Repos wiederhergestellt (`C:\tmp-harness-r19\m19\…`), der
zugehörige Test darin gefahren:

| Mutation | Test | Ergebnis |
|---|---|---|
| jede Lesart eines Wortes ist erweiterbar | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| ein Wort vor dem Befehlsnamen lässt die Basis stehen | dito | **rot** |
| eine unverbuchbare Operandenliste lässt die Basis stehen | dito | **rot** |
| eine Bewegung, die nicht gelang, lässt die Basis stehen | dito | **rot** |
| eine Ersetzung ist kein Befehl | dito | **rot** |
| eine Ersetzung ist kein Befehl | `…gate3_refuses_a_line_that_moves_the_tree_before_it_commits` | **rot** |
| nur die ausbalancierte Klammer schließt eine Ersetzung | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| die Vorsatz-Achse kommt wieder aus der Wortliste statt aus den Verzweigungen | `…words_the_kits_reader_steps_over_are_all_crossed` | **rot** |
| die Tabelle kreuzt nur eine Richtung | dito | **rot** |

Die letzten beiden sind Stolperdrähte auf den Achsen selbst: der erste fragt die Verzweigungen der
laufenden Funktion und **nicht** den Erzeuger der Zellen (sonst wären beide per Konstruktion einig),
der zweite fragt, ob überhaupt eine Form in den zwei Richtungen verschieden antwortet.

## 6. Suite

`python -B -m pytest .claude/hooks/test_gates.py -q`:

| Lauf | Ergebnis | Dauer |
|---|---|---|
| vor dieser Runde, im Klon außerhalb des Repos | 130 grün | 3:13 |
| nachher, im Klon | 130 grün | 3:44 |
| nachher, im Repo (installiert) | **130 grün** | 4:24 |
| nachher, im Repo, unter Nebenlast (die Hälfte der Kerne belegt) | **130 grün** | 5:10 |

Die zusätzliche Zeit ist das gewachsene Kreuz: 1440 Formen durch einen echten Gate-Prozess (77,5 s)
und 1197 davon zusätzlich durch eine echte `bash` (24,9 s), zehn gleichzeitig. Die Zahl der
Shell-Prozesse ist trotz der doppelten Tabelle nur um 559 gestiegen, weil die konstant gebundenen
Zellen nicht mehr gemessen werden (Abschnitt 4).

`python -m ruff check .` ist sauber, `python tools/validate.py` meldet nach der Installation
**„all structural checks passed"** (gemessen 2026-08-07, nach dem letzten Einspielen). Ein
Kit-Stempel gehört dieser Runde nicht: `team-kits/**` ist verbotener Bereich, und der Arbeitsbaum
trägt ein fremdes, parallel laufendes Kit-Paket — `python tools/bump_kit_version.py` ist deshalb
**nicht** gefahren worden, es hätte diese fremde Änderung gestempelt.

`python -m pytest tools/ -q` ist ebenfalls nicht gefahren. Grund, geprüft statt vermutet: keine der
sieben geänderten Dateien wird von jener Suite gelesen — sie sammelt `.claude/hooks/test_gates.py`
nicht ein (dessen Docstring sagt das und `tools/` ist die Suite der Kits), und die Treffer auf
`CLAUDE.md` in `tools/test_hooks.py` und `tools/test_context_budget.py` sind Dateien, die diese
Tests in ihren eigenen Stellvertreterprojekten **schreiben**, plus die installierte Einstiegsdatei
unter `user/claude/`. Ein Lauf über `tools/` hätte in dieser Runde den Zustand des fremden Pakets
gemeldet, nicht den dieses.

## 7. Was diese Runde NICHT geschlossen hat

- **H32, zweite Hälfte** — eine Ersetzung in einem quotierten Nachrichtenargument. Kette in
  Abschnitt 3, Urteil und Begrenzung im Eintrag.
- **H22** — die Pipe (`echo <pfad> | xargs sed -i …`) und die Patch-Datei. Unverändert.
- **H16/H21** — der Pfad in einer Variablen als **Pfad**; geschlossen ist nur die Bewegung.
- **H29** — `cd -L` und `cd <ziel> 2>&1` bleiben Über-Verweigerung, jetzt in beiden Richtungen.
- **H19** — ein Kandidat, der einen Vorfahren nennt. Er ist in dieser Runde dreimal einer eigenen
  Messzeile begegnet: ein einzelner Backslash in einem `python -c`-Programmtext ist ein
  `_PATHISH`-Treffer, der zu `C:\` auflöst, und die Zeile wird verweigert. Reibung, unverändert.

## 8. Was der Fix kostet, an der eigenen Zeile gemessen

Die erste Zeile, die nach der Installation verweigert wurde, war die des Umsetzers selbst:
`cd /c/Offline\ Repos/AgentAndSkills && python -B -m pytest .claude/hooks/test_gates.py -q`. Der
Grund ist der gebaute Zweig: Git Bash betritt `/c/…`, ein Windows-Prozess betritt es nicht
(`C:\c\…`), also kann der Leser die Bewegung nicht ausrechnen und gibt die Position auf. Gemessen
gegen ein Stellvertreterprojekt, vorher aus der Sicherungskopie der Hooks:

| Zeile | vorher | nachher |
|---|---|---|
| `cd /c/<projekt> && echo hi > docs/note.md` | rc 0 | **rc 2** |
| `cd "C:/<projekt>" && echo hi > docs/note.md` | rc 0 | rc 0 |
| `cd /c/<projekt> && git rev-parse HEAD` | rc 0 | rc 0 |
| `cd /c/<projekt> && timeout … python -B -m pytest …` | rc 2 | rc 2 |

Die letzte Zeile war **schon vorher** rc 2, und aus einem anderen Grund: `timeout` führen die Kits
nicht als lesendes Verb, also wird jedes Wort der Stufe zum Kandidaten, und `.claude/hooks/…` ist
dem Sitzungsagenten verweigert. Die Abhilfe steht in der Verweigerung; die dokumentierten Befehle
dieses Repos tragen kein `cd`. Der Eintrag dazu ist H20.
