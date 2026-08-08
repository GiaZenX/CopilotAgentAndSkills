# Messprotokoll TSK-0022 (2026-08-07) — Nachbesserung von TSK-0021

Alles hier ist gegen **laufende Prozesse** gemessen: das Gate als echter Prozess mit JSON auf stdin
gegen ein Stellvertreterprojekt **außerhalb** dieses Repos, und eine echte Shell als Schiedsrichter
über die **Datei** — die geschützte Datei trägt vor jeder Zeile `a`, und was zählt, ist, ob sie
danach etwas anderes trägt. Ein Rückgabecode ist kein Beleg dafür, wo eine Shell steht.

Vorher/Nachher wird an **zwei Klonen** gemessen (`clone-before` = Stand TSK-0021, `clone-after` =
dieser Stand), beide außerhalb des Repos. Der Klon baut sein eigenes Stellvertreterprojekt: ein
Projekt, das von einem anderen Klon gebaut wurde, antwortet mit **dessen** Gates — das ist beim
ersten Nachher-Lauf passiert und hat den Fix als wirkungslos ausgewiesen, bis die Vorrichtung den
Klonnamen in den Projektnamen aufnahm.

Betroffene Löcherlisten-Einträge: **H31**, **H33**, **H37**.

---

## Abschnitt 0 — die Messdisziplin, gebaut statt versprochen

Jedes Skript dieser Runde importiert `guard.py` (Sandbox `%TEMP%/tsk0022`) und tut zwei Dinge,
bevor eine Nutzlast läuft:

* `guard.pin()` — betritt das Arbeitsverzeichnis **absolut**, liest es zurück und bricht ab, wenn es
  nicht unter der Sandbox oder wenn es unter dem Repo liegt;
* `guard.watch(lines)` — hasht vor und nach dem Lauf jede Datei des **echten** Repos, die eine der
  Zeilen benennen kann. Die Wachliste ist aus den Zeilen **abgeleitet** (dieselbe großzügige
  Pfadklasse, die auch das Gate benutzt), nicht getippt; bei einer Differenz endet der Lauf mit
  `REPO DAMAGED by this measurement run`.

Jeder Messlauf unten meldet darum eine Zeile `[guard] n files of C:\Offline Repos\AgentAndSkills
unchanged`. Warum das nicht genügt und was wirklich schützt, steht in Abschnitt 3.

---

## Abschnitt 1 — F1: die Quotierung hinter dem Präfix (H33, zweite Kette)

Ein Werkzeugaufruf, keine Vorbereitung, Payload `Bash`, Schiedsrichter
`C:\Program Files\Git\usr\bin\bash.exe` über die Datei.

| Zeile | Shell schreibt | vorher | nachher |
|---|---|---|---|
| `sed -i "s/a/b/" team-kits/kernel/state.py` | ja | rc 2 | rc 2 |
| `sed -i "s/a/b/" ~+/team-kits/kernel/state.py` | ja | rc 2 | rc 2 |
| `sed -i "s/a/b/" ~+/"team-kits"/kernel/state.py` | **ja** | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/'team-kits'/kernel/state.py` | **ja** | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/team-kits/"kernel"/state.py` | **ja** | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/team-kits/kernel/"state.py"` | **ja** | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/".claude"/settings.json` | (Datei fehlt in der Sandbox) | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/.claude/"hooks/_harness.py"` | (dito) | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" ~+/"project_memory"/…/DEC-0020.yaml` | (dito) | **rc 0** | **rc 2** |

Die Begründung der neuen Verweigerungen nennt das Wort: *„a word this line writes could not be
placed: `~+/team-kits/kernel/state.py`. this word carries the tilde prefix `~+` …"*.

### 1b. Die Gegenrichtung, die **nicht** kippen durfte

| Zeile | Shell schreibt | vorher | nachher |
|---|---|---|---|
| `sed -i "s/a/b/" ~"+"/team-kits/kernel/state.py` | nein | rc 0 | rc 0 |
| `sed -i "s/a/b/" "~+"/team-kits/kernel/state.py` | nein | rc 0 | rc 0 |
| `sed -i "s/a/b/" ~/"team-kits"/kernel/state.py` | nein (Heimatverzeichnis) | rc 0 | rc 0 |
| `sed -i "s/a/b/" ~+"/team-kits"/kernel/state.py` | **nein** | rc 0 | rc 0 |
| `sed -i "s/a/b/" "team-kits"/kernel/state.py` | ja | rc 2 | rc 2 |
| `cd "~" ; sed -i "s/a/b/" team-kits/kernel/state.py` | ja | rc 2 | rc 2 |
| `cd ~"+" ; sed -i "s/a/b/" team-kits/kernel/state.py` | ja | rc 2 | rc 2 |

Die vierte Zeile ist die, die die Regel bestätigt: das Trennzeichen steht **in** der Quotierung, das
Präfix endet also am ersten **unquotierten** Trennzeichen und trägt dann selbst Quotierung — `bash`
lässt das Wort literal, und das Gate erlaubt es. Der Leser bekommt dieselbe Antwort geschenkt, weil
die Maskierung der Kits das quotierte `/` unsichtbar macht.

### 1c. Was das kostet (Über-Verweigerung, gemessen)

| Zeile | Shell schreibt | nachher |
|---|---|---|
| `sed -i "s/a/b/" ""~+/team-kits/kernel/state.py` | nein | **rc 2** |
| `sed -i "s/a/b/" ''~+/team-kits/kernel/state.py` | nein | **rc 2** |
| `sed -i "s/a/b/" x=~+/team-kits/kernel/state.py` | ~~nein~~ **ja, erweitert** | ~~rc 2~~ **rc 0** — siehe Runde 2, Abschnitt 9 |
| `sed -i "s/a/b/" ~jemand/team-kits/kernel/state.py` | nein | rc 2 (auch vorher) |

Die ersten beiden sind neu und stehen so in H31: eine führende Tilde **hinter** einer Quotierung ist
für diesen Leser nicht verortbar, also verweigert er — die Shell lässt sie literal.

**Die dritte Zeile war falsch, und zwar in beiden Spalten.** Sie ist am 2026-08-08 gegen ein
Stellvertreterprojekt **außerhalb** des Heimatverzeichnisses neu gemessen worden: das Gate antwortet
**rc 0**, und `bash` **erweitert** `x=~+/y`. Die rc 2 dieser Runde kam aus der Lage der Messung
(Stellvertreterprojekt unter `%TEMP%`, also unter dem Heimatverzeichnis) und nicht aus dem Wort.
Abschnitt 9 trägt die Messung, den Mechanismus und die Korrektur.

---

## Abschnitt 2 — F3: die Achse, die fehlte, und der rote Lauf

`test_gates.TILDE_SUBJECTS` kreuzt jetzt drei Achsen: 3 Zustände × 157 Präfixe × die Stellen, an
denen Quotierung im Zielwort stehen kann. Die dritte Achse ist **erzeugt** (`_quotings`): quotierbar
sind die Läufe, in die die Trennzeichen das Wort schneiden, und ein führendes `~` öffnet einen Lauf
für sich (`_quotable_runs`); die Schreibweisen kommen aus `shlex.quotes` und dem Escape desselben
Lesers. Das ergibt **7527** Subjekte gegen vorher **471**, von denen **keines** Quotierung im
Zielwort trug.

Dazu neun Zellen der gekreuzten Tabelle über den **gewöhnlichen** relativen Schreibzugriff
(`_quoted_write_shapes`) — dieselbe Achse ohne Tilde, damit ein Leser, der seine Verweigerungen
durch Verweigern von Quotierung kauft, an der anderen Seite rot wird. Die Tabelle wächst von 1440
auf **1449** Zellen; die Über-Verweigerung bleibt bei 64.

**Rot ohne den Fix** (Klon `clone-red2`: neue Prüfmenge, `_harness.readings` auf die Fassung von
TSK-0021 zurückgedreht):

```
FAILED test_gate1_places_a_tilde_word_where_the_shell_puts_it
  61 Zellen, alle mit „the shell writes the protected file, the gate answered rc 0", darunter
  `~+` with nothing behind it, with the span 1 separators in quoted by "
  `~-` after a move out of the tree, with the span 2 separators in quoted by '
  `~-` after a push out of the tree, with the span 3 separators in quoted by "
```

Mit dem Fix ist derselbe Test grün. Der Test fragt das Gate nur noch dort, wo er etwas behauptet
(wo die Shell schreibt, und für das leere Präfix in jeder Quotierung und jedem Zustand) — vorher lief
je ein Gate-Prozess pro Subjekt und die Antwort wurde für fast alle weggeworfen.

---

## Abschnitt 3 — H37: die Messvorrichtung schrieb den Baum, den sie misst

**Das ist der wichtigste Befund dieser Runde, und er ist während dieser Runde entstanden.** Beim
ersten Lauf der neuen Prüfmenge aus dem Repo heraus schlug der Sitzungsriegel an:

```
ERROR ... AssertionError: these files of THIS repo changed while the suite ran:
['team-kits/kernel/state.py']
```

`git diff --numstat` danach: 928 von 928 Zeilen, Muster „erstes `a` je Zeile → `b`", `SyntaxError`
in Zeile 236 — dieselbe Signatur wie am 2026-08-06 und am 2026-08-07 vormittags. **Dritter Treffer,
und diesmal mit dem Mechanismus statt einer Vermutung.**

Isoliert, ohne pytest, in zwei leeren Bäumen:

```
cwd = <sandbox>,  OLDPWD = <ein anderer Baum>
printf "%s\n" ~ ~+ ~- ~0 ~1 ~+0 ~-0
  ~   → /c/Users/zenti
  ~+  → <sandbox>
  ~-  → <der andere Baum>          ← hier
  ~0  → <sandbox>   ~1 → literal   ~+0/~-0 → <sandbox>
sed -i "s/a/b/" ~-/team-kits/kernel/state.py     → die Datei im ANDEREN Baum trägt danach `b`
```

Eine Tilde löst nicht gegen `cwd` auf, sondern gegen den Zustand der Shell, und `PWD`/`OLDPWD`
kommen über die **Umgebung** herein. Eine Suite, die im Baum gestartet wird, den sie misst — genau
so, wie `CLAUDE.md` es vorschreibt —, reicht diesen Baum in `OLDPWD` weiter; `~-` ist ein Subjekt
der Prüfmenge. Das `cwd=` war jedes Mal richtig. Die beiden früheren Schäden wurden einem Skript im
falschen Verzeichnis zugeschrieben; das war nie die ganze Antwort.

**Geschlossen:** `_changes_the_protected_file` **setzt** `PWD` und `OLDPWD` auf die Sandbox.
**Rot ohne den Fix** (Klon, Fix entfernt):

```
FAILED test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads
  a line of this check set reached …/a-tree-this-suite-must-not-reach, which is not the sandbox
  it was given
  assert 'b' == 'a'
```

Mit dem Fix grün (7,6 s). Der Test zeigt `PWD`/`OLDPWD` absichtlich auf einen dritten Baum und fährt
**jedes** Präfix des Alphabets; die zweite Hälfte verlangt, dass mindestens ein Präfix die
**eigene** Sandbox-Datei erreicht, damit die erste nicht aus Untätigkeit grün ist.

**Was offen bleibt und wo es steht:** ein Messskript **neben** `test_gates.py` fällt nicht unter den
Sitzungsriegel, solange keine Suite läuft. Das ist H37s benannter Rest, mit der Begrenzung, die
diese Runde gebaut hat (Abschnitt 0).

**Was mit dem Arbeitsbaum passiert ist, und was diese Runde daran NICHT getan hat.** Der Schaden
entstand um 2026-08-07 während des ersten Laufs der neuen Prüfmenge aus dem Repo heraus; danach war
`team-kits/kernel/state.py` nicht mehr parsebar. Zurückgesetzt wurde er **nicht von hier**:
`team-kits/**` ist für dieses Item verbotener Bereich, und ein Rücksetzen ist die Entscheidung des
Nutzers. Alle Suite-Läufe unten sind darum in einem **Klon** gefahren, dessen `state.py` aus dem
**Index** stammt (`git show :team-kits/kernel/state.py`, 71 160 Byte). Gegen Ende dieser Runde war
die Datei im Arbeitsbaum wieder heil (`git status` = nur gestaged, `import kernel.state` OK,
`ruff`/`validate` sauber) — wiederhergestellt hat sie jemand anders. Falls sie wieder zerschrieben
angetroffen wird, ist der Weg dieser, aus einer Shell **außerhalb** von Claude Code:

```bash
cd "C:/Offline Repos/AgentAndSkills"
git checkout -- team-kits/kernel/state.py
PYTHONPATH=team-kits python -B -c "import kernel.state; print('OK')"
```

---

## Abschnitt 4 — die PowerShell-Hälfte (vom Prüfer ungemessen gelassen)

`powershell.exe -NoProfile -NonInteractive`, cwd = Sandbox, Payload `PowerShell`:

```
Write-Output ~      → ~
Write-Output ~+     → ~+
Write-Output ~+/"team-kits"  → ~+/team-kits
Write-Output ~"+"/team-kits  → ~+/team-kits
Write-Output "~"    → ~
```

PowerShell erweitert `~+` **gar nicht**, und keine der Tilde-Zeilen erreicht die geschützte Datei
(`shell writes: False` für alle). Das Gate antwortet auf die PowerShell-Payload wie auf die
Bash-Payload: die vier quotierten Formen kippen von **rc 0 auf rc 2**. Für PowerShell ist das
**Reibung, kein geschlossenes Loch** — dieselbe Über-Verweigerung, die H33 für jedes nicht
auflösbare Präfix benennt. `Set-Content -Path "team-kits"/kernel/state.py -Value x` schreibt in
PowerShell nichts (Parserfehler) und wird trotzdem verweigert; auch das ist Reibung.

---

## Abschnitt 5 — die Gate-3-Kette der F1-Schreibweise, und der Vorbehalt des Prüfers

### 5a. Bis zum Commit gemessen

Stellvertreterprojekt mit **gültigem Urteil** (durch den Kernel aufgezeichnet, die Abhilfe des Gates
selbst), dann je Zeile Gate 1 und Gate 3, und wo beide erlauben, die Zeile wirklich gefahren; danach
`docs/note.md` gelesen und `git rev-parse HEAD` verglichen:

| Zeile | Gate 1 vorher/nachher | Gate 3 | gelaufen | vergiftet | HEAD bewegt |
|---|---|---|---|---|---|
| `git commit -am wip` | 0 / 0 | 0 | ja | nein | **ja** |
| `sed -i "s/prose/POISON/" docs/note.md ; git commit -am wip` | 0 / 0 | **2** | nein | nein | nein |
| `sed -i … ~+/"docs"/note.md ; git commit -am wip` | **0 / 2** | **2** | nein | nein | nein |
| `git commit -am wip $(sed -i … ~+/"docs"/note.md)` | **0 / 2** | **2** | nein | nein | nein |
| `git commit -am "wip $(sed -i … ~+/docs/note.md)"` | 2 / 2 | 2 | nein | nein | nein |

**Befund:** Gate 3 war an dieser Kette nie das Loch — es verweigert die committende Zeile schon
vorher, weil eine Stufe davor nicht nachweislich nur liest. Was die F1-Schreibweise vorher öffnete,
war der **Schreibzugriff** (Gate 1 rc 0), nicht der Commit in derselben Zeile. Beides ist jetzt
rc 2.

### 5b. Der Vorbehalt: `bash -c` gegen den Bash-Werkzeugpfad des Providers

Der Prüfer hat F1 mit `bash -c` aus einem Python-Prozess gemessen und den Übergabeweg des Providers
offengelassen. Gemessen über das **Bash-Werkzeug dieser Sitzung selbst** (eine rein lesende Zeile,
die das Gate erlaubt), cwd = dieses Repo:

```
echo ~+                → /c/Offline Repos/AgentAndSkills
echo ~+/"team-kits"    → /c/Offline Repos/AgentAndSkills/team-kits     ← die Kette
echo ~"+"/team-kits    → ~+/team-kits
echo "~"               → ~
echo ~                 → /c/Users/zenti
$0 = /usr/bin/bash, BASH_VERSION = 5.2.37(1)-release
```

Die zweite Zeile ist die Antwort: **auf dem Werkzeugpfad des Providers erweitert die Shell genau
so.** Der Vorbehalt ist damit erledigt, und die Kette lief nicht nur unter `bash -c`.

---

## Abschnitt 6 — F2: die Prosa, die etwas anderes behauptete als der Code baut

| Stelle | Was dort stand | Was jetzt dort steht |
|---|---|---|
| `_harness.readings` | „that direction only ever adds a refusal" für `~/"x"` | die Frage wird an die **getippte** Lesart gestellt; wo die Quotierung steht, entscheidet; was der Fallback kostet, steht mit der Zelle daneben, die ihn bemerken würde |
| `POST_V2_WISHLIST` H31 | `~/"x"` sei Über-Verweigerung | falsch in beide Richtungen, ersetzt: `~/"x"` wird erweitert wie in einer Shell (gemessen), Über-Verweigerung bleibt für `""~+/…` und `x=~+/…` (gemessen) |
| `POST_V2_WISHLIST` H33 | „blockierend, geschlossen" ohne die zweite Kette | zweite Kette mit Messung, neues Urteil, und die **Subjekte** der Prüfmenge, gegen die Prüfmenge geprüft |
| `CLAUDE.md` (dritte Ausnahme) | Tilde-Präfix wird verweigert — ohne ein Wort zur Quotierung | die Eigenschaft steht da, mit dem Satz, der bis 2026-08-07 danebenlag, und der gemessenen Zeile |

Neu ist außerdem, dass die Prosa **geprüft** wird statt nur korrigiert:
`test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries` erzeugt Größe und Achse
der Tilde-Prüfmenge aus der Prüfmenge und vergleicht sie in **beide** Richtungen mit dem, was H33
behauptet. Gemessen im Klon:

| Mutation | Antwort |
|---|---|
| den `**Subjekte…**`-Absatz aus H33 entfernt | rot: „these entries say the tilde check set is what would notice their defect and state nothing about it, so it can be cut back to what they were measured against: ['H33']" |
| ein Zeichen aus dem Präfix-Alphabet gestrichen | rot: „H33 says the tilde check set is 7527 / 3 / 157; it is 7431 subjects out of 3 states and 155 prefixes" |
| eine Quotierung aus der **Achse** gestrichen | rot: „… it is 7056 subjects out of 3 states and 157 prefixes" |
| eine Quotierung aus dem **Eintrag** gestrichen (Zahlen bleiben richtig) | rot: „H33 names quotings the check set does not carry: [] -- and leaves these unnamed: ['with the tilde itself escaped']" |

Und die Zusicherung, die `_harness.readings` über seinen eigenen **Rückfall** macht („ein Wort ohne
getippte Lesart bekommt die Antwort von vor H31, und die Zelle, die das bemerkt, ist
`cd to a tilde the quoting keeps`"), ist ebenfalls gemessen statt behauptet. Im Klon `clone-mut5`
setzt `tokenise` die Lesart nicht mehr:

```
FAILED test_gate1_refuses_a_line_exactly_where_the_shell_would_write
  AssertionError: cd to a tilde the quoting keeps -- after a group that closed -- …
FAILED test_the_words_this_reader_reads_are_the_kits_own_tokens
  AssertionError: a word without a typed reading in '! cd "/out" & sed -i "s/…
```

Genau die benannte Zelle, und der Tokens-Test daneben, der denselben Ausfall direkt meldet.

---

## Abschnitt 7 — Suite

`clone-ship` ist ein Klon außerhalb des Repos, mit dem Arbeitsbaum **byte-identisch** (sha256 der
geänderten Dateien verglichen) bis auf eine Docstring-Korrektur in `_harness._quoting_in`, die
danach kam; der Lauf im Arbeitsbaum selbst deckt sie ab.

| Lauf | Baum | Ergebnis |
|---|---|---|
| `pytest .claude/hooks/test_gates.py -q` | **Arbeitsbaum** | **137 bestanden** in 1014 s — und `team-kits/kernel/state.py` danach unverändert und importierbar, also derselbe Lauf, der die Datei vorher zerschrieben hat |
| `pytest .claude/hooks/test_gates.py -q` | `clone-ship` | **137 bestanden** in 1043 s |
| `pytest tools/ -q` | `clone-ship` | **2305 bestanden, 12 übersprungen** in 1743 s |
| `python -m ruff check .` | `clone-ship` | sauber |
| `python tools/validate.py` | `clone-ship` | „all structural checks passed" |
| `pytest … -k "arbiter or kits_own_tokens or tilde_subject or hole_list"` | **Arbeitsbaum** | 6 bestanden in 42 s |
| `python -m ruff check .` / `tools/validate.py` | **Arbeitsbaum** | sauber / bestanden |

Zwei Nebenbefunde über die Messvorrichtung, damit die Zahlen nachvollziehbar sind:

* eine Kopie **ohne** `.git` lässt `tools/test_migrate.py` mit 90 Fehlern abbrechen („git could not read
  this repository's history"); die Kit-Suite braucht echte Historie;
* eine Kopie **mit** `.git` bricht genauso ab, solange sie die Referenz
  `refs/codex/turn-diffs/…` mitkopiert, deren Objekt nicht im Klon liegt — `git log --all` scheitert
  daran. Nach dem Entfernen **dieser Referenz im Klon** (nicht im Repo) sind es 0 Fehler. Die 3
  „failed" aus dem ersten Lauf hatten dieselbe Ursache.

`python -B -m pytest tools/ -q` ist damit gemessen, obwohl diese Runde keinen Kit-Pfad anfasst:
geändert sind nur `.claude/hooks/**`, `CLAUDE.md` und `docs/**`, und `tools/` liest davon allein die
`L…`-Einträge der Löcherliste (Abschnitt 11, unberührt).

**`bump_kit_version.py` wurde NICHT gefahren** — kein Kit trägt eine Änderung dieser Runde; die
Spiegelprüfung entfällt aus demselben Grund.

---

## Abschnitt 8 — was diese Runde **nicht** geschlossen hat

* **H37s Rest:** ein Messskript neben der Suite ist von keinem Riegel bewacht, solange keine Suite
  läuft. Begrenzung: die Disziplin aus Abschnitt 0, im Eintrag benannt.
* **`team-kits/kernel/state.py` im Arbeitsbaum** ist zerschrieben und wurde **nicht** zurückgesetzt
  (verbotener Bereich, Entscheidung des Nutzers). Befehl in Abschnitt 3.
* **H34** (Prosa-Entfernung der Kits) und **H22** bleiben, wie sie waren — Reparaturstelle im Kit,
  außerhalb dieses Items.
* **Die PowerShell-Reibung** aus Abschnitt 4 ist benannt, nicht behoben: das Gate verweigert dort
  Formen, die PowerShell gar nicht erweitert.

---

# Runde 2 (2026-08-08) — Nachbesserung nach dem zweiten Prüfverdikt

Der Kern der Runde 1 ist vom Prüfer unabhängig bestätigt und **nicht angefasst**. Was hier steht,
sind die vier Befunde des Verdikts (`project_memory/staging/TSK-0022/verdict-round2-2026-08-08.md`)
und der fünfte, den der Sitzungsagent nachgemessen hat.

**Die Messdisziplin dieser Runde, und was an ihr neu ist.** Sandbox `C:\tsk0022r2` — **außerhalb
des Repos und außerhalb des Heimatverzeichnisses**, was in Runde 1 nicht galt und der Grund für F1
ist. Jedes Skript importiert `.claude/hooks/_sandbox.py` (neu, siehe Abschnitt 10): `pin()` setzt
`PWD`/`OLDPWD` und entfernt `DIRSTACK` in `os.environ`, also in jedem Kindprozess, und `watch()`
hasht die **geschützte Menge** des echten Repos vor und nach jedem Lauf. Jeder Lauf unten meldet
darum eine Zeile `[sandbox] N protected files of C:\Offline Repos\AgentAndSkills unchanged`; keiner
dieser Läufe hat den Arbeitsbaum bewegt. `N` ist aus dem Baum **abgeleitet** und darum nicht
konstant — an diesem Tag 457 und später 445: die Menge enthält auch Bytecode-Reste unter
`team-kits/`, weil `ProtectedArea.verdict` sie ebenso schützt (gemessen:
`team-kits/kernel/__pycache__/state.cpython-313.pyc` → *the session agent*).

---

## Abschnitt 9 — F1: eine Zeile, die „verweigert" sagte, wo das Gate erlaubt

**Der Mechanismus, und er ist allgemeiner als die eine Zeile.** Ein Wort, dessen Tilde **nicht** am
Wortanfang steht, ist für `_harness._expanded` kein Tilde-Wort — die ganze Lesart geht unverändert
durch. Was übrig bleibt, ist der Substring-Scan (`_harness._PATHISH`), und dessen Zeichenklasse
trägt weder `=` noch `+`: aus `x=~+/team-kits/kernel/state.py` bleiben die Spannen `x`, `~` und
`/team-kits/…`. Die mittlere ist ein bloßes `~`, und **das** wird erweitert — zum
Heimatverzeichnis. Liegt das Stellvertreterprojekt **unter** dem Heimatverzeichnis, dann *enthält*
dieser Kandidat geschützten Zustand und wird für die Enthaltung verweigert (H19). Genau das war die
rc 2 der Vorrunde: gemessen wurde ein **Vorfahre**, nicht die Eigenschaft.

**Beide Lagen, sonst identisch, ein Werkzeugaufruf, `bash` als Schiedsrichter über die Datei:**

| Zeile | Shell schreibt | Projekt außerhalb `~` | Projekt unter `~` |
|---|---|---|---|
| `sed -i "s/a/b/" ~+/team-kits/kernel/state.py` | ja | rc 2 | rc 2 |
| `sed -i "s/a/b/" x=~+/team-kits/kernel/state.py` | **nein** | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" x=~/team-kits/kernel/state.py` | nein | rc 0 | rc 0 |
| `sed -i "s/a/b/" ""~+/team-kits/kernel/state.py` | nein | rc 2 | rc 2 |
| `sed -i "s/a/b/" ''~+/team-kits/kernel/state.py` | nein | rc 2 | rc 2 |
| `sed -i "s/a/b/" --file=~+/team-kits/kernel/state.py` | nein | **rc 0** | rc 2 |
| `sed -i "s/a/b/" ~\+/team-kits/kernel/state.py` | nein | **rc 0** | rc 2 |

Und was `bash` selbst tut, denn die zweite Hälfte des Satzes war auch falsch:

```
printf "%s\n" x=~+/y        -> x=/c/tsk0022r2/work/run/y      ← ERWEITERT
printf "%s\n" --file=~+/y   -> --file=~+/y                    ← literal
printf "%s\n" ""~+/y        -> ~+/y                           ← literal
printf "%s\n" ~\+/y         -> ~+/y                           ← literal
```

**Korrigiert:** `docs/POST_V2_WISHLIST.md` H31 (der Fall steht jetzt mit Messung, Mechanismus und
der Prüfmenge dort), H33 (die falsche Klammer entfernt, mit Verweis auf H31), und die Zeile in
Abschnitt 1c dieses Protokolls.

**Die Zelle ist jetzt ein erzeugtes Subjekt statt eines Satzes.**
`test_gate1_answers_for_a_tilde_that_does_not_start_its_word` kreuzt zwei erzeugte Achsen: die
**Vorläufe** (`_tilde_leads` — die leere Spanne, die jedes Anführungszeichen des Lesers bilden kann,
und jedes Zeichen aus `_word_alphabet`) gegen die beiden Enden der Präfix-Achse. Die Regel, gegen
die gemessen wird, ist **ein Ausdruck**, keine Liste: nachdem die Shell die Quotierung entfernt hat,
beginnt das Wort mit einer Tilde mit nicht-leerem Präfix — dann verweigert das Gate jedem — oder
nicht. Dazu wird für **jeden** Vorlauf die Shell gefragt, ob sie die geschützte Datei erreicht;
täte sie es bei rc 0, wäre das ein Loch und der Test sagt es. Beide Enden: dieselbe Zeile **ohne**
Vorlauf muss die Datei erreichen **und** rc 2 sein, sonst misst der Rest nichts.

**Die verallgemeinerte Lehre ist gebaut, nicht versprochen:** `test_gates._base_outside_the_home
_directory` legt **jedes** Stellvertreterprojekt außerhalb des Heimatverzeichnisses an (abgeleitete
Kandidaten: Temp-Verzeichnis, Anker des Repo-Pfads, Elternverzeichnis des Repos — der erste, der
weder unter `~` noch unter dem Repo liegt und beschreibbar ist).

**Und ein Defekt, den diese Änderung selbst eingeschleppt hat, gemessen und geschlossen.** Der
neue Basisordner wird nicht mehr von `tmp_path` aufgeräumt, und mein erster Aufräumer war
`shutil.rmtree(..., ignore_errors=True)`: die Objektdateien eines `.git` sind schreibgeschützt,
Windows verweigert deren Löschen, und `ignore_errors` verschluckt genau das — nach einem
Suite-Lauf standen **sieben** Stellvertreterprojekte am Anker (`C:\harness-gates-*`). Jetzt löscht
`test_gates._removed` mit einem `onexc`, der das Schreibschutz-Bit entfernt, und die Fixture
**prüft nach dem Löschen**, dass der Ordner weg ist. Rot ohne den Fix (Klon, `onexc` zurück auf
`ignore_errors=True`):

```
ERROR test_gate1_refuses_a_protected_path_spelled_absolutely_through_a_space
  AssertionError: C:\harness-gates-mfrtz2dl survived the run. This base is not `tmp_path`, so
  nothing else cleans it up …
```

**Rot ohne diese Bau-Entscheidung** (Klon `clone-red-home`, `project`-Fixture zurück auf
`tempfile.gettempdir()`):

```
FAILED test_gate1_answers_for_a_tilde_that_does_not_start_its_word
  lead '!', prefix '!': … so this gate can place it as any other word -- and it answered rc 2
  … dieselbe Meldung für '%', '*', '+', ',', '=', '?', '@', '[', ']', '^'
```

Elf Vorläufe — und zwar genau die, deren Zeichen `_PATHISH` nicht trägt, also die, bei denen das
bloße `~` als eigener Kandidat übrig bleibt.

**Was ich sonst noch auf diese Lage geprüft habe.** Die Tabellen der Abschnitte 1, 1b und 1c sind
außerhalb des Heimatverzeichnisses **vollständig neu gefahren** worden. Alle Zeilen reproduzieren
unverändert; die einzige Abweichung ist die oben korrigierte. Betroffen sein können nur Wörter, bei
denen die Erweiterung erlaubt ist **und** die ganze Lesart kein Tilde-Wort ist — bei jedem Subjekt,
das mit `~<Präfix>` beginnt, entscheidet die ganze Lesart, bevor ein Substring gelesen wird.

---

## Abschnitt 10 — F2: die Vorrichtung, die H37 als Begrenzung nannte, baute sie nicht

Der Prüfer hat beide Hälften der Zusicherung widerlegt, und beide sind hier reproduziert:

* `guard.pin()` pinnte **nur** `cwd`. Kontrolllauf mit Köder-Baum in `PWD`/`OLDPWD`: die
  `~-`-Nutzlast schreibt den Köder (`b`), während der Riegel „unchanged" meldete — **wörtlich der
  Mechanismus von H37**, in der Vorrichtung, die H37 als Begrenzung nannte;
* `guard.named_in()` lieferte für die Rundenzeilen **eine** von vier geschützten Zieldateien.

**Was jetzt an der Stelle steht:** `.claude/hooks/_sandbox.py`, neben der Suite, von ihr **und** von
den Skripten dieser Runde importiert — `test_gates._changes_the_protected_file` setzt seine
Umgebung seit dieser Runde durch `_sandbox.sandbox_environment`, es gibt also **eine** Antwort statt
zweier, die auseinanderlaufen können.

| Frage | vorher | jetzt | Test, der ohne den Fix rot wird |
|---|---|---|---|
| Wo steht ein Kindprozess? | `cwd` | `cwd` **und** `PWD`/`OLDPWD`/`DIRSTACK` in `os.environ`; Sandbox im oder um das Repo wird verweigert — **unvollständig, in Runde 3 korrigiert, siehe Abschnitt 16** | `test_the_measurement_sandbox_pins_every_directory_a_child_shell_reads` (in Runde 3 ersetzt) |
| Was darf sich nicht bewegen? | Spannen-Scan über die Zeilen (1 von 4 Dateien) | die **geschützte Menge** (`ProtectedArea.verdict` über die Bereiche, die das Objekt selbst nennt) — 457 Dateien in diesem Repo | `test_the_measurement_watch_list_is_the_area_the_gate_protects` |
| Wohin darf eine Reparatur schreiben? | nirgends geprüft (`repair.py` prüfte den **Prozess**) | das **Ziel** muss unter der gepinnten Sandbox liegen | `test_an_index_restore_refuses_a_target_outside_the_pinned_sandbox` |

**Rot gesehen** (Klon `clone-red-f2`, je ein Defekt einzeln wiederhergestellt, danach zurückgesetzt):

```
1) pin() ohne die Umgebungszeilen
FAILED test_the_measurement_sandbox_pins_every_directory_a_child_shell_reads
  AssertionError: a payload run after `pin()` reached …\a-tree-this-apparatus-must-not-reach,
  which is not the sandbox it was pinned to   /   assert 'b' == 'a'

2) protected_files() ersetzt durch den Spannen-Scan der Vorrunde über deren eigene vier Zeilen
FAILED test_the_measurement_watch_list_is_the_area_the_gate_protects
  AssertionError: watched but not protected: [] -- protected but not watched:
  ['…\\.claude\\agents\\codex-watcher.md', …]   /   assert set() == {…}

3) restore_from_index() ohne die Zielprüfung
FAILED test_an_index_restore_refuses_a_target_outside_the_pinned_sandbox
  Failed: DID NOT RAISE SystemExit
```

Der erste Test trägt seinen eigenen Kontrolllauf: mit **geerbtem** Zustand muss der Köder wirklich
beschädigt werden, sonst ist die zweite Hälfte grün aus Untätigkeit; und nach dem Pinnen muss die
Sandbox-eigene Datei getroffen sein. Der zweite vergleicht als **Mengen-Gleichheit** gegen einen
unabhängigen Lauf über den Baum, also in beide Richtungen — eine Liste, die einfach alles zurückgibt,
fällt ebenfalls durch. Der dritte misst beide Enden am selben Ziel-Argument.

H37 sagt jetzt, was gebaut ist, und nennt ausdrücklich, was diese Vorrichtung **nicht** deckt: sie
wirkt nur, wo ein Skript sie importiert.

---

## Abschnitt 11 — F3: **H38**, das Programm im Hier-Dokument

**Mechanismus:** `_harness._prose_removed` läuft vor **jedem** Leser beider Gates und wendet beide
Ausdrücke der Kits an. `gate_write_scope._HEREDOC_RX` löscht **jeden** Rumpf eines Hier-Dokuments —
und ein Rumpf ist nicht nur, wohin man eine Nachricht schreibt, sondern auch der Weg, auf dem eine
Shell oder ein anderer Interpreter ein **Programm** bekommt.

Gemessen 2026-08-08, ein Werkzeugaufruf, `bash` als Schiedsrichter über die Datei:

| Gestalt | Shell schreibt | Gate 1 | Gate 3 |
|---|---|---|---|
| `bash -c '<relativer Schreibzugriff>'` | ja | **rc 2** | 0 |
| das Hier-Dokument mit derselben Nutzlast | ja | **rc 0** | 0 |
| dasselbe mit quotiertem Marker | ja | **rc 0** | 0 |
| ein **Python**-Programm im Rumpf, das die Zeile ausführt | ja | **rc 0** | 0 |
| das Hier-Dokument **und** `git commit -am wip` auf derselben Zeile | ja | **rc 0** | **rc 2** |

Die letzte Zeile ist die einzige gemessene Begrenzung, und sie ist eine schwache: Gate 3 verweigert
den Commit, weil das Verb davor (`bash`) in der Read-only-Klassifikation der Kits kein lesendes ist
— nicht, weil irgendetwas den Rumpf gelesen hätte. Der **Schreibzugriff** ist offen.

Eingetragen als **H38** mit Mechanismus (nicht mit den probierten Schreibweisen), Kette, Urteil
(*blockierend, benannte Ausnahme, Abnahme des Nutzers offen*) und Begrenzung. Die Reparaturstelle
liegt in `gate_write_scope._HEREDOC_RX`, also **im Kit** und damit außerhalb des erlaubten Bereichs
von TSK-0022; das steht so im Eintrag.

**Zwei Tests, und der zweite war rot, bevor ich den Docstring anfasste:**

* `test_gate1_does_not_see_a_program_a_here_document_hands_a_shell` hält die Kante in beide
  Richtungen fest und wird rot, sobald das Loch zugeht;
* `test_every_span_the_kits_prose_removal_takes_out_is_named_where_it_is_documented` liest die
  angewandten Ausdrücke aus dem **Syntaxbaum** von `_prose_removed` und vergleicht sie in beide
  Richtungen mit dem, was `_harness.command_line` als seine Blindstelle nennt. Gegen den Docstring,
  wie er bis 2026-08-08 dastand:

```
FAILED test_every_span_the_kits_prose_removal_takes_out_is_named_where_it_is_documented
  AssertionError: `command_line` names ['_MESSAGE_ARG_RX'] as what its reading does not reach;
  the prose removal it goes through takes out ['_HEREDOC_RX', '_MESSAGE_ARG_RX']
```

Danach grün. Der Docstring nennt jetzt beide Spannen mit ihrem jeweiligen Löcherlisten-Eintrag.

---

## Abschnitt 12 — F4: der Satz in `CLAUDE.md`, der mehr behauptete als gebaut ist

`CLAUDE.md` sagte, ein Wort mit einem nicht-leeren **Tilde-Präfix** werde verweigert, und zählte
dazu `~+`, `~-`, `~1`, `~jemand/…` auf. Für `~\+/…` ist das nicht gebaut: `bash` liest `\+` als
Präfix mit einem quotierten Zeichen (und lässt das Wort literal), dieses Gate liest das **leere**
Präfix, weil der Backslash bei ihm in `_PATH_SEPARATORS` steht — gemessen außerhalb des
Heimatverzeichnisses **rc 0** (Tabelle in Abschnitt 9). Der Hook-Kommentar
(`_harness._quoting_in`) sagte das schon richtig; die Widersprüchlichkeit war der Befund.

Der Absatz verweist jetzt auf die Präfix-Definition des Gates (`_harness._tilde_prefix`) statt auf
die der Shell, nennt die Divergenz mit ihrer Messung und ersetzt die Aufzählung durch die
Eigenschaft. Dass der Verweis nicht verrottet, hält
`test_the_constitution_names_only_code_that_exists` fest (Pfad über den Syntaxbaum des Moduls).

---

## Abschnitt 13 — F5: die zweite Vorrichtung, die kanonischen Zustand schreibt

Unabhängig nachgemessen, ohne den Baum anzufassen:

```
project_memory/.audit/hook_events.jsonl   existiert:  True
git check-ignore -v <datei>               rc 1        (keine Regel deckt sie)
git status --porcelain --ignored <datei>  '?? project_memory/.audit/hook_events.jsonl'
git ls-files <datei>                      ''          (untracked)
43 Ereignisse, 2026-08-04T16:49:14 … 2026-08-07T20:32:28, Hooks: gate_needs (23), gate_shell_hygiene (20)
```

Der Schreibpfad ist `team-kits/*/hooks/_audit.py::record_event` über `_root.find_repo_root()`, und
das läuft von `cwd` aufwärts bis zum ersten `.claude`/`project_memory`/`.git`. Ein Kit-Hook-Prozess,
der irgendwo **in** diesem Repo gestartet wird, landet damit auf `<repo>/project_memory/.audit/` —
also in dem Bereich, den Gate 1 **jedem** verweigert (gemessen an der Datei selbst:
`ProtectedArea.verdict` antwortet *everyone*).

**Und die Kette ist nicht erschlossen, sondern gefahren.** `pytest tools/ -q` lief im Arbeitsbaum
mit der geschützten Menge vor und nach dem Lauf gehasht (`C:\tsk0022r2\run_tools_suite.py`, das
absichtlich **nicht** pinnt, weil sein Subjekt gerade der Lauf im Baum ist):

```
2305 passed, 12 skipped in 1347.43s (0:22:27)
protected files watched: 445
moved by this run: ['.claude\hooks\test_gates.py', 'project_memory\.audit\hook_events.jsonl']
```

Die erste bewegte Datei bin **ich** — ich habe `test_gates.py` während des Laufs weiter bearbeitet;
das ist kein Befund über die Suite. Die zweite ist es: `pytest tools/` schreibt kanonischen Zustand
des Baums, den es misst. Als zweiter Rest in **H37** eingetragen, mit
der Begrenzung: nichts Technisches, aber die Datei ist untracked sichtbar und ist kein Beweismittel,
mit dem Gate 3 urteilt. Die Reparaturstelle liegt im Kit und damit außerhalb dieses Items.

---

## Abschnitt 14 — was Runde 2 **nicht** geschlossen hat

* **H38** — Reparaturstelle im Kit, benannte Ausnahme, Abnahme des Nutzers offen.
* **H37, Rest 1** — eine Vorrichtung, die `_sandbox.py` nicht importiert, ist unbewacht wie zuvor.
  Das ist die Grenze der Konstruktion, nicht ein Versäumnis: bewachen kann sie nur, was in ihrem
  eigenen Prozess entsteht.
* **H37, Rest 2** — `_audit.record_event` schreibt weiter; Reparaturstelle im Kit. **Und diese
  Runde hat es selbst ausgelöst:** mein Lauf von `pytest tools/ -q` hat drei Zeilen an
  `project_memory/.audit/hook_events.jsonl` angehängt (43 → 46, letzter Stempel
  `2026-08-08T02:10:29`). Das ist ein Schreibzugriff in den für dieses Item **verbotenen** Bereich,
  ausgelöst durch den Befehl, den `CLAUDE.md` vorschreibt — kein Werkzeug-Schreibzugriff und nichts,
  was ich zurückgesetzt hätte (die Datei ist untracked, und ein Rücksetzen wäre selbst ein Eingriff
  in den verbotenen Bereich). Es ist genau die Kette, die H37 Rest 2 beschreibt, hier am eigenen
  Lauf gemessen.
* **Die Über-Verweigerung, die diese Runde bestätigt hat**, bleibt: `""~+/…` und `''~+/…` sind rc 2
  bei einer Shell, die literal bleibt (H33), und `~jemand/…` ebenso.
* **`--file=~+/…`** ist rc 0 und bleibt es: `bash` erweitert dort nicht, die Shell schreibt nichts.
  Was diese Zeile für die **Prosa-Entfernung** bedeutet, ist H34 und nicht diese Runde.
* **H22, H34, H35, H36** unberührt.
* **`git`-Leseformen, die Gate 1 nicht als lesend führt:** `git check-ignore -v <pfad>` wird
  verweigert, obwohl es nur liest — ich habe die Messung in Abschnitt 13 darum aus einem
  Python-Prozess gefahren. Das ist dieselbe Klasse wie H22, nur in der anderen Richtung
  (Über-Verweigerung); nicht neu eingetragen, weil H22 die Klassifikation der Kits schon trägt.

---

## Abschnitt 15 — Läufe der Runde 2

| Lauf | Baum | Ergebnis |
|---|---|---|
| `pytest .claude/hooks/test_gates.py -q` | **Arbeitsbaum** | **143 bestanden** in 1013,5 s (vorher 137; sechs neue Tests) |
| `pytest tools/ -q` | **Arbeitsbaum** | **2305 bestanden, 12 übersprungen** in 1347,4 s |
| `python -m ruff check .` | **Arbeitsbaum** | sauber |
| `python tools/validate.py` | **Arbeitsbaum** | „all structural checks passed" |
| gezielte Wiederholungen nach den letzten zwei Korrekturen (`_removed`, Umgebungs-Wiederherstellung) | **Arbeitsbaum** | 5 bestanden bzw. 2 bestanden |

`pytest tools/` ist gefahren worden, obwohl kein Kit-Pfad im erlaubten Bereich liegt: `tools/` liest
`docs/POST_V2_WISHLIST.md` (`tools/test_migrate.py`, `L…`-Einträge), und diese Runde ändert diese
Datei. Nach dem Lauf ist `team-kits/kernel/state.py` unverändert (`ca3e1735…`, 71 160 Byte).

`bump_kit_version.py` wurde auch in dieser Runde **nicht** gefahren: geändert sind nur
`.claude/hooks/**`, `CLAUDE.md` und `docs/**`; kein Kit-Pfad liegt im erlaubten Bereich, und die
Spiegelprüfung entfällt aus demselben Grund.

---

# Runde 3 (2026-08-08) — Abschlussrunde nach dem dritten Prüfverdikt

Messdisziplin dieser Runde: Basis `C:\tsk0022r3` — außerhalb des Repos (`C:\Offline Repos\…`) **und**
außerhalb des Heimatverzeichnisses (`C:\Users\zenti`), was für `HOME` diesmal nicht nur Hygiene ist,
sondern Voraussetzung der Messung. Jeder Lauf im Arbeitsbaum lief unter `run_watched.py`, das die
geschützte Menge (445 Dateien, `_sandbox.protected_files`) vor und nach dem Lauf hasht.

## Abschnitt 16 — B1: `HOME` und `CDPATH`, und der Test, der sie strukturell nicht sehen konnte

**Beide Hälften des Befundes reproduziert** (`probe_env.py`, Köder-Baum außerhalb der Sandbox, echte
`bash` aus Git for Windows, Nutzlast `sed -i "s/a/b/" <wort>/team-kits/kernel/state.py`):

| Nutzlast | Zustand geerbt | mit `sandbox_environment` davor (Fassung vor dieser Runde) |
|---|---|---|
| `~-/…` (`OLDPWD`) | Köder `'b'` | Köder `'a'` — gepinnt |
| `~/…` (`HOME`) | Köder `'b'` | Köder **`'b'`** — **nicht** gepinnt |
| `cd <köder> && sed -i …` (`CDPATH`) | Köder `'b'` | Köder **`'b'`** — **nicht** entfernt |
| `~+/…` (`PWD`) | Köder `'a'` | Köder `'a'` |
| `~1/…` (`DIRSTACK`) | Köder `'a'` | Köder `'a'` |

`PWD` und `DIRSTACK` sind damit auf diesem Host **Theater**, wie der Prüfer für `DIRSTACK` gesagt
hat, und für `PWD` zusätzlich: `bash` leitet `PWD` beim Start aus `getcwd()` neu her — mit
`PWD=<köder>` in der Umgebung druckt `printf ~+` trotzdem das Arbeitsverzeichnis (`probe_cdpath.py`).

**Nebenbefund zur Schreibweise, weil er die erste Messung falsch grün machte:** `CDPATH` ist eine
**Doppelpunkt-Liste**. `C:/tsk0022r3` wird darin als `C` und `/tsk0022r3` gelesen und findet nichts
(rc 1); `/c/tsk0022r3` und `C:\tsk0022r3` funktionieren (rc 0, Köder `'b'`). Der Test spricht das in
`_pointed_at` aus, statt es zu erraten.

**Gebaut** (`.claude/hooks/_sandbox.py`), und zwar nach dem, was mit einem Namen **getan** wird,
nicht nach seinem Namen:

* `THE_SHELLS_POSITION = ("PWD", "OLDPWD")` — wo die Shell steht und wo sie herkam: auf die Sandbox
  gezeigt;
* `THE_USERS_OWN_PLACE = ("HOME",)` — **in** der Sandbox, aber **neben** dem Baum
  (`HOME_LEAF = ".a-home-beside-the-tree"`, von `sandbox_environment` angelegt). Warum das kein
  Detail ist, steht in Abschnitt 21;
* `DROPPED = ("CDPATH", "DIRSTACK")` — ein Name, der eine **Liste** hält, hat keinen
  Ein-Verzeichnis-Wert, also fliegt er raus;
* `NOT_MEASURED_TO_CARRY_A_TREE = ("PWD", "DIRSTACK")` — die beiden oben, für die **keine** Kette
  gemessen ist. Sie werden trotzdem behandelt, aber der Kommentar behauptet für sie nichts.
* `pin()` entfernt jetzt wirklich: `os.environ.update()` legt Werte oben drauf und nimmt keinen weg,
  also wäre `CDPATH` im pinnenden Prozess stehen geblieben. Die Entfernmenge wird **abgeleitet**
  (was `sandbox_environment` weggelassen hat), nicht ein zweites Mal aufgezählt.

**Der Test misst eine Eigenschaft**, nicht drei Namen:
`test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_that_names_another_tree`
(ersetzt `test_the_measurement_sandbox_pins_every_directory_a_child_shell_reads`). Die Prüfmenge ist
`_directory_words`: **jedes** Tilde-Präfix, das das Alphabet hergibt (157, generiert aus
`_harness._tilde_prefix`), **plus** das relative Wort über eine Suchliste. Alle 158 Zeilen laufen als
**ein** Skript pro Umgebung, was sieben Umgebungen parallel bezahlbar macht (~100 s statt ~190 s
seriell). Gefragt wird: **erreicht irgendeine Zeile nach `pin()` einen Baum außerhalb der Sandbox?**
Dazu die Kontrollhälfte (mit geerbtem Zustand **muss** der Köder beschädigt werden) und die
Gegenprobe (die sandbox-eigene Datei **muss** getroffen sein).

### Und hier steckte der Defekt, den diese Runde selbst eingebaut hat

Die erste Fassung des Tests hat ihre **feindliche Umgebung aus dem Modul unter Prüfung** abgeleitet
(`hostile = POINTED_AT_THE_SANDBOX | DROPPED`). Gemessen im Klon `clone-red`:

```
=== HOME dropped from the pinned set    -> rc 0   1 passed   !!! STAYED GREEN
=== CDPATH dropped from the removed set -> rc 0   1 passed   !!! STAYED GREEN
=== OLDPWD dropped from the pinned set  -> rc 0   1 passed   !!! STAYED GREEN
```

Der Grund ist genau die Sorte Zirkel, die dieses Repo dreimal erwischt hat: wird ein Name aus dem
Modul gelöscht, hört der Test auf, ihn auf den Köder zu zeigen — **die Verteidigung und der Angriff
verschwinden zusammen**. Der Test hätte also mit ausgebautem Fix behauptet, der Fix sei da.

**Korrektur:** die feindliche Lage steht jetzt im Test (`CARRY_A_TREE = ("OLDPWD", "HOME",
"CDPATH")`) und ist eine Aussage über **Shells auf diesem Host**, nicht über das Modul; der Test
bindet sie in beide Richtungen an die laufende Shell (`carries == set(CARRY_A_TREE)`), an das Modul
(`carries <= controlled`) und an dessen Blind-Erklärung
(`controlled - carries == NOT_MEASURED_TO_CARRY_A_TREE`).

### Rot gesehen — `red2.py`, Klon unter gepinnter Sandbox, je ein Defekt einzeln, danach zurückgesetzt

Der Rotlauf selbst **pinnt sich zuerst** und hasht die geschützte Menge des **echten** Repos vor dem
Lauf, nach **jeder** Mutation und am Ende. Das ist die Lehre aus Abschnitt 20 und nicht Kosmetik:

```
[watch] 445 protected files of the REAL repo
[pin] OLDPWD='C:/tsk0022r3/redbox/run'  HOME='…/run/.a-home-beside-the-tree'  CDPATH=None
```

| Mutation | rc | woran es scheitert |
|---|---|---|
| Kontrolle, unmutiert | 0 | 1 bestanden (119 s) |
| `HOME` nirgendwohin gezeigt | 1 | „a line run after `pin()` reached …\not-mine-pinned" |
| `OLDPWD` nirgendwohin gezeigt | 1 | dieselbe Zeile |
| `PWD` nirgendwohin gezeigt | 1 | „`_sandbox` says ['DIRSTACK','PWD'] carry no tree; … the ones that carry none are ['DIRSTACK']" |
| `CDPATH` nicht entfernt | 1 | „a line run after `pin()` reached …" |
| `DIRSTACK` nicht entfernt | 1 | die Partitionszeile, `['PWD']` |
| `pin()` ohne die Entfernschleife (nur `update`) | 1 | „a line run after `pin()` reached …" |
| Modul behauptet, `CDPATH` trage nichts | 1 | die Partitionszeile |
| Suite behauptet, dieser Host lese ein Verzeichnis aus `PWD` | 1 | „the names this host was measured to resolve a directory out of are …" |
| `HOME` **auf** den Baum statt daneben (Abschnitt 21) | 1 | „the table says 'a bare cd, which goes home …' does not change the protected file, and bash disagrees" |

**Keine Mutation blieb grün, und der echte Baum bewegte sich bei keiner** („real repo moved: none",
nach jeder einzelnen). Damit ist jede gesetzte **und** jede entfernte Variable einzeln verdrahtet,
in beide Richtungen, und die Aufzählung im Modul trägt den Stolperdraht, den die Hausregel für
Aufzählungen verlangt.

Eine frühere Fassung dieser Rotmessung (`red.py`, ohne Pin, mit der zirkulären feindlichen Lage)
ist in Abschnitt 20 als Schadensursache beschrieben; ihre Ergebnisse sind durch die obigen ersetzt.

**Was die Prüfmenge nicht deckt**, steht als **H37 Rest 3** in der Löcherliste — samt der dort
gemessenen dritten Gestalt: `BASH_ENV` führt in `bash -c true` eine Datei aus und hat den Köder
außerhalb der Sandbox geschrieben, **mit** der neuen Sandbox-Umgebung davor (`ENV` allein nicht).
Das ist kein Verzeichniswort, sondern ein Programm; warum es diese Runde nicht geschlossen hat und
was stattdessen begrenzt, steht im Eintrag.

## Abschnitt 17 — B2: die Zählung, die sich am eigenen Abnahmelauf widerlegt hat

`docs/POST_V2_WISHLIST.md` nannte in H37 Rest 2 **43** Ereignisse in
`project_memory/.audit/hook_events.jsonl`. Der Abnahmelauf **derselben Runde**, die die Zahl
hingeschrieben hat, hat drei weitere angehängt (46) — die Zahl war beim Lesen schon falsch.

Ersetzt durch die **Eigenschaft**: *jeder Lauf hängt an*. Dazu ist der Satz aus Abschnitt 14 in den
Eintrag gezogen, und zwar so, dass ein Leser der Löcherliste den Unterschied erkennt: **kein
Scope-Verstoß des Pakets, sondern ein Defekt der Kits.** Der Schreibzugriff kommt aus einem
Kit-Hook-**Unterprozess** über `find_repo_root()`, nicht aus einem Werkzeugaufruf; Gate 1 sieht ihn
nie, das Item konnte ihn also nicht verbieten, und vermeidbar wäre er nur gewesen, indem man den von
`CLAUDE.md` vorgeschriebenen Abnahmelauf unterlässt. Zurückgesetzt ist er nicht — die Datei ist
untracked, und ein Rücksetzen wäre selbst ein Eingriff in den verbotenen Bereich.

## Abschnitt 18 — R1, R2, R3: eingetragen, nicht gebaut — und selbst nachgemessen

Der Auftrag sagt „eintragen, nicht bauen". Was hier steht, ist trotzdem **selbst gemessen**, weil
ein übernommener Befund ohne eigene Messung genau die Behauptung wäre, gegen die dieses Repo
arbeitet (`probe_residues.py`, `probe_short.py`, gegen eine Kopie dieses Baums außerhalb des Repos,
420 geschützte Dateien).

**R1 → H37 Rest 4.** `watch` friert die Pfadliste beim Betreten ein und vergleicht nur Digests:

```
would gate 1 refuse project_memory/evidence/active/EVD-9999.yaml?  'everyone'
CREATED a protected file        -> watch ended QUIETLY
CONTROL, changed an existing one -> watch complained: REPO DAMAGED by this measurement run: [...state.py]
```

**R2 → H37 Rest 5.** `_inside` steht auf `realpath`/`commonpath`:

| Schreibweise der Repo-Wurzel | `_inside` | `pin()` |
|---|---|---|
| wie sie dasteht / Großschreibung / über `..` | `True` | verweigert |
| echter 8.3-Kurzname `C:\OFFLIN~1\AGENTA~1` | `True` | verweigert |
| `\\?\C:\Offline Repos\AgentAndSkills` | **`False`** | **akzeptiert und pinnt** |
| `\\localhost\C$\Offline Repos\AgentAndSkills` | **`False`** | **akzeptiert und pinnt** |
| `\\?\C:\OFFLIN~1\AGENTA~1` | **`False`** | **akzeptiert und pinnt** |

Die Fix-Richtung im Eintrag ist **nicht** der `splitdrive`-Vorschlag geworden, sondern der Verweis
auf die Autorität nebenan: `_harness._anchored`/`_identity` beantwortet „dieselbe Datei" über
`(st_dev, st_ino)`, und genau diese fünf Namensräume sind dort schon gemessen (TSK-0008). Eine
eigene Kanonisierung in `_sandbox` wäre die zweite Antwort, die H15 beschreibt. Im Eintrag steht
außerdem, dass **Gate 1 von dieser Lücke nicht betroffen ist** — es liest über `_harness`.

**R3 → in H38 hineingeschrieben**, weil H38 sich auf diesen Test stützt: der Syntaxbaum-Test sieht
nur `modul._X_RX.sub(...)`; eine dritte Entfernung über einen lokalen Namen, eine in einer gerufenen
Hilfsfunktion und jeder Name ohne `_RX`-Endung bleiben unsichtbar. Fix-Richtung: die Laufzeit messen.

## Abschnitt 19 — Läufe der Runde 3

| Lauf | Baum | Ergebnis |
|---|---|---|
| gezielt: die vier Vorrichtungs-Tests, unter `run_watched.py` | **Arbeitsbaum** | 4 bestanden in 130,7 s; „445 protected files … moved: none" |
| `pytest .claude/hooks/test_gates.py -q` (voll) | **Klon, Kernel aus dem Index** | **141 bestanden, 2 gefallen** in 1299 s — die zwei sind Abschnitt 21 |
| die fünf `HOME`-empfindlichen Tests nach der Korrektur | **Klon, Kernel aus dem Index** | **5 bestanden** in 1178 s; echtes Repo unbewegt |
| Rotmessung `red2.py`, 9 Mutationen + Kontrolle | **Klon unter gepinnter Sandbox** | Kontrolle grün, **9/9 rot**, echtes Repo unbewegt |
| `python -m ruff check .claude/hooks/` | **Arbeitsbaum** | sauber |
| `python -m ruff check .` / `tools/validate.py` / `pytest tools/ -q` | **Arbeitsbaum** | **blockiert** durch den Schaden in Abschnitt 20 |

Die volle `test_gates.py` ist **nicht** im Arbeitsbaum gefahren, sondern im Klon: der Arbeitsbaum
trägt einen beschädigten Kernel (Abschnitt 20), und jeder dieser Läufe importiert oder kopiert ihn.
Der Klon bekommt `team-kits/kernel/state.py` über `_sandbox.restore_from_index` aus dem **Index** —
also über genau den Pfad, den diese Runde als „schreibt nur unter die gepinnte Sandbox" misst.

## Abschnitt 21 — der Defekt, den die Korrektur aus B1 eingebaut hat

Der volle Lauf war **nicht** grün: `HOME` auf `where` zu zeigen heißt, die Sandbox zum
Heimatverzeichnis zu machen — und die Sandbox **ist** der Stellvertreter-Baum. Damit ist
`~/team-kits/kernel/state.py` die geschützte Datei, und ein blankes `cd` verlässt den Baum nicht
mehr. Gemessen im vollen Lauf, exakt ausgezählt:

```
test_gate1_places_a_tilde_word_where_the_shell_puts_it        30 Zellen, alle mit dem Präfix `~`
test_the_shell_writes_where_the_table_of_line_shapes_says     32 Zellen, alle unter den Bewegungen
                                                              „a bare cd, which goes home" und
                                                              „cd to a tilde the shell expands"
```

Das sind **keine** echten Löcher in Gate 1: die 30 Zellen behaupten, `~/<kit-pfad>` sei ein
erlaubter Schreibzugriff auf geschützten Zustand — was nur stimmt, wenn das Repo **unter** dem
Heimatverzeichnis liegt. Dieses tut es nicht (`C:\Offline Repos\…` gegen `C:\Users\zenti`), und
`_base_outside_the_home_directory` besteht seit der Vorrunde genau darauf. Die Vorrichtung hätte
also eine Konfiguration gemessen, in der dieses Repo nicht ist, und die bewusste Position des Gates
zum leeren Präfix (H33) als Loch gemeldet.

**Korrektur:** `HOME` zeigt **in** die Sandbox, aber **neben** den Baum
(`<sandbox>/.a-home-beside-the-tree`), und `sandbox_environment` legt das Verzeichnis an — es muss
existieren, sonst scheitert ein blankes `cd` und die Shell bleibt im Baum stehen, was dieselben
Zellen andersherum kippt. Danach: die fünf betroffenen Tests **grün**. Rot ohne die Korrektur:
letzte Zeile der Rotmess-Tabelle in Abschnitt 16.

`bump_kit_version.py` ist auch in dieser Runde **nicht** gefahren worden, und die Spiegelprüfung
entfällt: absichtlich geändert sind `.claude/hooks/_sandbox.py`, `.claude/hooks/test_gates.py`,
`docs/POST_V2_WISHLIST.md` und diese Datei.

## Abschnitt 20 — der vierte Messschaden, und er ist meiner

**`team-kits/kernel/state.py` im Arbeitsbaum ist beschädigt, und die Rotmessung dieser Runde hat es
getan.** Das steht hier vor dem Ergebnis der Runde, weil es das Ergebnis der Runde blockiert.

**Wie es aufgefallen ist:** nicht durch einen Riegel, sondern durch `python -m ruff check .` beim
Abnahmelauf — die Datei liest sich als `rbise StbteError`, `clbss ProjectStbte`, `bnd`.

**Befund, gemessen (`assess_damage.py`, `assess_damage2.py`, rein lesend):**

```
worktree sha256 b220f0c97f11dc5f…  71160 bytes
index    sha256 ca3e17358fc49f6f…  71160 bytes
index, zweimal durch `sed -i "s/a/b/"`, == worktree:  True
```

Der Index trägt also **byte-genau** den Stand vor dem Schaden, und `ca3e1735…` ist genau der Hash,
den Abschnitt 15 (Runde 2) unabhängig als „unverändert" notiert hat. `git diff --name-only` nennt im
Arbeitsbaum genau vier unstaged Dateien: `docs/POST_V2_WISHLIST.md` (meine Änderung),
`.claude/agents/codex-watcher.md` und `.claude/agents/radar-watcher.md` (beide schon beim
Sitzungsstart so) und diese eine. **Kein zweiter Schaden.**

**Mechanismus, und er ist genau der von H37 — an meiner eigenen Vorrichtung:**

1. `red.py` läuft aus der Bash-Werkzeugzeile `cd /c/tsk0022r3 && python -B red.py`. Damit erbt der
   Python-Prozess `OLDPWD = 'C:/Offline Repos/AgentAndSkills'` — **das Repo**. Nachgemessen:
   `which_prefixes.py` druckt genau diesen Wert aus `os.environ`.
2. Die **erste** Fassung des neuen Tests leitete ihre feindliche Umgebung aus dem Modul unter
   Prüfung ab. Bei der Mutation „`OLDPWD` aus `POINTED_AT_THE_SANDBOX` entfernt" fiel `OLDPWD` damit
   aus der Menge, die der Test überhaupt anfasst — der Test hat es also **nicht** auf seinen Köder
   gezeigt, und `pin()` hat es (mutiert) nicht überschrieben. Das geerbte Repo stand.
3. Von den 157 Präfixen schreibt genau **eines** den `OLDPWD`-Baum (`~-`; gemessen,
   `which_prefixes2.py`: `['-']`). Dieser eine Lauf fährt zwei Umgebungen mit geerbtem `OLDPWD` —
   „inherited" und „pinned" —, also **zwei** Anwendungen. Das deckt sich exakt mit dem Befund
   „zweimal `sed`".
4. Der Sitzungsriegel `the_repo_is_not_a_sandbox` lief dabei mit — **im Klon**. Ein Riegel im Klon
   kann den Schaden am Original nicht sehen. Und `run_watched.py`, das die geschützte Menge hasht,
   habe ich um die Klon-Läufe **nicht** gelegt, weil „läuft im Klon" wie „ist sicher" aussah. Genau
   diese Annahme ist H37.

**Das ist H37 Rest 1, gemessen statt behauptet**, und mit einer Verschärfung, die im Eintrag jetzt
steht: eine Rotmessung ist nicht irgendein Skript daneben, sie **baut den Pin absichtlich aus**. Sie
ist damit die eine Gattung Lauf, die die feindliche Lage aus ihrer eigenen Umgebung bekommt.

**Was ich NICHT getan habe, und warum.** Ich habe die Datei **nicht** zurückgesetzt. Zwei
unabhängige Gründe zeigen in dieselbe Richtung: `team-kits/**` ist für TSK-0022 **verbotener
Bereich**, und die stehende Regel dieses Arbeitsbaums verbietet `git restore` /
`git checkout <ref> -- <pfad>` ausnahmslos und legt die Entscheidung dem Nutzer vor. Gate 1 würde
einen Werkzeug-Schreibzugriff dorthin übrigens **nicht** aufhalten — es schützt diesen Pfad gegen
den *Sitzungsagenten*, nicht gegen einen Subagenten (`ProtectedArea.verdict` antwortet
`('the session agent', …)`); die Grenze hier ist also die Regel und das Item, nicht der Apparat.

**Was der Nutzer entscheiden muss** — eine Zeile, nachweislich verlustfrei, weil der Index den
Vor-Schadens-Stand byte-genau trägt und der Hash unabhängig protokolliert ist:

```
git -C "C:\Offline Repos\AgentAndSkills" checkout -- team-kits/kernel/state.py
```

**Was bis dahin blockiert ist:** `python -m ruff check .` (bricht an dieser Datei ab; über
`.claude/hooks/` allein ist sie sauber), `python tools/validate.py`, `python -m pytest tools/ -q`
und die volle `test_gates.py` — jede von ihnen importiert oder kopiert den Kernel.

**Nachtrag 2026-08-08, Abschlussrunde:** die Sperre ist aufgehoben. `git diff -- team-kits/kernel/
state.py` ist leer, der Arbeitsbaum trägt wieder die Index-Fassung (`git status` zeigt die Datei nur
noch als *staged* gegenüber `HEAD`). Die Rücksetzung habe **ich nicht** gefahren; sie liegt
außerhalb dieses Pakets. `python -m ruff check .` und `python tools/validate.py` laufen seither
sauber (beides am 2026-08-08 nachgefahren).

## Abschluss (2026-08-08) — vierte Runde ist ein Edit, keine Härtung

Grundlage ist `DEC-0022`: Werkbank und Produkt tragen nicht dieselbe Beweislast; für
`.claude/hooks/` ist die Abhilfe **Streichen** statt gemessenem Ausbau (§3), und eine Lücke ohne
innerhalb einer Sitzung durchlaufende Kette ist ein Löcherlisten-Rest (§2).

**Zahlen des Prüfers, Runde 3 — übernommen, nicht von mir nachgefahren:** B1 geschlossen (9 von 9
Mutationen selbst rot gesehen, Nicht-Zirkularität in beide Richtungen), B2 geschlossen, R1/R2/R3
vollständig eingetragen, `test_gates.py` 143/143, `pytest tools/` 2305/12, `ruff` und
`tools/validate.py` sauber, geschützte Menge über 11 Rotläufe unverändert.

**Was diese Runde geändert hat — drei Dateien, ausschließlich Prosa, kein Codepfad:**

1. `.claude/hooks/test_gates.py`, Docstring von `the_repo_is_not_a_sandbox`: die Zeile ist sicher
   durch `cwd` **und** den Verzeichniszustand, den `_sandbox.sandbox_environment` setzt — vorher
   stand dort „only because of that one keyword argument". Die eigene Runde hatte das widerlegt.
2. Dieselbe Datei, Meldung desselben Riegels: die Teilaussage „is kept off this tree by `cwd`
   alone" ist ersatzlos gestrichen. Sie nannte einem Leser als erstes `cwd`, während im Rotlauf
   „`OLDPWD` nicht gesetzt" genau `OLDPWD` die Ursache war.
3. `.claude/hooks/_sandbox.py` Kopfkommentar, `test_gates.py` in `_changes_the_protected_file` und
   in `test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads`: die Zahl
   „three times in two days" bzw. „cost three files" ist gestrichen; die Zahl steht nur noch an
   **einer** Stelle (`docs/POST_V2_WISHLIST.md` H37), auf die alle drei verweisen. Sie war bereits
   gedriftet — H37 führt inzwischen einen vierten Schaden, `DEC-0022` schreibt „viermal in drei
   Tagen".
4. `docs/POST_V2_WISHLIST.md`, H37 Rest 3: die „dritte Gestalt" ist als **offene Gattung**
   umgeschrieben, mit den zwei zusätzlich gemessenen Namen (`BASHOPTS=cdable_vars`, exportierte
   Shell-Funktion) und den sieben gemessen **nicht** tragenden. Ohne Kette, also Rest nach §2.

**Eine eigene Korrektur zwischen den beiden Läufen, und sie gehört ins Protokoll, weil sie genau die
Klasse ist, um die F1 ging.** Meine erste Fassung von Punkt 1 schrieb, der Verzeichniszustand werde
„set to it as well" — auf die Sandbox. Das baut der Code nicht: `sandbox_environment` setzt
`PWD`/`OLDPWD` auf die Sandbox, `HOME` auf ein Blatt **darin** (nicht auf den Baum) und entfernt
`CDPATH`/`DIRSTACK` ganz. Die Formulierung heißt jetzt „kept inside that sandbox", also das, was die
Funktion in ihrem eigenen Docstring zusagt.

**Abnahmelauf:** `python -B -m pytest .claude/hooks/test_gates.py -q` → **143 passed in 1765.08 s
(0:29:25)**, rc 0, ein Lauf, nach **allen** Änderungen einschließlich dieser Korrektur. (Der Lauf
davor, vor der Korrektur, war 143 passed in 1725.24 s.) `python -m ruff check .` und
`python tools/validate.py` grün. **Kein `bump_kit_version.py`** — kein Kit-File angefasst, und
`validate.py` bestätigt, dass keine Version fehlt. **Kein `pytest tools/`** (Auftragsvorgabe: der
Lauf schreibt nach `project_memory/.audit/`, H37 Rest 2, und der Prüfer hat ihn am selben Tag grün
gemessen).

**Geschützte Menge um die Läufe, gehasht mit `_sandbox.protected_files`:** um den Abnahmelauf
**448 vorher, 448 nachher, nichts bewegt**. Um den Lauf davor 446 → 448, und bewegt hatten sich
`project_memory/generated/index.yaml` sowie die **neuen** `decisions/active/DEC-0023.yaml` und
`tasks/active/TSK-0024.yaml` (erstellt 14:29 bzw. 14:33 laut ihrem eigenen `created`-Feld). Das
waren Kernel-Erfassungen des Sitzungsagenten **während** meines Laufs, kein Schreibzugriff dieses
Pakets — dieses Paket fasst `project_memory/` nirgends an. `team-kits/kernel/state.py` blieb in
beiden Läufen unbewegt. Genau diesen Fall nennt die Riegelmeldung als zweite Möglichkeit;
angeschlagen hat er nicht, weil seine Wachliste aus einem Sandbox-Gang entsteht, in dem diese drei
Dateien nicht vorkommen (H37 Rest 4).

**Was hier ausdrücklich NICHT behauptet wird:** kein Test wird ohne diese vier Änderungen rot. Sie
sind Docstring- und Meldungstext; die einzige Docstring-Kopplung dieser Suite liest
`command_line.__doc__` (H22-Stolperdraht) und keine der geänderten Stellen. Ein Test, der einen Satz
in einer Datei sucht, wäre eine Zeichenkettensuche über eine Datei und damit genau das, was die
Hausregel verbietet. Der Beleg dieser Runde ist deshalb der grüne Abnahmelauf plus die Feststellung,
dass die geänderten Sätze jetzt sagen, was die Messungen der Runde ergeben haben.

