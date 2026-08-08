# Messprotokoll TSK-0021 (2026-08-07)

Alles hier ist gegen **laufende Prozesse** gemessen: das Gate als echter Prozess mit JSON auf stdin,
gegen ein Stellvertreterprojekt **außerhalb** dieses Repos (`test_gates.build_project`), und die
Shell als Schiedsrichter über die **Datei** — die geschützte Datei trägt vor jeder Zeile `a`, und was
zählt, ist ob sie danach etwas anderes trägt. Ein Rückgabecode ist kein Beleg dafür, wo eine Shell
steht.

Der Schiedsrichter wird **gemessen ausgewählt** (`test_gates._can_arbitrate`), nicht nach Namen: auf
diesem Host ist die erste `bash` auf dem PATH der WSL-Starter, der `C:/…` nicht sieht. Gewählt wurde
`C:\Program Files\Git\usr\bin\bash.exe`.

Registrierte Frist von Gate 1 in diesem Repo: **120 s** (`.claude/settings.json`). Das Budget, das
sich das Gate davon zugesteht, ist `120 − max(120·0,2; 1,5)` = **96 s**.

---

## Abschnitt 1 — H33: die Tilde-Erweiterung kam von einer Funktion mit einer anderen Frage

### 1a. Was die Shell wirklich tut

Ein Aufruf, alle Formen auf einmal, `printf "%s\n" ~X/T`, Arbeitsverzeichnis = Sandbox:

| Form | ohne Vorbereitung | nach `cd docs ; pushd ..` |
|---|---|---|
| `~` | `/c/Users/zenti/T` | `/c/Users/zenti/T` |
| `~+` | `<sandbox>/T` | `<sandbox>/T` |
| `~-` | `~-/T` (unverändert) | `<sandbox>/docs/T` |
| `~0` | `<sandbox>/T` | `<sandbox>/T` |
| `~1` | `~1/T` (unverändert) | `<sandbox>/docs/T` |
| `~+0` | `<sandbox>/T` | `<sandbox>/T` |
| `~+1` | `~+1/T` (unverändert) | `<sandbox>/docs/T` |
| `~-0` | `<sandbox>/T` | `<sandbox>/docs/T` |
| `~-1` | `~-1/T` (unverändert) | `<sandbox>/T` |
| `~zenti` | `/c/Users/zenti/T` | `/c/Users/zenti/T` |
| `~root` | `~root/T` (unverändert) | `~root/T` |

`os.path.expanduser` beantwortet davon **zwei** Formen wie die Shell (`~`, und einen Login-Namen,
den es kennt). Für die übrigen schweigt es nicht, sondern liefert `C:\Users\<präfix>\…`.

### 1b. Was die Shell dabei mit der geschützten Datei macht

Schreibzeile jeweils `sed -i "s/a/b/" <form>/team-kits/kernel/state.py`:

| Zeile | Datei geändert |
|---|---|
| `~+` ohne Vorbereitung | **ja** |
| `~0` ohne Vorbereitung | **ja** |
| `~+0` ohne Vorbereitung | **ja** |
| `cd docs ; … ~-/…` | **ja** |
| `pushd docs … ; … ~1/…` | **ja** |
| `~` ohne Vorbereitung | nein (Heimatverzeichnis) |

### 1c. Was das Gate dazu sagte — vorher

Ein Werkzeugaufruf, keine Vorbereitung, gegen das Gate des laufenden Repos:

```
sed -i "s/a/b/" team-kits/kernel/state.py                    rc 2
sed -i "s/a/b/" ~0/team-kits/kernel/state.py                 rc 0
sed -i "s/a/b/" ~1/team-kits/kernel/state.py                 rc 0
sed -i "s/a/b/" ~-/team-kits/kernel/state.py                 rc 0
sed -i "s/a/b/" ~-0/team-kits/kernel/state.py                rc 0
sed -i "s/a/b/" ~-1/team-kits/kernel/state.py                rc 0
sed -i "s/a/b/" ~root/team-kits/kernel/state.py              rc 0
sed -i "s/a/b/" ~zenti/team-kits/kernel/state.py             rc 0
sed -i "s/a/b/" ~+/.claude/settings.json                     rc 2  ← Zufall, siehe unten
sed -i "s/a/b/" ~+/project_memory/…                          rc 2  ← Zufall, siehe unten
```

`~+` und `~+0` kamen **nur zufällig** verweigert heraus: `+` fehlt in der Zeichenklasse
`_harness._PATHISH`, also zerfällt das Wort beim Teilstring-Scan und `/team-kits/…` bleibt als
eigener Kandidat übrig. Gemessen im roten Lauf war die Begründung dieser Verweigerungen
`no tool call in this repo may write C:\Users\zenti` — das Heimatverzeichnis als **Vorfahre**, nicht
das Wort. Ein Schutz, der so zustande kommt, ist keiner.

### 1d. Nach dem Fix

Dieselben Zeilen gegen den geänderten Klon: `~` und `~/` bleiben **rc 0**, alle 14 übrigen Formen
sind **rc 2**, mit einer Begründung, die das Wort nennt.

### 1e. Rot ohne den Fix

`_harness._expanded` im Klon auf die alte Fassung zurückgedreht,
`pytest .claude/hooks/test_gates.py -k tilde`:

```
FAILED test_gate1_places_a_tilde_word_where_the_shell_puts_it
  `~-`  after a move out of the tree : shell writes, gate rc 0
  `~-`  after a push out of the tree : shell writes, gate rc 0
  `~-0` after a push out of the tree : shell writes, gate rc 0
  `~1`  after a push out of the tree : shell writes, gate rc 0
  `~-0` with nothing behind it       : shell writes, gate rc 0
  `~0`  with nothing behind it       : shell writes, gate rc 0
  `~00` with nothing behind it       : shell writes, gate rc 0
  `~+`  with nothing behind it       : refused, but the reason never names the word
  `~+0` with nothing behind it       : refused, but the reason never names the word
```

Neun Zellen zugleich, und die letzten beiden sind der Zufall aus 1c, den derselbe Test als solchen
meldet statt ihn als Schutz zu zählen. Danach zurückgesetzt; der Test ist wieder grün (35,2 s).

---

## Abschnitt 2 — H35: die Frist als Angriffsfläche

Alle Zeiten sind die volle Prozesslaufzeit des Gates, gegen die registrierten 120 s.

### 2a. Vorher, Zeile aus Ersetzungs-Öffnern und einem Schließer (`echo $($(…)…)`)

| Öffner | Zeichen | rc | Zeit |
|---|---|---|---|
| 200 | 406 | 0 | 2,9 s |
| 500 | 1006 | 0 | 24,1 s |
| 1000 | 2006 | **0** | **106,6 s** |
| 2000 | 4006 | 2 | 96,1 s |
| 4000 | 8006 | 2 | 96,5 s |

Die 106,6 s bei 2006 Zeichen sind der Befund: die Prüfung stand **am Anfang** von
`substituted_lines`, und die ganze Zeit steckte in **einem** Aufruf davon.

### 2b. Die vollständige Kette, ein Werkzeugaufruf, ohne Vorbereitung

```
sed -i "s/a/b/" team-kits/kernel/state.py #$($($(…1200 Öffner…)
```

2444 Zeichen. Das `#` versteckt die Öffner vor der Shell, nicht vor dem Gate.

* `bash` ändert die geschützte Datei: **ja**
* Gate 1 vorher: **rc 2 nach 150,6 s** — also **nach** der registrierten Frist. Ein Hook, der dann
  noch entscheidet, wird getötet, und ein getöteter Hook ist ein Durchlass.
* Gate 1 nachher: **rc 2 nach 96,2 s**, mit der Begründung des Budgets.

### 2c. Nachher, über die Größe hinweg

| Öffner | Zeichen | rc | Zeit |
|---|---|---|---|
| 1000 | 2006 | 2 | 96,2 s |
| 4000 | 8006 | 2 | 96,2 s |
| 20000 | 40006 | 2 | 96,2 s |

Die Antwort hängt nicht mehr an der Länge, sondern nur noch am Budget.

### 2d. Rot ohne den Fix

Der Faden `_harness._the_budget_is_spent` im Klon aus `guarded()` entfernt,
`pytest -k however_long`:

```
FAILED test_gate1_answers_before_its_registration_however_long_the_line_takes_to_read
  the gate answered after 13.02s while its registration gives it 2s
```

Danach zurückgesetzt; der Test ist wieder grün (26,8 s).

---

## Abschnitt 3 — H34: die Prosa-Entfernung löscht einen Schreib-Operanden

Ein Werkzeugaufruf, kein Commit, keine Ersetzung. Schiedsrichter über die Datei wie oben.

| Zeile | Shell schreibt | Gate |
|---|---|---|
| `sed -i "s/a/b/" team-kits/kernel/state.py` | ja | **rc 2** |
| `sed -i -e "s/a/b/" -b "team-kits/kernel/state.py"` | **ja** | **rc 0** |
| `sed -i -e "s/a/b/" --notes "team-kits/kernel/state.py"` | nein (`sed` lehnt das Flag ab) | rc 0 |
| `sed -i -e "s/a/b/" -F "team-kits/kernel/state.py"` | nein (`sed` lehnt das Flag ab) | rc 0 |

Die zweite Zeile ist die Kette: `-b` ist für `sed` ein echtes Boolean, der quotierte Operand
dahinter ist die **Datei**, und `gate_write_scope._MESSAGE_ARG_RX` löscht beides zusammen, bevor
irgendein Leser den Text sieht. Das Verb steht dabei nirgends in der Frage — die Schreibweise
genügt, und sie darf irgendwo auf der Zeile stehen. Die dritte und vierte Zeile zeigen, dass die
Blindheit des Gates nicht am Werkzeug hängt: dieselbe Wirkung mit zwei weiteren Schreibweisen,
nur dass `sed` diese Flags nicht annimmt.

Nicht geschlossen — die Reparaturstelle liegt im Kit, siehe H34.

---

## Abschnitt 4 — H36: was ein Faden nicht unterbrechen kann, und wo diese Kette endet

### 4a. Unterbrechbarkeit, gemessen statt angenommen

Ein Faden tickt alle 0,05 s und zählt, wie oft er drankommt:

| Arbeit | Dauer | Ticks | erwartet |
|---|---|---|---|
| `gate_write_scope._HEREDOC_RX` über 80 005 Zeichen | 8,07 s | **1** | ~161 |
| `_harness.substituted_lines` über 1200 Öffner | 32,61 s | 517 | ~652 |

Ein einzelner Aufruf nach C gibt den Interpreter nicht zurück; reiner Python-Code tut es.

### 4b. Wo die Kette endet

Zeile: `sed -i "s/a/b/" team-kits/kernel/state.py` + n × `: <<A`. Der erste Heredoc verschluckt den
Rest, `sed` läuft trotzdem.

| Zeilen | Zeichen | Shell | Gate |
|---|---|---|---|
| 500 | 3 042 | schreibt die Datei | rc 2 nach 0,2 s |
| 4 000 | 24 042 | **schreibt die Datei** | rc 2 nach 0,6 s |
| 6 000 | 36 042 | lässt sich nicht mehr starten | rc 2 nach 1,1 s |
| 20 000 | 120 042 | lässt sich nicht mehr starten | rc 2 nach 8,6 s |
| 80 000 | 480 042 | lässt sich nicht mehr starten | rc 2 nach **129,5 s** |

Die Frist reißt erst bei rund 480 000 Zeichen — und ab rund 32 000 Zeichen bricht die
Prozesserzeugung dieses Hosts mit „Der Dateiname oder die Erweiterung ist zu lang" ab, es läuft also
nichts mehr. Beides zusammen ist der Grund für das Urteil „Rest, keine Angriffskette auf diesem
Host". Was es ändern würde, steht in H36.

---

## Abschnitt 5 — die Prüfmenge und was über sie behauptet wurde

Aus der laufenden Tabelle erzeugt (`test_gates.LINE_SHAPES`):

* 1440 Zellen, davon 1098 mit einer Behauptung über die Shell, 342 ohne;
* 547 Zellen, in denen die Shell die geschützte Datei schreibt;
* **64** Zellen Über-Verweigerung, und sie kommen aus genau **acht** Bewegungen:
  `cd into a directory that is not there`, `cd into a relative directory that is not there`,
  `cd to a target this reader cannot name`, `cd to a tilde the quoting keeps`,
  `cd with a second operand the shell rejects`, `cd with an option the shell accepts`,
  `cd with an option the shell rejects`, `pushd with a second operand the shell rejects`.

Der Eintrag H30 nannte davon vier nicht (`cd with a second operand …`, `cd with an option the shell
rejects`, `cd to a tilde the quoting keeps`, `pushd with a second operand …` — zusammen 32 der 64
Zellen) und nannte zwei Dinge, die **keine** solche Zelle haben: die Deskriptor-Verdopplung (die
Tabelle führt sie überhaupt nicht) und die Wörter, die die Kits vor dem Befehlsnamen überspringen
(deren Zellen behaupten über die Shell **nichts**, was etwas anderes ist als „schreibt nicht"). Die
beiden Zahlen stimmten. Seit TSK-0021 wird die Aussage aus der Tabelle erzeugt und in beiden
Richtungen verglichen.

**Und die Prüfmenge ließ sich still beschneiden.** Gemessen in einem Klon **ohne** den Stolperdraht
dieser Runde: `POSITIONS`, `MOVES` und `LOOSE_SHAPES` auf je die ersten **zwei** Einträge gekürzt —
die Tabelle geht von **1440 auf 100 Zellen**. Der volle Lauf über diesen Klon meldete danach
**111 bestanden, 6 gescheitert, 13 Fehler**, und die 19 sind Zeile für Zeile dieselben, die die
beschädigte `team-kits/kernel/state.py` erzeugt (Abschnitt 6) — 111 + 6 + 13 = 130, also **exakt**
die Zahl des Referenzlaufs vor der Kürzung. Die Kürzung hat **nichts** rot gemacht. Der Grund: die
vorhandenen Tripwires decken die **erzeugten** Achsen (`_verb_shapes`, `_prefix_shapes`,
`_substitution_shapes`), nicht die von Hand geschriebenen Werte.

Seit TSK-0021 nennt jeder geschlossene Eintrag, dessen roter Test diese Tabelle ist, die Werte, auf
denen er steht, und `test_every_cell_a_closed_hole_names_is_one_the_table_carries` prüft beide
Enden. Gemessen mit je einer Mutation im Klon:

| Mutation | Antwort |
|---|---|
| `LOOSE_SHAPES["a write behind a backgrounded read"]` gelöscht | rot: „H26 names `a write behind a backgrounded read`, and no value of the cross table is spelled that way" |
| die `**Zellen…**`-Zeile von H27 entfernt | rot: „these entries … name no value of it: ['H27']" |
| eine Bewegung in H30 umbenannt | rot: `test_the_hole_list_states_the_over_refusal_the_table_carries`, „Extra items in the right set" |
| eine Bewegung in H30 weggelassen | rot, dasselbe, mit der weggelassenen Bewegung benannt |
| „1440" in H30 zu „1441" | rot: `assert [64, 1441] == [64, 1440]` |

---

## Abschnitt 6 — ein Befund am Arbeitsbaum, der nicht zu dieser Aufgabe gehört

Gemessen 2026-08-07 um 13:26 (Forensik-Skript über alle 152 Python-Dateien des Repos):
`team-kits/kernel/state.py` im **Arbeitsbaum** ist beschädigt und nicht mehr parsebar
(`SyntaxError`, Zeile 236). `git diff --numstat` zeigt **928 Zeilen geändert von 928** gegenüber dem
Index; das Muster ist das erste `a` jeder Zeile durch `b` ersetzt, also genau eine Ausführung von
`sed -i "s/a/b/" team-kits/kernel/state.py` — die Schreibzeile, mit der die Gates gemessen werden.
mtime der Datei: **13:14:36**; mtime von `.git/index`: 13:13:11. Keine andere Python-Datei des Repos
ist betroffen.

`team-kits/**` ist für TSK-0021 **verbotener Bereich**, und der Arbeitsbaum ist der Zustand — daher
wurde hier **nichts** zurückgesetzt. Für die Messungen dieser Runde wurde die Datei **nur im Klon**
durch ihren gestageten Inhalt ersetzt (`clone.py --repair-state`, `git show :team-kits/kernel/state.py`,
71 160 Byte); der Arbeitsbaum blieb unberührt.

**Was das für die Abnahme dieser Runde heißt, gemessen statt behauptet:**

| Baum | Ergebnis |
|---|---|
| Repo, 12:56 (vor der Beschädigung, ohne diese Änderung) | **130 bestanden** in 300,8 s |
| Klon mit dieser Änderung, `state.py` aus dem Index | **134 bestanden** in 308,1 s |
| Repo, nach dem Einbau (`state.py` beschädigt) | 115 bestanden, **6 gescheitert, 13 Fehler** |
| Klon **ohne** diese Änderung, `state.py` beschädigt, dieselben 19 ausgewählt | **6 gescheitert, 13 Fehler** — Zeile für Zeile dieselben |

Die letzte Zeile ist der Punkt: die 19 roten Ergebnisse im Repo stehen **ohne** diese Änderung genau
so da. Jedes einzelne trägt `invalid syntax (state.py, line 236)`; keines sagt etwas über die Gates.
`python -m ruff check .` meldet aus demselben Grund 70 Fehler, **alle** in dieser einen Datei
(`python -m ruff check .claude/` ist sauber).

---

## Abschnitt 7 — der Befund über die Messvorrichtung, und was dagegen gebaut wurde

**Der Mechanismus, unabhängig davon, wer die Zeile gefahren hat:** jede Zeile dieser Prüfmenge nennt
ihr Ziel **relativ** (`test_gates.RELATIVE_WRITE` = `sed -i "s/a/b/" team-kits/kernel/state.py`), und
was sie vom echten Baum fernhält, ist **allein** das `cwd=` an einer Stelle
(`_changes_the_protected_file`). Eine Zeile, die eine **Verweigerung beweisen** soll, ist genau dann
gefährlich, wenn der Beweis misslingt: verweigert das Gate sie nicht, läuft sie. Eine Vorrichtung,
deren Fehlschlag den geprüften Baum verändert, misst nicht.

**Welche Zeilen meiner eigenen Vorrichtung einen echten Repo-Pfad nennen — vollständig:**

| Ort | Form | Ausgeführt von |
|---|---|---|
| `test_gates.RELATIVE_WRITE` und jede Zelle, die es einsetzt | relativ, `cwd=` Sandbox | echte Shell |
| `test_gates._can_arbitrate` → `_changes_the_protected_file` | dieselbe Zeile, einmal je Shell-Kandidat | echte Shell |
| meine Zusatzskripte (`m1/shell.py`, `m1/chain.py`, `m1/prose.py`, `m1/heredoc.py`) | dieselbe relative Form, `cwd=` eigene Sandbox | echte Shell |
| `m1/lines.json`, die Tilde-Sonden | nennt `.claude/settings.json`, `.claude/hooks/_harness.py`, `project_memory/…` | **nur** der Gate-Prozess, nie eine Shell — ein Gate führt nichts aus |

Die letzte Zeile ist die harmlose Klasse; die ersten drei sind die, die auf `cwd=` stehen.

**Was gebaut wurde:** ein Riegel, der die Vorrichtung an ihrem eigenen Fehlschlag misst statt an
ihrer Sorgfalt — `the_repo_is_not_a_sandbox` in `.claude/hooks/test_gates.py`, eine
`autouse`-Sitzungsvorrichtung. Die Wachliste ist **abgeleitet**, nicht getippt: eine Sandbox wird
gebaut, der Helfer, der sie befüllt, läuft einmal darin, und jeder Pfad, den sie danach enthält, wird
in `ROOT` nachgeschlagen und vorher/nachher gehasht. Beide Enden:

* **Rot, wenn ein Lauf ausbricht** — gemessen mit einem Test **innerhalb** von `test_gates.py`, der
  eine Zeilenform mit `cwd=ROOT` statt mit einer Sandbox fährt: `AssertionError: these files of THIS
  repo changed while the suite ran: ['team-kits/kernel/state.py']`.
* **Rot, wenn er nichts bewacht** — der erste Entwurf leitete die Wachliste allein aus `_sandbox`
  ab; die legt `docs/note.md` an, nicht die geschützte Datei, und dieses Repo hat kein
  `docs/note.md`. Der Riegel war grün, während der ausbrechende Lauf den Baum wirklich umschrieb.
  Die Zusicherung, dass **mindestens ein** bewachter Pfad in `ROOT` überhaupt existiert, ist die
  Lehre daraus und steht jetzt im Riegel.

**Was er nicht kann:** er unterscheidet nicht, ob diese Suite den Baum geschrieben hat oder ein
anderer Agent währenddessen. Die Meldung sagt beides. Und er gilt nur für Läufe **dieser** Datei —
ein Skript daneben (wie meine `m1/*.py`) fällt nicht darunter; für die bleibt die Regel, die Sandbox
absolut zu adressieren.

**Was ich zur Ursache am 13:14:36 sagen kann und was nicht.** Nicht: wer die Zeile gefahren hat. Ich
finde in meiner Vorrichtung keinen Aufruf mit `cwd=` auf dem Repo — alle laufen gegen
`m1/<name>-sand` oder gegen ein Stellvertreterprojekt —, aber „ich finde keinen" ist kein Beweis.
Gemessen ist: das Scratchpad-Verzeichnis wird **geteilt** (Dateien, die ich nicht geschrieben habe,
erscheinen darin um 13:16:12, 13:17:33, 13:23:14, 13:38:42 …, also mitten in meinen Aufrufen), und
`git status --porcelain` zeigt genau **eine** betroffene Datei — nicht `docs/note.md`, das dieselbe
Vorrichtung ebenfalls beschreibt. Beides passt zu genau **einem** Lauf der Zeile mit falschem `cwd`,
sagt aber nicht, aus welchem Prozess. Deshalb der Riegel: die nächste Ausführung dieser Art wird
benannt, statt gesucht.
