# Messprotokoll der vier Repo-Gates (TSK-0013, 2026-08-05)

Fortsetzung von `docs/reviews/2026-08-05-tsk0011-measurements.md`. Dieses Dokument trägt die Ketten
zu **H18**, **H20**, **H21**, **H24** und **H25**, die Ketten der in dieser Runde geschlossenen
Einträge **H26**, **H27** und **H28** sowie die Vorher/Nachher-Werte der Runde TSK-0013 (Befunde
F1–F9 des Prüfberichts zu TSK-0011).

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht messbar war, steht das ausdrücklich da,
samt dem Grund.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile unten ist ein `subprocess`-Start des registrierten Skripts
  mit JSON auf `stdin`, gegen ein Projekt **außerhalb** dieses Repos (`team-kits/`,
  `tools/bump_kit_version.py`, `project_memory/`, `.claude/`, `CLAUDE.md`, echtes git-Repo mit
  echtem Diff). `2` = Verweigerung, `0` = Durchlass; alles andere liest der Provider als „hook
  error, carry on", also ebenfalls als Durchlass.
- **Die Shell als Schiedsrichter, und zwar über die DATEI.** Für „wo steht die Shell wirklich" ist
  der Rückgabecode kein Beleg. Jede Zeile lief zusätzlich in einer echten `bash` in einem
  Sandbox-Baum, in dem `team-kits/kernel/state.py` den Inhalt `a` hatte; „schreibt" heißt: danach
  steht dort `b`.
- **Vorher/Nachher aus zwei Hook-Verzeichnissen.** „vorher" ist der Stand nach TSK-0011, „nachher"
  der dieser Runde; beide liegen als Prozess vor, dasselbe Projekt, dieselbe Zeile.
- **Ablation statt Behauptung.** Jeder neue Zweig wurde einzeln in einer Kopie außerhalb des Repos
  zurückgedreht und die zugehörigen Tests gefahren (Abschnitt 8).

## 1. F1 — die Kindschaft ist breiter als die Klammer (H27)

Jede Zeile endet auf `sed -i "s/a/b/" team-kits/kernel/state.py`, **relativ** geschrieben. Spalte
„bash" ist die Datei im Sandbox-Baum, nicht der Rückgabecode.

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `( true ; cd "<außerhalb>" ) ; <schreiben>` | schreibt | rc 0 | **rc 2** |
| `( true && cd "<außerhalb>" ) ; <schreiben>` | schreibt | rc 0 | **rc 2** |
| `( false \|\| cd "<außerhalb>" ) ; <schreiben>` | schreibt | rc 0 | **rc 2** |
| `(cd "<außerhalb>");<schreiben>` | schreibt | rc 0 | **rc 2** |
| `cd "<außerhalb>" & <schreiben>` | schreibt | rc 0 | **rc 2** |
| `cd "<außerhalb>" & true ; <schreiben>` | schreibt | rc 0 | **rc 2** |
| `cd "<außerhalb>" && true & <schreiben>` | schreibt | rc 0 | **rc 2** |
| `cd "<außerhalb>" \| true ; <schreiben>` | schreibt | rc 0 | **rc 2** |
| `( cd "<außerhalb>" ) ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `( ( cd "<außerhalb>" ) ) ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `( pushd "<außerhalb>" ) ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `true \| cd "<außerhalb>" ; <schreiben>` | schreibt | rc 2 | rc 2 |

Die Gegenrichtung, im selben Lauf — die Shell geht wirklich, der Schreibzugriff landet außerhalb:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `cd "<außerhalb>";<schreiben>` (geklebt) | schreibt nicht | rc 0 | rc 0 |
| `{ cd "<außerhalb>" ; } ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `cd "<außerhalb>" > /dev/null ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `( true ) ; cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `( true & ) ; cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `cd "<außerhalb>" && cd . ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `true&&cd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `pushd "<außerhalb>" ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `cd "<außerhalb>" ; cd . ; <schreiben>` | schreibt nicht | rc 0 | rc 0 |
| `true & cd "<außerhalb>" ; <schreiben>` | schreibt nicht | **rc 2** | **rc 0** |

Die letzte Zeile ist die Gegenrichtung des Fixes und lief vorher falschherum: das `&` gehörte zum
`true`, der Wechsel dahinter ist die Shell selbst — vorher sah der Leser dort gar kein Verb und
blieb stehen, also verweigerte er einen Schreibzugriff, der außerhalb landet.

**Zwei Ursachen, dieselbe Klasse.** Die Kindschaft wurde pro Pipeline gezählt und nur in einer
Schreibweise erkannt: hinter einem Listentrenner fing der Zähler wieder bei null an, obwohl die
Klammer offen war, und die asynchrone Liste wie das Pipelineglied kamen im Zähler gar nicht vor.
Die drei Zeilen, die schon vorher rc 2 waren, stehen mit in der Tabelle: sie sind der Teil der
Klasse, den die vorige Runde getroffen hat, und sie messen mit, dass der Umbau ihn nicht verloren
hat.

## 2. F1, zweite Hälfte — ein Trenner, den der Leser nicht kannte (H26)

Dieselbe Klasse ohne jeden Verzeichniswechsel: steht vor dem Schreibbefehl ein **lesendes** Verb und
dazwischen ein Trenner, den der Leser nicht als Trenner liest, gehört das ganze Zeilenende zum Verb
davor — und ein lesendes Verb sammelt keine Kandidaten.

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `echo hi & <schreiben>` | schreibt | **rc 0** | **rc 2** |
| `cat docs/note.md & <schreiben>` | schreibt | **rc 0** | **rc 2** |
| `(echo hi);<schreiben>` | schreibt | **rc 0** | **rc 2** |
| `(echo hi)&&<schreiben>` | schreibt | **rc 0** | **rc 2** |
| `cd . & <schreiben>` | schreibt | **rc 0** | **rc 2** |
| `sed -i "s/x/y/" docs/note.md & <schreiben>` | schreibt | rc 2 | rc 2 |
| `( echo hi ) ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `echo hi ; <schreiben>` | schreibt | rc 2 | rc 2 |
| `echo hi&&<schreiben>` | schreibt | rc 2 | rc 2 |

Das ist ein Durchlass in **einem** Werkzeugaufruf, ohne Vorbereitung: `echo hi & sed -i <kitdatei>`.

**Derselbe Lauf mit einer Umleitung statt eines Schreibbefehls**, und er hat die erste Fassung
dieser Runde noch einmal korrigiert. Ein `;` unmittelbar vor einem `>` steht in einem Lauf, den
weder die Trennerliste noch die Umleitungsform der Kits erkennt:

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `echo hi;>team-kits/kernel/state.py` | **kürzt die Datei** | **rc 0** | **rc 2** |
| `(echo hi);>team-kits/kernel/state.py` | **kürzt die Datei** | **rc 0** | **rc 2** |
| `echo hi ;> team-kits/kernel/state.py` | **kürzt die Datei** | **rc 0** | **rc 2** |
| `echo hi ; > team-kits/kernel/state.py` (mit Leerzeichen) | kürzt die Datei | rc 2 | rc 2 |
| `echo hi;>>team-kits/kernel/state.py` | ändert nichts (Anhängen ohne Ausgabe) | rc 0 | rc 2 |
| `echo hi;>docs/free.txt` (Gegenrichtung, freier Bereich) | — | rc 0 | rc 0 |

Zwei Dinge daran sind Befund über die **Messung**, nicht über das Gate: der erste Schiedsrichter
dieser Runde fragte, ob die Datei danach den geschriebenen Inhalt trägt — eine **gekürzte** Datei
sah damit unberührt aus, und die Zeile oben wäre als „schreibt nicht" durchgegangen. Das Kriterium
ist jetzt „die Datei hat sich geändert". Und die letzte Zeile ist reine Über-Verweigerung: ein
Anhängen ohne Ausgabe ändert nichts, das Gate verweigert trotzdem, weil der Operator die Datei
nennt.

## 3. F2 — ein Verzeichnis, das existiert und nicht betretbar ist (H28)

Gemessen an einem Verzeichnis, dem mit `icacls /deny <user>:(RD,X)` Auflisten und Betreten entzogen
wurden:

| Frage | Antwort |
|---|---|
| `os.path.isdir` | **True** |
| `os.stat` | liefert einen Datensatz |
| `os.access(X_OK)` | **True** |
| `os.listdir` / `os.scandir` | `PermissionError` |
| `os.chdir` (eigener Prozess) | `PermissionError` |
| `bash -c 'cd <verzeichnis>'` | `Permission denied`, die Shell bleibt stehen |

| Zeile | bash | vorher | nachher |
|---|---|---|---|
| `cd "<entzogen>" ; <schreiben>` | schreibt | **rc 0** | **rc 2** |
| `cd "<erreichbar>" ; <schreiben>` (Gegenrichtung) | schreibt nicht | rc 0 | rc 0 |

Der Docstring, der dazu gehörte, sagte *„a directory a process can enter exists"* — das ist die
Umkehrung der gebrauchten Aussage. Von den sechs Fragen oben antwortet nur das **Öffnen** des
Verzeichnisses so wie die Shell.

**Was der Fix kostet, und es ist nicht gemessen, sondern hergeleitet:** ein Verzeichnis, das ein
Prozess betreten, aber nicht auflisten darf (POSIX `--x`, Windows „Ordner durchsuchen" ohne „Ordner
auflisten"), scheitert am Öffnen, während `cd` gelänge. Die Basis bleibt dann stehen — das ist die
verweigernde Richtung, dieselbe wie in H20.

**Nebenbefund, der die Testform bestimmt hat:** ein Verzeichnis, dem `(F)` entzogen wird, ist danach
von demselben Konto weder lesbar noch zurückzusetzen noch zu übernehmen — `icacls`, `takeown` und
`Set-Acl` antworten alle „Zugriff verweigert", und das Verzeichnis überlebt jede spätere Aufräumung
der Suite. Der Test entzieht deshalb genau `(RD,X)` und prüft nach dem Zurückgeben nach, dass ein
Prozess wieder hineinkommt.

## 4. Gate 3 — „vorher" ist, was die Zeile zeigen kann (H26)

Mit gültigem Urteil im Baum, sonst wäre jede Zeile aus einem anderen Grund rc 2:

| Zeile | vorher | nachher |
|---|---|---|
| `git commit -m wip` | rc 0 | rc 0 |
| `echo more >> docs/note.md && git commit -m wip` | rc 2 | rc 2 |
| `echo more >> docs/note.md & git commit -m wip` | **rc 0** | **rc 2** |
| `sed -i "s/a/b/" docs/note.md & git commit -m wip` | **rc 0** | **rc 2** |
| `git commit -m wip & sed -i "s/a/b/" docs/note.md` | **rc 0** | **rc 2** |
| `(echo more >> docs/note.md);git commit -m wip` | **rc 0** | **rc 2** |
| `git commit -m wip ; sed -i "s/a/b/" docs/note.md` (Gegenrichtung) | rc 0 | rc 0 |
| `git add -A && git commit -m wip` (Gegenrichtung) | rc 0 | rc 0 |

Die vorletzte Zeile ist der Grund, warum die Regel nicht „alles davor" heißt: ein Befehl im
Hintergrund hat kein Davor. Die letzte Gegenrichtung zeigt die andere Seite — nach einem Commit, auf
den die Shell gewartet hat, ist ein Schreibzugriff wieder harmlos.

## 5. F9 — die Reserve war ein Anteil und deckte den Prozessstart nicht (H23)

Was **vor** der ersten Zeile von `_harness.py` passiert (Interpreterstart plus Import), gemessen
über sieben Läufe einer Sonde, die `time.monotonic() - _LOADED_AT` meldet, während ihr Elternprozess
den ganzen Prozess stoppt:

| Lauf | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| vor der ersten Zeile (s) | 0,79 | 0,66 | 0,52 | 0,67 | 0,80 | 0,53 | 0,81 |

Ein Kandidat auf einem nicht erreichbaren Host (RFC-5737-Bereich, eine Frage kostet hier 42,1 s):

| registrierte Frist | vorher | nachher |
|---|---|---|
| 6 s | rc 2 nach 5,37 s | rc 2 nach 4,92 s |
| 1 s | **rc 2 nach 1,55 s — nach der Frist** | rc 2 nach 0,52 s |

Ein Fünftel von 1 s ist 0,2 s, der Prozessstart hier 0,52–0,81 s: der Anteil allein hat die
Eigenschaft, die sein eigener Kommentar behauptete, unter kurzen Fristen nicht erfüllt.

**Was die Untergrenze kostet:** unter einer registrierten Frist, die kürzer ist als sie, ist das
Budget null, und das Gate verweigert jeden Aufruf, für den es das Dateisystem fragen muss. Das steht
als Preis an `_harness._RESERVE_FLOOR`.

## 6. F8 — der Matcher ist ein Ausdruck, keine Alternation von Namen

Zwei Registrierungen desselben Gates, eine wörtlich mit 60 s, eine als Ausdruck (`Ba.h`) mit 5 s;
Aufruf auf `Bash`, ein Kandidat auf einem nicht erreichbaren Host:

| | vorher | nachher |
|---|---|---|
| 60 s wörtlich + 5 s als Ausdruck | **rc 0 nach 43,13 s** | rc 2 nach 4,06 s |

Vorher wurde die Gruppe mit der **kürzeren** Frist übersprungen, das Gate rechnete mit 60 s und
hätte den Kill nicht überlebt. Die Gegenrichtung im selben Test: eine Gruppe, deren Matcher auf
diesen Aufruf nicht passt (`NeverFires`, 1 s), verkürzt nichts — sonst wäre der Fix „nimm einfach
die kleinste Zahl in der Datei".

## 7. F4 — die Frist des Gates und die Frist des Providers sind zwei Zahlen (H25)

Gemessen ist die eine Hälfte: das Gate folgt der **Datei**, bei jedem Aufruf.

| registriert | Antwort des Gates |
|---|---|
| 6 s | rc 2 nach 4,92 s |
| 1 s | rc 2 nach 0,52 s |
| 60 s (+ 5 s als Ausdruck) | rc 2 nach 4,06 s |

Die andere Hälfte ist **nicht** von hier aus messbar: wann der Provider tötet, hat er beim
Sitzungsstart gebunden. Dass er es dort bindet, ist die Zusage, auf der dieses Repo ohnehin steht —
`SR-0006` („Alle vier binden beim Sitzungsstart") und der Neustart-Hinweis in jeder Verweigerung
(`_harness.ESCAPE_NOTE`). Solange eine Sitzung läuft, sind die beiden Zahlen damit entkoppelt.

Was daran eine Kette ist: `.claude/` ist dem **Sitzungsagenten** verweigert und einem **Subagenten**
offen (H12, dort gemessen). Wer als Subagent `.claude/settings.json` schreiben darf, setzt die Zahl
hoch, die sich das Gate zugesteht, ohne die zu ändern, nach der getötet wird.

## 8. Mutationen — jeder gebaute Zweig einzeln

Defekt in einer Kopie außerhalb des Repos wiederhergestellt, die zugehörigen Tests gefahren:

| Mutation | Test | Ergebnis |
|---|---|---|
| die Pipeline-Trennung der Kits, unverfeinert | `…refuses_a_line_exactly_where_the_shell_would_write` | **rot** |
| der asynchrone Trenner ist keiner | dito | **rot** |
| ein Schnitt ist eine Schreibweise, kein Zeichen im Lauf | dito | **rot** |
| ein bedingter Operator beendet die Liste | dito | **rot** |
| eine Hintergrundliste läuft in der Shell selbst | dito | **rot** |
| ein Pipelineglied läuft in der Shell selbst | dito | **rot** |
| eine Gruppe zählt erst ab dieser Pipeline | dito | **rot** |
| eine geschlossene Gruppe hält das Verb weiter | dito | **rot** |
| ein unplatzierbarer Trenner ist ein gewöhnliches Wort | `…separator_this_reader_cannot_place_refuses_the_line` | **rot** |
| ein existierendes Verzeichnis ist ein betretbares | `…does_not_follow_a_move_no_process_can_make` | **rot** |
| die Reserve ist ein Anteil und sonst nichts | `…answers_before_its_registration_gives_up` | **rot** |
| ein Matcher ist eine Alternation von Namen | `…answers_before_the_shortest_registration_that_applies` | **rot** |
| jede Registrierung gilt | dito | **rot** |
| ein Commit, auf den die Shell nicht wartet, ist trotzdem ein Zaun | `…refuses_a_line_that_moves_the_tree_before_it_commits` | **rot** |

## 9. Die Reste, am neuen Stand gemessen

| Kette | rc | Eintrag |
|---|---|---|
| `cp -r project_memory <außerhalb>/copy` | 2 | H18 (Über-Verweigerung) |
| `robocopy team-kits <außerhalb>/bk /E` | 2 | H18 |
| `tar -czf <außerhalb>/bk.tgz team-kits` | 2 | H18 |
| `cd "$NOWHERE" && sed -i … team-kits/kernel/state.py` | 2 | H20 (Über-Verweigerung) |
| `R="<außerhalb>" ; sed -i … "$R/team-kits/kernel/state.py"` | **0** | H16 (offen) |
| `Set-Location <außerhalb> ; Push-Location "<repo>" ; Set-Content team-kits/…` | 2 | H21 — verweigert, weil die Zeile den Repo-Pfad wörtlich nennt |
| `Set-Location <außerhalb> ; Push-Location "$env:R" ; Set-Content team-kits/…` | **0** | H21s Kette, und sie läuft — der Grund ist H16 |
| `while true ; do cd "<außerhalb>" ; break ; done ; <schreiben>` | 2 | H24, Über-Verweigerung (bash schreibt nicht) |
| `if cd "<außerhalb>" ; then true ; fi ; <schreiben>` | 2 | H24, Über-Verweigerung |
| `arr=(a b) cd "<außerhalb>" ; <schreiben>` | 2 | H24, Über-Verweigerung |

Die drei H24-Zeilen sind in `bash` gemessen: die Shell geht dort wirklich hinaus, das Gate folgt ihr
nicht und verweigert den relativen Schreibzugriff. Bei allen dreien meldet der Leser der Kits ein
anderes Verb als das Verzeichnisverb (`do`, `cd` hinter `if`, das erste Element der Feldzuweisung),
also bewegt sich die Basis gar nicht erst.

## 10. Suite

`python -B -m pytest .claude/hooks/test_gates.py -q` — 118 grün vor dieser Runde, 125 danach.
