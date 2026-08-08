# Messprotokoll der vier Repo-Gates (TSK-0015, 2026-08-05)

Fortsetzung von `docs/reviews/2026-08-05-tsk0013-measurements.md`. Dieses Dokument trägt die Ketten
zu **H1**, **H26**, **H28** und **H29**, die Vorher/Nachher-Werte der Runde TSK-0015 (Befunde F1–F11
des Prüfberichts zu TSK-0013) und den Stand der Reste **H10**, **H16**, **H18**, **H20**, **H21**,
**H24**.

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht messbar war, steht das ausdrücklich da,
samt dem Grund.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile ist ein `subprocess`-Start des registrierten Skripts mit
  JSON auf `stdin`, gegen ein Projekt **außerhalb** dieses Repos. `2` = Verweigerung, `0` =
  Durchlass; alles andere liest der Provider als „hook error, carry on", also ebenfalls als
  Durchlass.
- **Die Shell als Schiedsrichter, und zwar über die DATEI.** Für „wo steht die Shell wirklich" ist
  der Rückgabecode kein Beleg. Jede Zeile lief zusätzlich in einer echten `bash` in einem
  Sandbox-Baum, in dem `team-kits/kernel/state.py` den Inhalt `a` hatte; „schreibt" heißt: die
  Datei hat sich danach geändert. Die Tabellen dieses Dokuments liefen über
  `C:\Program Files\Git\bin\bash.exe`; die Suite sucht sich ihre Shell selbst
  (`_can_arbitrate`) und nahm auf diesem Host `C:\Program Files\Git\usr\bin\bash.exe` — beide
  antworten in allen 213 Formen gleich. (Korrigiert 2026-08-07: hier und in der Überschrift von
  Abschnitt 3 stand **207**, während Tabelle und Text der Runde 213 nennen; 19 × 10 + 23 = 213.)
- **Vorher/Nachher aus zwei Hook-Verzeichnissen.** „vorher" ist der Stand nach TSK-0013, „nachher"
  der dieser Runde; beide liegen als Prozess vor, dasselbe Projekt, dieselbe Zeile.
- **Ablation statt Behauptung.** Jeder neue Zweig wurde einzeln in einer Kopie außerhalb des Repos
  zurückgedreht und die zugehörigen Tests gefahren (Abschnitt 7).

## 1. F1 — eine Operandenliste, die die Shell zurückweist, bewegte die Basis (H29)

Jede Zeile endet auf `sed -i "s/a/b/" team-kits/kernel/state.py`, **relativ** geschrieben. Spalte
„bash" ist die Datei im Sandbox-Baum, nicht der Rückgabecode; Spalte „stderr" ist, was `bash` zu
dem Verzeichnisverb selbst sagt.

| Zeile davor | bash | stderr der Shell | vorher | nachher |
|---|---|---|---|---|
| `cd "<außerhalb>" x ;` | **schreibt** | `cd: too many arguments` | **rc 0** | **rc 2** |
| `cd -q "<außerhalb>" ;` | **schreibt** | `cd: -q: invalid option` | **rc 0** | **rc 2** |
| `pushd "<außerhalb>" x ;` | **schreibt** | `pushd: too many arguments` | **rc 0** | **rc 2** |
| `pushd -n "<außerhalb>" ;` | **schreibt** | — (`-n` schiebt, ohne zu wechseln) | **rc 0** | **rc 2** |
| `cd "<außerhalb>" > /dev/null x ;` | **schreibt** | `cd: too many arguments` | **rc 0** | **rc 2** |

Das ist ein Durchlass in **einem** Werkzeugaufruf, ohne Vorbereitung, und er reicht so weit wie
Gate 1 reicht. Dieselbe Zeile mit einer Umleitung statt des `sed`, gemessen über die jeweilige
Datei im Sandbox-Baum:

| `cd "<außerhalb>" x ; echo z > <ziel>` | bash | vorher | nachher |
|---|---|---|---|
| `.claude/settings.json` (Registrierung der vier Gates) | **schreibt** | **rc 0** | **rc 2** |
| `.claude/hooks/_harness.py` (der gemeinsame Rumpf selbst) | **schreibt** | **rc 0** | **rc 2** |
| `project_memory/README.md` (kanonischer Zustand) | **schreibt** | **rc 0** | **rc 2** |

**Warum die Antwort eine dritte sein musste.** Der Leser kannte zwei Antworten auf „welches Wort
ist das Ziel": ein Wort — oder keines, und *keines* heißt für den Aufrufer *bare `cd` →
Heimatverzeichnis*. Ein Leser, der bei einer zurückgewiesenen Operandenliste ins Heimatverzeichnis
wandert, ließ die Prüfmenge von TSK-0013 **grün** — das ist die Messung, aus der DEC-0014 kommt.
`_UNACCOUNTABLE` ist die dritte Antwort; sie lässt die Basis stehen. Gegen die gekreuzte Tabelle
dieser Runde ist derselbe Leser **rot** (Abschnitt 7, erste Zeile).

**Die Gegenrichtung, im selben Lauf** — hier muss die Basis sich bewegen, sonst ist der Fix eine
Stilllegung:

| Zeile davor | bash | vorher | nachher |
|---|---|---|---|
| `cd "<außerhalb>" ;` | schreibt nicht | rc 0 | rc 0 |
| `cd "<außerhalb>" > /dev/null ;` | schreibt nicht | rc 0 | rc 0 |
| `cd ;` (Heimatverzeichnis) | schreibt nicht | rc 0 | rc 0 |
| `cd > /dev/null ;` (bare `cd`, Ausgabe umgeleitet) | schreibt nicht | **rc 2** | **rc 0** |
| `pushd "<außerhalb>" ;` | schreibt nicht | rc 0 | rc 0 |
| `pushd "<außerhalb>" ; popd ;` | schreibt | rc 2 | rc 2 |
| `pushd "<außerhalb>" ; popd +0 ;` | schreibt | rc 2 | rc 2 |

Die vierte Zeile ist die Falle, vor der der Prüfbericht gewarnt hat: die Verbuchung muss die
**Umleitungs-Token** auslassen, sonst zählt `> /dev/null` als Operand und ein bare `cd` mit
Umleitung bleibt stehen. Die letzten beiden Zeilen sind der Grund, warum die Verbuchung auf `popd`
**nicht** angewandt wird: ein Pop geht in Richtung des geschützten Baums zurück, dort ist
Stehenbleiben nicht die verweigernde Richtung.

## 2. F2 — das Recht, das ein Prozess für das Hineingehen fragt (H28)

Gemessen an je einem Verzeichnis, dem **einzeln** ein Recht entzogen wurde (`icacls /deny`):

| Frage | Recht voll | nur Auflisten entzogen `(RD)` | nur Durchsuchen entzogen `(X)` |
|---|---|---|---|
| `os.path.isdir` | ja | ja | ja |
| `os.stat` | ja | ja | ja |
| `os.stat` von `.` darin | ja | ja | **ja** |
| `os.access(X_OK)` | ja | ja | **ja** |
| `os.scandir` (öffnen) | ja | **PermissionError** | ja |
| `os.chdir` | ja | ja | **PermissionError** |
| `bash -c 'cd <verzeichnis>'` | ja | ja | **nein** |

Nur `os.chdir` antwortet in **beiden** Richtungen wie die Shell. Am Gate, mit derselben Zeile:

| Fall | bash | vorher (öffnen) | nachher (betreten) |
|---|---|---|---|
| Durchsuchen entzogen, `cd <verzeichnis>` davor | **schreibt** | **rc 0** | **rc 2** |
| Auflisten entzogen, `cd <verzeichnis>` davor | schreibt nicht | **rc 2** | **rc 0** |

Die erste Zeile ist ein Loch (die Shell bleibt im Baum, das Gate folgt ihr hinaus), die zweite
Reibung. Der Docstring der vorigen Runde nannte das Öffnen *„die einzige der gemessenen Fragen, die
antwortet wie die Shell"* — die Zeile, die das widerlegt, stand in derselben Tabelle
(`docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 3: `os.chdir` → `PermissionError`).

**Preis des Wechsels, benannt statt versteckt, und hergeleitet statt gemessen:** `os.chdir` bewegt
den Prozess wirklich. Er wird im selben Aufruf zurückgesetzt, und die Frage läuft im **einen**
Arbeitsthread (`_Probes`), auf dessen Antwort der Aufrufer wartet — es gibt also keinen Moment, in
dem eine zweite Frage aus dem fremden Verzeichnis heraus gestellt wird. Die eine Ausnahme steht in
derselben Konstruktion: läuft die Frist ab, wartet der Aufrufer nicht mehr, verweigert und verlässt
den Prozess — der Arbeitsthread kann dann im fremden Verzeichnis stehenbleiben, was nichts mehr
kostet, weil nichts mehr entschieden wird. Kommt der Rückweg nicht zustande, ist das kein `False`,
sondern ein Fehler, und `guarded()` macht daraus eine Verweigerung.

## 3. Das Kreuz — 213 Formen, gegen die Shell und gegen beide Leser

Die Tabelle in `.claude/hooks/test_gates.py` ist nicht mehr gesammelt, sondern **gekreuzt**: 19
Stellungen des Verbs (Shell selbst / Kind, in jeder Schreibweise, die TSK-0013 gemessen hat) × 10
Verbformen (Ziel da, zweiter Operand, zurückgewiesene Option, Ziel nicht da, bare `cd`, `pushd`,
`popd` …) plus 23 Formen ohne Verzeichnisverb oder mit zweien — **213 Zeilen**. Erwartet wird
**abgeleitet**: der relative Schreibzugriff landet im geschützten Baum, außer die Shell führt das
Verb selbst aus **und** der Wechsel kommt zustande. Jede Zelle läuft durch eine echte `bash` (die
Spalte) und durch einen echten Gate-Prozess (die Antwort).

| Lauf | Formen | Shell ≠ abgeleitete Spalte | Loch (rc 0, Shell schreibt) | Über-Verweigerung |
|---|---|---|---|---|
| vorher (Stand TSK-0013) | 213 | 0 | **26** | **1** |
| nachher | 213 | 0 | **0** | **0** |

24 der Löcher sind drei Verbformen (`cd <ziel> x`, `cd -q <ziel>`, `pushd <ziel> x`) × den acht
Stellungen, in denen die Shell das Verb selbst ausführt — ein Kreuz, das keine der drei Formen
einzeln gezeigt hätte. Die beiden übrigen sind die Pipe-Läufe aus Abschnitt 4.2. Die
Über-Verweigerung ist `cd > /dev/null` aus Abschnitt 1.

**Der Lauf gegen die Shell hat außerdem einen Defekt im Test selbst gefunden:** die erste Fassung
verteilte die Sandbox-Bäume über `index % 6` statt über einen gehaltenen Platz, und der siebte
Prüfling maß im Baum des ersten mit — sechs Zellen kamen mit fremden Antworten zurück. Genau dafür
ist der Schiedsrichter da.

## 4. F5 — der Stolperdraht auf der Trennerliste, beide Enden (H26)

Der Trenner der Kits wird in einem Klon **erweitert** (angehängte Zeile, kein Eingriff in den
Quelltext von `team-kits/**`), dann laufen vier Zeilen durch das echte Gate:

| ergänzter Trenner | `echo hi` | Kernel-Aufruf des Repos | Schreibzugriff in `team-kits/` | freier Schreibzugriff |
|---|---|---|---|---|
| keiner | rc 0 | rc 0 | rc 2 | rc 0 |
| `&` (dieser Leser platziert ihn) | rc 0 | rc 0 | rc 2 | rc 0 |
| `;;` (dito) | rc 0 | rc 0 | rc 2 | rc 0 |
| `\|` (dieser Leser schneidet daran **Stufen**) | **rc 2** | **rc 2** | rc 2 | **rc 2** |
| `>` (nicht platzierbar) | rc 2 | rc 2 | rc 2 | rc 2 |
| `NEWLINE-ISH` (nicht platzierbar) | rc 2 | rc 2 | rc 2 | rc 2 |

Die `|`-Zeile ist der Befund: das Prädikat fragte `_cuts`, und `_cuts` platziert `|` nicht — die
Wörter dahinter bekommen aber sehr wohl ein eigenes Verb, weil `stages()` dort schneidet. Der
Stolperdraht legte damit **jede** Zeile lahm, den eigenen Kernel-Aufruf eingeschlossen. Das
Prädikat fragt jetzt nach der Folge (`_placed_by_this_reader`), nicht nach dem Schnitt; `>` und
`NEWLINE-ISH` verweigern weiter, denn dort bliebe das Zeilenende beim Verb davor.

### 4.2 Zwei Läufe mit einem `|`, die dieser Leser nicht als Stufenschnitt las (H26)

Die Frage aus 4.1 zurück auf den eigenen Leser angewandt: `stages()` verglich das Token mit `|`
**selbst**, und `_cuts` las jeden Lauf mit einem `&` als asynchronen Trenner. Beides trifft
Schreibweisen, die `shlex` als **einen** Lauf zurückgibt. Gemessen 2026-08-05, `bash` über die
Datei:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `(echo hi)\|sed -i … team-kits/kernel/state.py` | **schreibt** | **rc 0** | **rc 2** |
| `echo hi \|& cd "<außerhalb>" ; <relativ schreiben>` | **schreibt** | **rc 0** | **rc 2** |
| `(echo hi) \| <schreiben>` (mit Leerzeichen) | schreibt | rc 2 | rc 2 |
| `echo hi \|& <schreiben>` | schreibt | rc 2 | rc 2 |
| `echo hi\|&<schreiben>` (geklebt) | schreibt | rc 2 | rc 2 |
| `cd "<außerhalb>" \|& true ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `(echo hi)\|cd "<außerhalb>" ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `echo x \| PYTHONPATH=team-kits python -B -m kernel.cli …` (Gegenrichtung) | — | rc 0 | rc 0 |

**Dieselbe Frage an Gate 3 (H1), und sie hat eine eigene Lücke aufgedeckt.** Mit gültigem Urteil im
Baum, gemessen an denselben Hook-Verzeichnissen:

| Zeile | vorher | Zwischenstand (nur `_cuts`-Fix) | nachher |
|---|---|---|---|
| `sed -i … docs/note.md \| git commit -m wip` | **rc 0** | **rc 0** | **rc 2** |
| `(echo more >> docs/note.md)\|git commit -m wip` | **rc 0** | **rc 0** | **rc 2** |
| `echo more >> docs/note.md \|& git commit -m wip` | rc 2 | **rc 0** | rc 2 |
| `sed -i … docs/note.md \|& git commit -m wip` | rc 2 | **rc 0** | rc 2 |
| `git commit -m wip \|& sed -i … docs/note.md` | rc 2 | **rc 0** | rc 2 |
| `git commit -m wip` (Gegenrichtung) | rc 0 | rc 0 | rc 0 |
| `git add -A && git commit -m wip` (Gegenrichtung) | rc 0 | rc 0 | rc 0 |
| `git commit -m wip ; sed -i … docs/note.md` (Gegenrichtung) | rc 0 | rc 0 | rc 0 |
| `echo wip \| git commit -F -` (Gegenrichtung) | rc 0 | rc 0 | rc 0 |

Die mittlere Spalte ist eine **Regression dieser Runde**, gefunden bevor sie eingebaut blieb: sobald
`|&` kein Listentrenner mehr ist, steht der Schreibbefehl in **derselben** Pipeline wie der Commit,
und Gate 3 sah nur die Pipelines *davor*. Die ersten beiden Zeilen zeigen, dass dieselbe Lücke schon
vorher offen war — eine Pipe ist keine Ordnung, die Stufen laufen nebeneinander. Gate 3 prüft jetzt
auch die committende Pipeline, jede Stufe außer der, die den Commit trägt. **Was das kostet:** eine
Stufe, die die Kits nicht als lesend führen, verweigert jetzt auch neben einem Commit — gemessen
`git commit -m wip 2>&1 | tee /dev/null` → rc 2, obwohl dorthin nichts geschrieben wird. Das ist die
Klassifikationsgrenze aus H22, in einer neuen Stellung.

Die erste Zeile der Tabelle darüber ist dieselbe Klasse wie H26 in einer Schreibweise, die TSK-0013 nicht getroffen
hat: `)|` ist weder ein Trenner der Kits noch der Vergleich, mit dem `stages()` schnitt, also blieb
das `sed` beim `echo` davor — und ein lesendes Verb sammelt keine Kandidaten. Die zweite ist die
Grenze, die der Docstring von `_cuts` **für sich behauptet hatte**: „`|&` … Both halves of that
error refuse rather than pass". Die zweite Hälfte stimmte nicht — steht hinter `|&` ein
Verzeichnisverb, bewegte es die Basis, obwohl die Shell es in einem Kind ausführt. Gefunden wurde
das nicht durch eine neue Idee, sondern durch DEC-0014: eine Bedingung, die ein Docstring für sich
behauptet, ist eine Achse der Prüfmenge — beim Kreuzen fiel sie um. Beide Schreibweisen stehen
jetzt in der Tabelle.

## 5. F4 — ein Test, der sich selbst übersprang

Fünf Wiederholungen von `test_gate1_answers_before_its_registration_gives_up`, unabhängig gefahren
(Stand vorher): **einmal übersprungen** mit dem Grund *„this host needs 1.12s for a call this gate
allows, so a 1s registration cannot be answered inside by any implementation"*, viermal grün. Der
volle Lauf davor: 125 grün in 4 min 24 s, kein Übersprungener. Der Prüfbericht meldet für dieselben
fünf Wiederholungen **drei** Übersprungene und einen roten Lauf; beide Beobachtungen zeigen auf
dieselben zwei Ursachen, und welche von beiden zuschlägt, hängt an der Last der Maschine und am
Alter des Negativ-Caches. Reproduziert habe ich eine von beiden direkt (die Vorbedingung) und die
zweite an ihrem Mechanismus (die Cache-Tabelle unten).

Zwei Ursachen, beide im Test:

1. **Die Vorbedingung maß die falsche Zahl.** Verglichen wurde die kurze Registrierung mit den
   Kosten eines Aufrufs, den das Gate **erlaubt** (voller Preis eines Urteils, gemessen 0,67–1,26 s),
   während der Prüfling einer ist, den es **verweigert**. Gemessen, was ein Prozess dieses Gates
   mindestens kostet — ein Lauf, der keine einzige Dateisystemfrage stellt (Registrierung ohne
   `timeout`, also Verweigerung vor der ersten Frage): **0,48–0,87 s** über neun Läufe. Die
   Registrierungen werden jetzt daraus abgeleitet, samt der Bedingung, unter der die Untergrenze
   überhaupt etwas zeigt (`bare > seconds * (1 - share)`), und jede Kostenprobe ist der
   **schlechteste** von drei Läufen, weil ein zufällig schneller Lauf eine Frist erzeugt, die der
   nächste nicht hält. Drei Ableitungen hintereinander auf diesem Host: `(4, 2)`, `(3, 2)`,
   `(4, 2)` — lange und kurze Registrierung in Sekunden.
2. **Die Übersprungbedingung hing am Negativ-Cache.** Gemessen an einer UNC-Adresse aus dem
   RFC-5737-Bereich:

| Frage | Kosten |
|---|---|
| `192.0.2.11`, kalt | 42,18 s |
| `192.0.2.11`, sofort danach | **0,00 s** |
| `192.0.2.12` (Nachbar, frisch) | 42,16 s |
| `198.51.100.13` (anderer Bereich, frisch) | 42,15 s |
| `192.0.2.11`, ~85 s später | 42,15 s |

Die Adresse war aus `os.getpid() % 120` abgeleitet; eine Suite, die hundert Prozesse startet,
bringt den nächsten Lauf in Reichweite derselben Zahl. Jetzt wird pro Frage eine aus 750 gezogen,
und ein Prüfling, der schnell zurückkam, wird mit einer neuen Adresse wiederholt.

**Und keiner dieser Tests überspringt sich noch.** Ein Test, der seine Eigenschaft nicht messen
kann, meldet das als Fehlschlag.

## 6. Die Reste, am neuen Stand gemessen

| Kette | bash | vorher | nachher | Eintrag |
|---|---|---|---|---|
| `while true ; do cd "<außerhalb>" ; break ; done ; <schreiben>` | schreibt nicht | 2 | 2 | H24, Über-Verweigerung |
| `if cd "<außerhalb>" ; then true ; fi ; <schreiben>` | schreibt nicht | 2 | 2 | H24, Über-Verweigerung |
| `arr=(a b) cd "<außerhalb>" ; <schreiben>` | schreibt nicht | 2 | 2 | H24, Über-Verweigerung |
| `x=1 cd "<außerhalb>" ; <schreiben>` (skalare Zuweisung) | schreibt nicht | **0** | **0** | **kein Rest** — das Gate folgt |
| `cd -L "<außerhalb>" ; <schreiben>` | schreibt nicht | 0 | **2** | H29, Über-Verweigerung |
| `cd -P "<außerhalb>" ; <schreiben>` | schreibt nicht | 0 | **2** | H29 |
| `cd -- "<außerhalb>" ; <schreiben>` | schreibt nicht | 0 | **2** | H29 |
| `cd "<außerhalb>" 2>&1 ; <schreiben>` | schreibt nicht | 0 | **2** | H29 |
| `R="<außerhalb>" ; cd "$R" ; <schreiben>` | schreibt nicht | 2 | 2 | H20, Über-Verweigerung |
| `R="<außerhalb>" ; sed -i … "$R/team-kits/kernel/state.py"` | schreibt | **0** | **0** | H16 (offen) |

Die vierte Zeile korrigiert H24: von den beiden Zuweisungsformen ist nur die **Array**-Form
betroffen. Bei einer skalaren Zuweisung meldet der Leser der Kits `cd` als Verb, die Basis bewegt
sich, und das Gate antwortet wie die Shell.

## 7. Mutationen — jeder gebaute Zweig einzeln

Defekt in einer Kopie außerhalb des Repos wiederhergestellt, die zugehörigen Tests gefahren. Das
ist die Stichprobe, die **H10** meint, und ausdrücklich kein erschöpfender Mutationslauf:

| Mutation | Test | Ergebnis |
|---|---|---|
| eine zurückgewiesene Operandenliste ist „kein Operand" (Heimatverzeichnis) | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| eine zurückgewiesene Operandenliste ist der erste Operand (Stand TSK-0013) | dito | **rot** |
| die Verbuchung zählt die Umleitungs-Token mit | dito | **rot** |
| nur ein bares `popd` schiebt zurück (die Verbuchung auch auf `popd` angewandt) | dito | **rot** |
| ein betretbares Verzeichnis ist ein auflistbares (Stand TSK-0013) | `…follows_a_move_a_process_can_make_and_no_other` | **rot** |
| dieselbe Mutation | `…refuses_a_line_exactly_where_the_shell_would_write` | **grün** — die Tabelle kreuzt kein entzogenes Recht; genau dafür gibt es den eigenen Test |
| ein Stufenschnitt ist das Token `\|` und sonst nichts | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| ein Lauf mit `\|` und `&` ist der asynchrone Trenner | dito | **rot** |
| die committende Pipeline wird nicht geprüft | `…gate3_refuses_a_line_that_moves_the_tree_before_it_commits` | **rot** |
| der Stolperdraht fragt `_cuts` statt der Folge | `…separator_this_reader_cannot_place_refuses_the_line` | **rot** |
| die Reserve ist ein Anteil und sonst nichts | `…answers_before_its_registration_gives_up` | **rot** |
| ein Urteil der Löcherliste widerspricht seinem Eintrag (Rest → GESCHLOSSEN) | `…hole_list_judges_every_entry_it_carries` | **rot** |
| dasselbe in der Gegenrichtung (GESCHLOSSEN → Rest) | dito | **rot** |
| ein Verweis nennt ein Protokoll ohne Abschnitt | `…every_reference_to_a_measurement_leads_to_one` | **rot** |

Jede Mutation lief in einem eigenen Klon **außerhalb** des Repos (`shadow` + `mutants/mNN`), mit
dem echten Testlauf darin; die Zeile „grün" steht mit in der Tabelle, weil sie die Arbeitsteilung
zwischen der gekreuzten Tabelle und dem Rechte-Test belegt.

## 8. Suite

`python -B -m pytest .claude/hooks/test_gates.py -q`:

| Lauf | Ergebnis | Dauer |
|---|---|---|
| vor dieser Runde | 125 grün, 0 übersprungen | 4:24 |
| Zwischenstand (vor dem Pipe-Fix) | 125 grün, 0 übersprungen | 7:27 / 7:03 |
| Zwischenstand, zweiter Lauf | 125 grün, 0 übersprungen | 6:42 |
| Zwischenstand (nach dem Pipe-Fix) | 125 grün, 0 übersprungen | 7:21 / 7:41 |
| Endstand (mit dem Gate-3-Fix), Lauf 1 | 125 grün, 0 übersprungen | 7:22 |
| Endstand, Lauf 2 | 125 grün, 0 übersprungen | 7:30 |

Die Zahl ist wiederholbar, und sie enthält keine Übersprungenen mehr. Die zusätzlichen ~3 Minuten
sind die gekreuzte Tabelle: 213 Formen × zwei Läufe (echte `bash`, echter Gate-Prozess), zehn davon
gleichzeitig. Die beiden Tests kosten 81 s und 62 s, gemessen mit `--durations`.

**Korrigiert 2026-08-07:** vier dieser Zeilen sagten „zufällige Reihenfolge" bzw. „feste
Reihenfolge". Eine zufällige Testreihenfolge ist auf diesem Rechner nicht herstellbar — es ist weder
`pytest-randomly` noch `pytest-random-order` installiert (`python -m pytest --help` kennt keine
solche Option, und es gibt keine `pytest.ini`/`pyproject.toml`, die eine setzt). Die Läufe haben
stattgefunden, ihre Reihenfolge war die der Datei; die Angabe ist gestrichen statt umgedeutet.
