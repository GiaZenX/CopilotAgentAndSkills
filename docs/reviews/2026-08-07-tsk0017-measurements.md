# Messprotokoll der vier Repo-Gates (TSK-0017, 2026-08-07)

Fortsetzung von `docs/reviews/2026-08-05-tsk0015-measurements.md`. Dieses Dokument trägt die Ketten
zu **H1**, **H29** und **H30**, den neuen Stand des Kreuzes nach `DEC-0016` und die Reste, die die
Prüfung von TSK-0015 als F5–F8 gemeldet hat.

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht messbar war, steht das ausdrücklich da,
samt dem Grund.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile ist ein `subprocess`-Start des registrierten Skripts mit
  JSON auf `stdin`, gegen ein Projekt **außerhalb** dieses Repos. `2` = Verweigerung, `0` =
  Durchlass; alles andere liest der Provider als „hook error, carry on", also ebenfalls als
  Durchlass.
- **Die Shell als Schiedsrichter, und zwar über die DATEI.** Jede Zeile lief zusätzlich in einer
  echten `bash` (`C:\Program Files\Git\usr\bin\bash.exe`) in einem Sandbox-Baum, in dem
  `team-kits/kernel/state.py` den Inhalt `a` hatte; „schreibt" heißt: die Datei hat sich danach
  geändert.
- **Vorher/Nachher aus zwei Hook-Verzeichnissen.** „vorher" ist der Stand nach TSK-0015, „nachher"
  der dieser Runde; beide liegen als Prozess vor, dasselbe Projekt, dieselbe Zeile.
- **Ablation statt Behauptung.** Jeder neue Zweig wurde einzeln in einem Klon außerhalb des Repos
  zurückgedreht und der zugehörige Test gefahren (Abschnitt 6).

## 1. F1 — ein Wort, das die Shell nicht als Verzeichnisverb ausführt (H30)

Jede Zeile endet auf `sed -i "s/a/b/" team-kits/kernel/state.py`, **relativ** geschrieben. Spalte
„bash" ist die Datei im Sandbox-Baum; Spalte „stderr" ist, was die Shell zum Wort selbst sagt.

| Zeile davor | bash | stderr der Shell | vorher | nachher |
|---|---|---|---|---|
| `CD "<außerhalb>" ;` | **schreibt** | `CD: command not found` | **rc 0** | **rc 2** |
| `Cd "<außerhalb>" ;` | **schreibt** | `Cd: command not found` | **rc 0** | **rc 2** |
| `cD "<außerhalb>" ;` | **schreibt** | `cD: command not found` | **rc 0** | **rc 2** |
| `PUSHD "<außerhalb>" ;` | **schreibt** | `PUSHD: command not found` | **rc 0** | **rc 2** |
| `PushD "<außerhalb>" ;` | **schreibt** | `PushD: command not found` | **rc 0** | **rc 2** |
| `set-location "<außerhalb>" ;` | **schreibt** | `set-location: command not found` | **rc 0** | **rc 2** |
| `Set-Location "<außerhalb>" ;` | **schreibt** | `Set-Location: command not found` | **rc 0** | **rc 2** |
| `/usr/bin/cd "<außerhalb>" ;` | **schreibt** | `/usr/bin/cd: No such file or directory` | **rc 0** | **rc 2** |
| `env cd "<außerhalb>" ;` | **schreibt** | `env: 'cd': No such file or directory` | **rc 0** | **rc 2** |
| `nice cd "<außerhalb>" ;` | **schreibt** | `nice: 'cd': No such file or directory` | **rc 0** | **rc 2** |
| `sudo cd "<außerhalb>" ;` | **schreibt** | (auf diesem Host deaktiviert) | **rc 0** | **rc 2** |

Zwei Teilursachen, **eine** Eigenschaft: der Leser fragte nie, ob das Wort ein Verb **dieser** Shell
ist. Er faltete die Groß-/Kleinschreibung und nahm den Basisnamen (beides macht eine POSIX-Shell
nicht), und er übernahm das Verb, das der Leser der Kits **hinter** einem übersprungenen Wort
findet. `_harness._directory_role` fragt jetzt die Verbtabelle **der Shell, die der Werkzeugname
nennt** (`SHELLS`), zeichengenau für POSIX; `_harness._is_the_command_name` verlangt, dass vor dem
Wort nur Syntax steht.

**Was das kostet, im selben Lauf gemessen** — hier bewegt die Shell sich wirklich und der Leser
bleibt stehen (Über-Verweigerung, H30):

| Zeile davor | bash | vorher | nachher |
|---|---|---|---|
| `command cd "<außerhalb>" ;` | schreibt nicht | rc 0 | **rc 2** |
| `time cd "<außerhalb>" ;` | schreibt nicht | rc 0 | **rc 2** |
| `! cd "<außerhalb>" ;` | schreibt nicht | rc 0 | **rc 2** |
| `exec cd "<außerhalb>" ;` | schreibt nicht (die Shell endet) | rc 0 | **rc 2** |

**Die Gegenrichtung, im selben Lauf** — hier muss der Leser folgen, sonst ist der Fix eine
Stilllegung:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `{ cd "<außerhalb>" ; } ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `cd -- "<außerhalb>" ; <schreiben>` | schreibt nicht | **rc 2** | **rc 0** |
| `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index` | — | rc 0 | rc 0 |
| `echo hi > docs/note.md` | — | rc 0 | rc 0 |

## 2. F2 — ein `popd`, den die Shell nicht vollzieht, bewegt die Basis hinaus (H30)

Stapelkopf **außerhalb**, Basis **innerhalb** — die eine Richtung, in der Stehenbleiben nicht die
verweigernde Antwort ist. Alle Zeilen enden auf denselben relativen Schreibzugriff.

| Zeile davor | bash | stderr der Shell | vorher | nachher |
|---|---|---|---|---|
| `cd "<außerhalb>" ; pushd "<hier>" ; popd x ;` | **schreibt** | `popd: x: invalid argument` | **rc 0** | **rc 2** |
| `… ; popd -q ;` | **schreibt** | `popd: -q: invalid number` | **rc 0** | **rc 2** |
| `… ; popd +9 ;` | **schreibt** | `popd: +9: directory stack index out of range` | **rc 0** | **rc 2** |
| `… ; popd -n ;` | **schreibt** | — (`-n` löscht den Eintrag ohne Wechsel) | **rc 0** | **rc 2** |
| `cd "<außerhalb>" ; pushd -n "<hier>" ; popd ;` | **schreibt** | — | **rc 0** | **rc 2** |
| `R="<hier>" ; pushd "$R" ; cd "<außerhalb>" ; popd ;` | **schreibt** | — | **rc 0** | **rc 2** |

Die letzte Zeile ist die, die keine der ersten fünf gezeigt hätte: der Leser kann den `pushd` nicht
ausrechnen (Variable), die Shell macht ihn — und der **bare** `popd` dahinter geht auf einen
Eintrag zurück, den der Leser nie gesehen hat. Deshalb ist die Antwort nicht „diesen Pop nicht
vollziehen", sondern eine **unbekannte Position**: jeder relative Kandidat von dort ist
`_harness.Unplaceable` und wird für **jeden** Aufrufer verweigert.

Zwei naheliegende Reparaturen sind gemessen und verworfen: „nur ein bares `popd` poppt" (rot gegen
die Gegenrichtung unten) und „unverbuchbar ⇒ nicht poppen" (grün, schließt die letzten beiden
Zeilen nicht).

**Die Gegenrichtung, im selben Lauf:**

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `cd "<außerhalb>" ; pushd "<hier>" ; popd ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `pushd "<außerhalb>" ; popd ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `pushd "<außerhalb>" ; popd +0 ; <schreiben>` | schreibt | rc 2 | rc 2 |

## 3. F3 — die Umleitung der committenden Stufe (H1)

Mit gültigem `EVD` (`result: pass`) auf den Diff-Hash des Baums, echter Gate-3-Prozess:

| Zeile | vorher | nachher |
|---|---|---|
| `git commit -am wip > docs/note.md` | **rc 0** | **rc 2** |
| `git commit -m wip > docs/note.md` | **rc 0** | **rc 2** |
| `git commit -m wip >> docs/note.md` | **rc 0** | **rc 2** |
| `git commit -m wip 2> docs/note.md` | **rc 0** | **rc 2** |
| `git commit -m wip > /dev/null` (Gegenrichtung) | rc 0 | rc 0 |
| `git commit -m wip` (Gegenrichtung) | rc 0 | rc 0 |
| `git add -A && git commit -m wip` (Gegenrichtung) | rc 0 | rc 0 |
| `echo wip \| git commit -F -` (Gegenrichtung) | rc 0 | rc 0 |

**Und die Wirkung, Ende zu Ende gemessen** (dieselbe Zeile in einer echten `bash` im Prüfbaum
gefahren): `docs/note.md` enthielt vorher `prose\nan uncommitted change\n`, danach die
Standardausgabe von `git`; der Commit zeichnete `docs/note.md | 1 -` auf — ein Baum, den kein
Urteil je gesehen hat. Die Shell richtet die Umleitung **vor** `git` ein, `-am` nimmt die gekürzte
Datei mit. Nur das **Verb** der Stufe ist der Commit; ihre Umleitung ist die Shell.

## 4. F4 — die Grenze, die die Verfassung als Vollständigkeit ausgab

Gate 3 fragt, ob alles, was die Zeile nicht **hinter** den Commit stellt, nur liest — und was „nur
liest" heißt, ist die Einstufung der Kits. Das ist eine Grenze, und zwar in der durchlassenden
Richtung. Gemessen mit gültigem Urteil im Baum:

| Zeile | Wirkung auf den Baum | Gate 3 |
|---|---|---|
| `git commit -am wip > docs/note.md` | kürzt `docs/note.md` | **rc 2** |
| `sed -n "w docs/note.md" radar/note.md ; git commit -m wip` | **überschreibt `docs/note.md`** | **rc 0** |

Die zweite Zeile schreibt ohne jeden Umleitungsoperator; `gate_write_scope` nennt genau das im
eigenen Docstring als seine offene Kante (H22). `CLAUDE.md` sagte dazu „**und jede Zeile, die den
Baum vor dem Commit noch ändert**" — eine Zusicherung, die der Code nicht baut. Die Zeile nennt
jetzt die Stelle, die entscheidet (`gate_commit_evidence._moves_the_tree_first`), und
`test_the_constitution_names_only_code_that_exists` liest diesen Zeiger aus dem Syntaxbaum des
Moduls; `test_gate3_sees_what_the_kits_classification_calls_a_write_and_no_more` misst **beide**
Enden der Grenze und wird rot, sobald sie sich verschiebt.

## 5. Das Kreuz nach DEC-0016 — 638 Formen, die Achsenwerte erzeugt

| | vorher (TSK-0015) | nachher |
|---|---|---|
| Stellungen des Verbs | 19 | 19 |
| Verbformen von Hand | 10 | 12 |
| Verbformen **erzeugt** aus `_harness.SHELLS` | 0 | 13 |
| Vorsatzformen **erzeugt** aus `_stage_verb` der Kits | 0 | 7 |
| Formen ohne Verzeichnisverb / mit zweien | 23 | 30 |
| **Zeilen gesamt** | **213** | **638** |

Erzeugt heißt: `_verb_shapes` liest `_harness.SHELLS` und bildet zu jedem Verb jede Schreibweise,
die der Vergleich der Kits nicht davon unterscheiden kann; `_skipped_words` liest die Wortliste aus
dem **Syntaxbaum der laufenden Funktion** `gate_write_scope._stage_verb` und `_prefix_shapes` bildet
zu jedem Wort eine Zelle. Die Gleichheit beider Mengen ist ein Test
(`test_the_words_the_kits_reader_steps_over_are_all_crossed`), und dass die Shells, die der Leser
kennt, die registrierten sind, ein zweiter
(`test_the_shells_this_reader_knows_are_the_ones_the_registration_names`).

**Die Tabelle hat jetzt zwei Spalten**, weil eine nur zu halten wäre, indem man jede Form weglässt,
in der der Leser bewusst strenger ist als die Shell — und genau dieses Weglassen hat die
verschriebenen Verben zwei Runden lang unsichtbar gehalten. Die erste Spalte ist, was die Shell mit
der Datei macht; die zweite, was der Leser tut. Wo der Leser über ein Wort **vor** dem Befehlsnamen
nichts behauptet, behauptet auch die Tabelle nichts (133 Zellen): dort wird gemessen und nur die
Invariante geprüft — **wo die Shell schreibt, verweigert das Gate**.

| Lauf | Formen | Shell ≠ behauptete Spalte | Loch (Shell schreibt, rc ≠ 2) | Über-Verweigerung (gemessen) |
|---|---|---|---|---|
| vorher (Stand TSK-0015) | 638 | 0 | **94** | 0 |
| nachher | 638 | 0 | **0** | **41** |

Die 94 Löcher sind, in einem Lauf gezählt: die Zeilen, in denen `bash` die geschützte Datei wirklich
ändert und der alte Gate-Prozess rc 0 antwortete. Die 41 Über-Verweigerungen sind die Zeilen, in
denen `bash` **nicht** in den Baum schreibt und der neue Leser trotzdem stehen bleibt — acht davon
`cd -L` (H29), die übrigen Vorsatzformen wie `command cd`, `time cd`, `! cd` (H30).

## 6. Mutationen — jeder gebaute Zweig einzeln

Defekt in einem Klon **außerhalb** des Repos wiederhergestellt (`C:\tmp-harness\mutants\mNN`), der
zugehörige Test darin gefahren:

| Mutation | Test | Ergebnis |
|---|---|---|
| ein verschriebenes oder fremdes Verb bewegt die Basis weiter | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| ein Wort vor dem Befehlsnamen wird übersprungen | dito | **rot** |
| ein Pop übergeht seine Operandenliste | dito | **rot** |
| ein Push, den der Leser nicht machen konnte, lässt den Stapel gültig | dito | **rot** |
| das Optionsende ist eine Option | dito | **rot** |
| Gate 3 überspringt die Umleitung der committenden Stufe | `…gate3_refuses_a_line_that_moves_the_tree_before_it_commits` | **rot** |
| die Reserve ist ein Anteil und sonst nichts | `…answers_before_its_registration_gives_up` | **rot** |
| die Vorsatz-Achse wird von Hand auf ein Wort gekürzt | `…words_the_kits_reader_steps_over_are_all_crossed` | **rot** |
| eine registrierte Shell hat keinen Eintrag im Leser | `…shells_this_reader_knows_are_the_ones_the_registration_names` | **rot** |
| die Verfassung zeigt auf einen Namen, den es nicht gibt | `…constitution_names_only_code_that_exists` | **rot** |
| die Kits führen kein Verb mehr als lesend | `…gate3_sees_what_the_kits_classification_calls_a_write_and_no_more` | **rot** |
| eine Vorsatz-Zelle behauptet, der Leser folge der Bewegung | beide Tabellen-Tests | **rot** (beide) |

Die letzte Zeile ist der Stolperdraht auf der Invariante selbst: wo die Tabelle für eine Zelle
nichts über die Shell behauptet, darf sie die Antwort des Gates trotzdem nicht frei wählen — die
gemessene Shell und der gemessene Gate-Prozess widersprechen ihr dann beide.

## 7. Der Deadline-Test, der an der Maschine scheiterte

**Vorher, auf diesem Rechner rot** — nicht wegen des Gates:
*„no registration on this host can show that the reserve needs its floor: a gate process that
answers at once costs 0.13s here and a whole verdict 0.16s, against a share of 0.80 and a floor of
1.50s"*. Die Vorbedingung verlangte `bare > seconds * (1 - share)`, also bei einem Anteil von 0,8
und ganzzahligen Registrierungen `bare > 0,2 s` — dieser Host braucht 0,13 s. Der Prüfbericht meldet
dieselbe Zeile aus der **anderen** Richtung: 4,76 s unter Nebenlast gegen eine Untergrenze von
1,50 s. Beides ist eine Zahl, die die Maschine bestimmt.

**Nachher wird die Größe kontrolliert statt erhofft.** `_slowed` schiebt einen bekannten Prozessstart
**vor** `_LOADED_AT` — die Zeile wird im Syntaxbaum von `_harness` gesucht, nicht im Text — und das
ist per Definition der Teil des Starts, den das Gate nicht messen kann. `_floor_case` wählt daraus
die Registrierung mit dem breitesten Rand auf **beiden** Seiten:

| Prozessstart vor der ersten Zeile | gewählte Registrierung | dafür eingestellter Start | Rand |
|---|---|---|---|
| 0,13 s (dieser Host, unbelastet) | 2 s | 0,95 s | 0,55 s |
| 0,50 s | 2 s | 0,95 s | 0,55 s |
| 0,90 s | 2 s | 0,95 s | 0,55 s |
| 1,40 s | 7 s | 1,45 s | 0,05 s |
| 1,60 s | — | — | — |
| 4,76 s (unter Nebenlast, aus dem Prüfbericht) | — | — | — |

Die letzten beiden Zeilen sind der Fall, den der Test als **Fehlschlag mit Grund** meldet: liegt der
Prozessstart über der Untergrenze der Reserve, gibt es keine Registrierung, unter der die
Untergrenze die Frist noch hält — dann ist `_harness._RESERVE_FLOOR` die Zahl, die sich ändern muss,
und nicht der Test. Ein Rand unter dem eigenen Zeitrauschen dieses Hosts (gemessen als Spanne
derselben drei Läufe) meldet dasselbe.

**Beide Enden im selben Lauf:** dieselbe verlangsamte Kopie mit `_RESERVE_FLOOR = 0.0` muss die
Frist **verfehlen**, sonst schmückt die Untergrenze nur. Gemessen auf diesem Host (Prozessstart
0,13 s, Rauschen 0,01 s, eingestellter Start 0,95 s, Registrierung 2 s): **mit** Untergrenze
Antwort nach 1,41 s, **ohne** sie nach 2,53 s — also nach dem Moment, in dem der Provider den
Prozess tötet, und ein getöteter Hook ist ein Durchlass.

## 8. Reste

| Kette | bash | nachher | Eintrag |
|---|---|---|---|
| `cd -L "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 2 | H29, Über-Verweigerung |
| `cd -- "<außerhalb>" ; <schreiben>` | schreibt nicht | **rc 0** | **H29, geschlossen** (POSIX-Optionsende) |
| `cd "<außerhalb>" 2>&1 ; <schreiben>` | schreibt nicht | rc 2 | H29, Über-Verweigerung |
| `command cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 2 | H30, Über-Verweigerung |
| `arr=(a b) cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 2 | H24, Über-Verweigerung |
| `x=1 cd "<außerhalb>" ; <schreiben>` | schreibt nicht | **rc 2** | **H24, neu** — vorher rc 0 |

Die letzte Zeile ist eine Verschärfung dieser Runde und steht als solche in H24: eine skalare
Zuweisung vor dem Verb folgte der Basis bisher, und `_is_the_command_name` lässt vor dem Befehlsnamen
nur noch Syntax stehen. Das ist Reibung, keine Lücke, und ohne Aufzählung nicht enger zu fassen.

`2>&1` bleibt offen und der Grund steht jetzt im Eintrag: der Tokeniser gibt `2`, `>&`, `1` zurück,
und ein Deskriptor **vor** einem Umleitungsoperator ist von einem Verzeichnis namens `2` nicht mehr
zu unterscheiden, sobald die Klebung weg ist (`cd 2 > log` gegen `cd <ziel> 2> log`). Das ist keine
fehlende Aufzählung, sondern eine Information, die die Zerlegung verliert.

## 9. Suite

`python -B -m pytest .claude/hooks/test_gates.py -q`:

| Lauf | Ergebnis | Dauer |
|---|---|---|
| vor dieser Runde | 124 grün, **1 rot** (Abschnitt 7) | 1:40 |
| nachher | **130 grün** | 2:20 |

Die zusätzliche Zeit ist das gewachsene Kreuz: 638 Formen × zwei Läufe (echte `bash`, echter
Gate-Prozess), zehn davon gleichzeitig. Die beiden Tests kosten 32,3 s und 7,5 s, gemessen mit
`--durations`. Eine zufällige Testreihenfolge ist auf diesem Rechner nicht herstellbar (weder
`pytest-randomly` noch `pytest-random-order` installiert, keine `pytest.ini`) — die Läufe stehen in
Dateireihenfolge.

`python tools/validate.py` meldet in dieser Runde **drei** Fehler, alle derselben Form
(`dev-team`/`office-team`/`research-team`: „kit files changed but VERSION not bumped"). Sie gehören
nicht zu diesem Auftrag: `team-kits/**` ist sein verbotener Bereich, und die geänderten Kit-Dateien
sind das parallel geprüfte Migrationspaket. `python tools/bump_kit_version.py` ist deshalb **nicht**
gefahren worden — es hätte eine fremde, laufende Änderung gestempelt.
