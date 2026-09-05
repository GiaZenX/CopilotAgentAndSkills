# TSK-0125 — Prüfbericht Runde 1 (`harness-verifier`)

Gegen den laufenden Code gemessen, read-only auf Repo und Worktree. Alle Kopien und Rigs unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0125\verify\` (Worktree-Kopien **ohne** `.git`,
zusätzlich zwei eigene Klone: `base` = pristine `75a00d1`, `applied` = `base` + Patch).
Kein Commit, kein Push, keine volle Suite, keine Brenner, ein pytest zur Zeit.

**Urteil: FAIL (Nacharbeit).** Vier Aussagen behaupten Schutz, den der Code nicht baut (F2, F3, F4)
bzw. lassen die tragende Zeile von AC-2 ohne rot-fähigen Test (F1). **Keiner** der Befunde ist
blockierend im Sinne einer in einer Sitzung durchlaufenden Angriffskette; alle sind Nacharbeit vor
dem Merge bzw. benannte Reste. Fachlich sind AC-1..AC-4 in der Sache erfüllt und jeder Rot-Zuerst
ist von mir selbst reproduziert.

---

## Urteil je Kriterium

| Kriterium | Urteil | Grundlage |
|---|---|---|
| AC-1 (BUG-0069) | **PASS** | gehosteter Lauf unabhängig bestätigt; beide Roten von mir rot gesehen und mit dem Fix grün, auf **beiden** Plattformen; Nachher-Richtung korrekt als Nutzerschritt benannt |
| AC-2 (BUG-0025) | **PASS mit Befunden** (F1, F2, F3, F5) | Stolperdraht in beiden Richtungen rot, Sweep rot + benennt die Datei, alle Zahlen von mir nachgemessen; **aber** die Pin-Zeile selbst hat keinen Test, der ohne sie rot wird |
| AC-3 (BUG-0088) | **PASS** | Pilot-Rot am echten Prozess reproduziert; umbenannte Rolle wird gefunden; der Satz erreicht `stdout` |
| AC-4 Solo-Hälfte | **PASS** | Solo-Rot an `75a00d1` reproduziert (4,66 s gegen 4,50 s); Budget abgeleitet, keine getippte Zahl; der Knoten fällt weiterhin, wenn der Mechanismus bricht |
| AC-4 Rig-Entwurf | **PASS mit Befunden** (F4, F6, F7, F8) | alle vier Verweigerungen ohne Fenster gemessen, nichts geschrieben |
| AC-4 Last-Hälfte | **ausstehend im Fenster des Leads** — kein Befund | von mir nicht gemessen (kein Fenster geöffnet, keine Brenner gestartet) |
| Pflicht 5 (Rot-Zuerst, Zahlen, Löcher) | **PASS mit Befund F5** | je Kriterium selbst rot gesehen; jeder benannte Test mutiert und rot gesehen |
| Pflicht 6 (Nähte) | **PASS** | per AST: **genau eine** geänderte Definition in `test_gates.py`; Protokoll nennt `kitupdate.py` als G4-2 verboten |
| Pflicht 7 (Übergabe) | **PASS** | Patch sauber, Scratch am richtigen Ort, Rigs verweigern außerhalb ihres Verzeichnisses |
| Pflicht 8 (Host-Regel) | **PASS** | Rig-Parameter stehen vor dem ersten Lauf im Protokoll; kein Lauf sättigt den Host |

---

## Befunde, blockierendste zuerst

### F1 — `.gitattributes:10`: die Zeile, auf der AC-2 ruht, hat keinen Test, der ohne sie rot wird
**Schwere: mittel. Nacharbeit vor dem Merge, nicht blockierend.**

`* text=auto eol=lf` ist die Ableitung, die BUG-0025 schließt. Alle drei neuen Prüfungen lesen den
**Arbeitsbaum** (`git ls-files --eol`, Spalte `w/`), und der bleibt LF, auch wenn das Pin
verschwindet — die Dateien auf der Platte sind ja schon LF.

Gemessen (`verify/applied`, Mutation, Zeile gelöscht):

```
$ grep -v '^\* text=auto eol=lf$' ../ga.bak > .gitattributes
$ python -B -m pytest -q -p no:cacheprovider tools/test_repo_hygiene.py -k "binary_pin or crlf or line_ending"
3 passed, 25 deselected in 3.79s
$ git check-attr text eol -- README.md
README.md: text: unspecified
README.md: eol: unspecified
```

Dass die Zeile trägt, habe ich getrennt bewiesen (`verify/eolproof.py`, zwei Wegwerf-Repos auf
diesem Host mit `core.autocrlf=true`):

```
--- without-pin   i/lf  w/crlf  note.md      i/lf  w/crlf  tool.py
--- with-pin      i/lf  w/lf    note.md      i/lf  w/lf    tool.py
```

Zweite Mutation, gleiche Blindheit: die beiden `binary`-Zeilen durch ein `* binary` ersetzt →
`3 passed`, während jede Textdatei `-text` wird und der Sweep gar nichts mehr sieht
(`attr/-text` für `note.md`, gemessen im dritten Fall von `eolproof.py`).

*Kein Verstoß gegen „jeder Fix braucht einen roten Test": die Pin-Zeile stammt aus `75a00d1` und ist
nicht die Änderung dieses Stroms; das `*.png binary`, das der Strom hinzufügt, HAT seinen roten Test
(unten). Es ist eine Vollständigkeitslücke gegen den Wortlaut von AC-2 („`.gitattributes` pinnt jede
Textklasse").*

**Minimaler Fix:** eine Zusicherung, die die **Wirkung** bei git erfragt, dieselbe Teilung wie im
Binär-Test — `git check-attr text eol -- <eine verfolgte .md und eine .py>` muss `auto` / `lf`
antworten.

### F2 — `tools/normalise_line_endings.py:82` (+ `:10`, `docs/line-endings.md:65`): die Verweigerung nennt einen Grund, der falsch sein kann
**Schwere: mittel. Nacharbeit, nicht blockierend (Klasse im Repo heute leer).**

Die Vorbedingung ist richtig (sie verweigert), die **Begründung** nicht: trägt der Blob in `HEAD`
selbst CRLF, sagt das Werkzeug „it carries a real uncommitted change", obwohl die Datei
**unverändert** ist. Der Docstring behauptet dazu `The committed blob is therefore already correct`
(`:10`) — für diese Klasse falsch. `docs/line-endings.md:65` wiederholt den Satz auf Deutsch.

Gemessen (`verify/normrig.py`, Wegwerf-Repo):

```
HEAD blob bytes: b'k1\r\nk2\r\n'
i/crlf  w/crlf  attr/text=auto eol=lf   keepcrlf.md
2 file(s) REFUSED -- each one is named with what stopped it:
  keepcrlf.md: normalised it is 6 bytes and HEAD holds 8 -- it carries a real uncommitted change, ...
git status for keepcrlf.md (is there REALLY an uncommitted change?): ''
```

Die richtige Abhilfe dort ist `git add --renormalize`, nicht eine Handentscheidung über eine
Änderung, die es nicht gibt. Heute nicht erreichbar: `verify/blob_crlf.py` — 1278 Textpfade,
**0** mit CRLF im `HEAD`-Blob.

**Minimaler Fix:** vor der Byte-Gleichheit prüfen, ob der Blob selbst CRLF trägt, und in dem Fall
diesen Grund plus `git add --renormalize` nennen.

### F3 — `tools/normalise_line_endings.py:53/73` gegen `tools/test_repo_hygiene.py:118`: die Abhilfe hat die Ausnahme nicht, die die Prüfung hat — und das Protokoll behauptet sie
**Schwere: mittel. Nacharbeit, nicht blockierend (Wirkung durch die Byte-Gleichheit begrenzt).**

`test_no_tracked_text_file_checks_out_with_crlf` nimmt den kanonischen Teil von `project_memory/`
über `_repairable` aus, weil Gate 1 dorthin keinen Werkzeugschreibzugriff lässt. `drifted_files()`
und `judge()` im Werkzeug kennen **kein** `_repairable`: sie nehmen jeden driftenden Pfad. Das
Protokoll (Abschnitt 3, Merge-Zeile, `stream-protocol.md:196`) sagt über die eine kanonische Datei
„kanonischer Zustand, den kein Werkzeugschreibzugriff erreicht" — eine Behauptung über genau dieses
Werkzeug, die es nicht baut.

Gemessen (`verify/audit_reach.py`, nur gelesen):

```
on disk        : 179461 bytes, 598 CRLF pairs
normalised     : 178863 bytes
HEAD blob      : 178635 bytes
precondition   : fails -> the tool refuses it (by accident of this file's size)
```

Es scheitert **heute** an der Größe, nicht an einer Regel. `python tools/normalise_line_endings.py
--apply` ist eine Zeile, die Gate 1 durchlässt. Begrenzt ist der Schaden dadurch, dass das Werkzeug
nur schreibt, wenn das Ergebnis dem committeten Blob **gleicht** — es kann keinen Inhalt einbringen.

**Minimaler Fix:** ein Prädikat für beide — `_repairable` in das Werkzeug ziehen und im Test von
dort importieren (oder umgekehrt); das Werkzeug überspringt kanonischen Zustand und sagt es.

### F4 — `_round-scratch/TSK-0125/under_load.py:28` und `stream-protocol.md:331`: der zweite Tötungspfad ist so nicht gebaut
**Schwere: niedrig-mittel. Nacharbeit am Satz, das Rig selbst bleibt.**

Behauptet: „their pids are written to `LOAD_BURNER_PIDS` **before the first one starts**" /
„ihre PIDs stehen in `LOAD_BURNER_PIDS`, **bevor** der erste startet". Gebaut ist das Gegenteil der
Reihenfolge (`under_load.py:100-104`):

```
100:            burners.append(subprocess.Popen([sys.executable, "-c", SPIN],
...
104:                pidfile.write("\n".join(str(one.pid) for one in burners) + "\n")
```

Der erste Brenner **läuft**, bevor irgendeine PID aufgeschrieben ist — und die Aussage ist nicht nur
unscharf, sie ist als Satz unmöglich: eine PID existiert vor ihrem Prozess nicht. Ein harter Ausfall
in genau diesem Fenster hinterlässt einen Brenner, den Tötungspfad 3 nicht kennt.

**Minimaler Fix:** den Satz auf das schreiben, was der Code baut („nach jedem Start, so dass ein
abgeschnittener Lauf höchstens den letzten Start nicht verzeichnet hat"), oder die Kinder in einer
Prozessgruppe/Job starten, deren Kennung vorher feststeht.

### F5 — dieselbe wachsende Zahl steht an **vier** ausgelieferten Stellen
**Schwere: niedrig. Nacharbeit; die Hausregel meint genau diesen Fall.**

`1794 tracked files / 516 binaries / 499 with CRLF` steht in
`.gitattributes:12-13`, `docs/line-endings.md:43-46`, `tools/normalise_line_endings.py:21-23`,
`tools/test_repo_hygiene.py:97-98`. Nachgemessen (`verify/count_binaries.py`) sind heute **alle vier
richtig** — genau das ist das Problem: sie sind heute richtig und es gibt vier, die altern können.

```
tracked files            : 1794
git says -text (binary)  : 516
NUL in first 8000 (mine) : 516
of those, contain CRLF   : 499
disagreements            : 0 []
binary kinds by extension: [('.png', 496), ('.woff2', 20)]
```

**Minimaler Fix:** die Messung bleibt im Protokoll und in der Löcherliste; die Kommentare tragen die
**Eigenschaft** („gits `text=auto`-Heuristik und ein NUL-Scan stimmen über den ganzen Baum überein")
und den Test, der sie nachmisst — nicht die Stückzahl.

### F6 — `under_load.py:14` / `stream-protocol.md:322`: „a wider setting is refused" ist eine Über-Behauptung
**Schwere: niedrig.** Gemessen (ohne Fenster, also nur bis zur ersten Verweigerung):

```
$ python -B under_load.py rig-base x 60 --burners 16 -- python -c "print(1)"
refused: no load window is open. ...
```

`main` liest `argv.index("--")`; Wörter davor werden nie angesehen. Verweigert wird nichts — die
Breite ist schlicht **nicht einstellbar**. Die Eigenschaft („kein Lauf kann breiter werden") hält;
das Wort „refused" hält nicht. Fix: Wortwahl, oder unbekannte Wörter vor `--` wirklich ablehnen.

### F7 — `under_load.py:105`: der Deckel hält den Host bis zu `cap + 2 s`
**Schwere: niedrig.** `time.sleep(2)` steht **nach** dem Start der Brenner und **vor** dem Kind, der
Deckel gilt nur für `child.wait(timeout=cap)`. AC-4 sagt „inside a window of at most 120 s"; gebaut
sind bis zu 122 s. Fix: die Anlaufzeit vom Deckel abziehen oder den Satz auf 120 s + Anlauf ändern.

### F8 — `under_load.py:65`: der Vorlauf-Kill prüft keine Identität
**Schwere: niedrig, Gefahr real.** `_sweep_previous` schickt `SIGTERM` an jede Zahl aus
`LOAD_BURNER_PIDS`. Die Datei überlebt **nur** einen harten Abbruch — nach dem der Host neu startet
und PIDs neu vergeben werden. Ein stehengebliebener Eintrag tötet dann, was gerade diese Nummer
trägt. Fix: `(pid, create_time)` oder ein Erkennungsargument im Spinner speichern und nur töten, was
sich als eigener Brenner ausweist.

### F9 — Beobachtung, kein Befund gegen den Umsetzer: auf POSIX ist die ROOT-Hälfte des Wächters gar nicht erreichbar
`_duties.py:306` (`candidate == base`) entfernt → Windows-Knoten **rot**, Linux-Knoten **grün**:

```
Windows: E AssertionError: '....//<year>/' was placed at the project root ...  1 failed
Linux  : 1 passed
```

Ursache, gemessen (`verify/posix_root_probe.py` unter WSL): `_literal_prefix` gibt für
`./<year>/`, `<year>/` und `x/../<year>/` `''` zurück, `_project_directory` kehrt vor dem Wächter um.
Es gibt auf POSIX keine Schreibweise, die durch `_literal_prefix` hindurch auf der Wurzel landet —
**genau deshalb war die alte Zusicherung dort falsch**. Ich habe das zuerst als verlorene Deckung
gelesen; das war mein Fehler. Bleibt nur eine Docstring-Nuance: „Both ends here" ist eine
Windows-Aussage, und die zweite Hälfte (der Feed über einen Ordner, den es wirklich gibt) ist auf
POSIX leer, weil `root/....` dort nicht angelegt wird.

---

## Ausdrückliche Negativ-Befunde

### Gemessen (von mir, mit Kommandozeile und Ausgabe)

**Patch / Übergabe**
* 10 Dateien, alle im `allowed_scope`; **keine** VERSION-Hunks; 65 388 B, **0** CR-Bytes;
  `git apply --check` gegen `75a00d1` → `rc=0`.
* Alle 13 geänderten Dateien im Worktree CR-frei (einzeln gezählt).
* `test_gates.py`: per `ast` gegen `75a00d1` verglichen — `added: []`, `removed: []`,
  `changed: ['test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge']`,
  also **genau ein** Test.
* `rig.py` und `under_load.py` verweigern außerhalb ihres Verzeichnisses; ohne Fenster wird nichts
  geschrieben (kein `load-x.txt`, kein `LOAD_BURNER_PIDS`).

**AC-1**
* Gehosteter Lauf `33835146802` unabhängig über `gh` bestätigt: ubuntu `1 failed, 4465 passed,
  105 skipped`; windows `1 failed, 4500 passed, 70 skipped`; die beiden Namen sind
  `test_a_filing_plan_that_resolves_to_the_project_ROOT_is_not_walked` und
  `test_the_route_reader_finds_the_spelling_it_claims_and_leaves_the_slash_form_alone`
  (`ValueError: path is on mount 'C:', start on mount 'D:'`).
* Ubuntu-Rot selbst reproduziert (WSL Ubuntu, Windows-`pytest` über `PYTHONPATH`), an `base`:
  `AssertionError: '....//<year>/' was placed at the project root ... test_office_duties.py:669`;
  mit Fix `1 passed` auf Linux **und** `1 passed` auf Windows.
* Der `....`-Fix fragt wirklich das Dateisystem und stimmt auf beiden Hosts mit dem Wächter überein
  (`verify/posix_probe.py`): Linux `filesystem_says_root=False / guard_placed=/tmp/…/....`,
  Windows `True / None`.
* Cross-Mount-Rot selbst reproduziert: `--basetemp=//localhost/C$/…` an `base` →
  `ValueError: path is on mount '\\localhost\C$', start on mount 'C:'`; mit Fix `1 passed`.
* **Zur Frage nach einem anderen Laufwerksbuchstaben:** auf diesem Host nicht baubar. Ein
  `subst X:` wird von `os.path.realpath` nach `C:` aufgelöst, bevor pytest `tmp_path` bildet — der
  Basis-Test lief mit `--basetemp=X:\bt` **grün** durch. Der UNC-Ersatz des Umsetzers ist damit der
  richtige. Strukturell hält der Fix für **jeden** Mount: `os.path.relpath(path, kit_dir)` startet
  am Glob-Wurzelverzeichnis, unter dem jeder Treffer per Konstruktion liegt.
* Beide Fixes liegen ausschließlich in `tools/`-Tests; kein Leser unter `team-kits/` ist berührt
  (Patch-Dateiliste).

**AC-2**
* Stolperdraht in **beiden** Richtungen rot:
  `*.png binary` entfernt → `AssertionError: git reads these files as binary by their bytes, but no
  binary line ... covers them: [496 .png]`; `*.zzz binary` ergänzt → `AssertionError: these binary
  lines match no binary file this repo carries any more ... ['*.zzz']`.
* Sweep rot und **benennt** die Datei: ein einzelnes CR in `README.md` → `w/mixed` →
  `AssertionError: 1 tracked text file(s) carry CRLF ... Files: ['README.md']`.
* Boden unter `_repairable` rot bei Aufweichung (`return True`) →
  `AssertionError: canonical state is what the exclusion is for`.
* Ganze Suite in `applied` (Klon mit `.git`): `tools/test_repo_hygiene.py` → **28 passed** (89 s).
* Frischer Klon auf diesem Host (`core.autocrlf` lokal **und** system `true`): **0** CRLF-Dateien.
* Die vier vom Umsetzer genannten Attacken durchgespielt (`verify/normrig.py`):
  einzelnes CR → git liest `-text` (Sweep sieht es nicht, außerhalb von AC-2);
  gemischte Enden → `w/mixed`, normalisiert;
  Binär mit Text-Endung ohne NUL → git nennt es Text, wird normalisiert (genau der Grund für die
  `binary`-Zeilen, und der Kommentar sagt es so);
  Text mit Binär-Endung → durch das Pin `-text`, außerhalb von Sweep und Werkzeug.
* Merge-Erwartung nachgerechnet, direkt am Haupt-Checkout (nur gelesen): 51 `w/crlf` + 2 `w/mixed`
  = **53**, davon 33 außerhalb `project_memory/`, 19 unter `staging/`, **1** kanonisch, und die eine
  ist `project_memory/.audit/hook_events.jsonl`. Die Protokollzeile „52 normalisiert, eine bleibt"
  stimmt.
* Doku-Behauptungen geprüft: `install.sh:243-247` ruft `validate.py` vor der Installation und bricht
  mit `exit 1` ab; `team-kits/kernel/hashing.py:249` normalisiert CRLF im `kit_hash`
  (`handle.read().replace(b"\r\n", b"\n")`).
* **Folge für den Merge:** mit diesem Paket ist `test_no_tracked_text_file_checks_out_with_crlf` im
  Haupt-Checkout **rot** (52 Dateien), bis `python tools/normalise_line_endings.py --apply` dort
  gelaufen ist. Das steht so im Protokoll; ich bestätige die Zahl und benenne es als
  Merge-Vorbedingung, nicht als Defekt.

**AC-3**
* Pilot-Rot am **echten** Prozess selbst reproduziert (`verify/ac3`, Defekt
  `_follow_up` → `_pending_templates`, mit `bump_kit_version.py` neu gestempelt):
  `AssertionError: the update left a memory tree no installed role declares and told nobody:` —
  die Ausgabe nennt Release und Neustart und über den Baum kein Wort. Mit Fix `4 passed` (13,7 s).
* **Umbenannte Rolle wird gefunden** (`verify/ac3_probe.py`): Baum `quality-engineer`, installiert
  ist `qa-engineer` → `{'orphaned': [('quality-engineer', 'no role definition of that name is
  installed any more', 2)], 'read': True}`.
* Der Satz erreicht den Nutzer im echten Berichtspfad (der Pilot liest `stdout`, also einschließlich
  `kernel/cli.py`); Wortlaut gelesen und verständlich, nennt Pfad, Dateizahl, Grund und sagt
  ausdrücklich, dass nichts entfernt wurde.
* Gegenende hält: eine Rolle, die `memory:` noch deklariert, taucht nicht auf; ein leerer Wert
  (`memory:` ohne Inhalt) zählt als vorhanden; eine unlesbare Rollendatei wird mit „carries no
  `memory:` this command could read" gemeldet, nicht als „hat den Schlüssel fallen gelassen".
* Ein Verzeichnis unter `agent-memory/`, das gar keine Rolle ist (`_shared/`), wird als Rest mit dem
  Grund „no role definition of that name is installed any more" gemeldet — nach dem Modell des
  Kit-Hakens (`guard_memory_budget` liest `agent-memory/<rolle>`) ist das die richtige Annahme;
  ich führe es als Beobachtung, nicht als Befund.

**AC-4 (Solo-Hälfte und Rig-Entwurf)**
* Solo-Rot an `75a00d1` reproduziert:
  `AssertionError: the gate answered after 4.66s while its registration gives it 4.50s ...
  assert 4.661525200000142 < 4.5` — deckt sich mit den 4,62 s des Umsetzers.
* Mit Fix solo `1 passed` (20,7 s).
* Budget **abgeleitet**, keine getippte Zahl: `_registrations` misst einen echten Verdikt-Lauf,
  `_reserve_numbers` liest `_harness._SPENDABLE_SHARE = 0.8` und `_RESERVE_FLOOR = 1.5`
  (`_harness.py:113/124`), `seconds = ordinary + floor` wird in die **Registrierung der Kopie**
  geschrieben. Die echte Registrierung in `.claude/settings.json` ist für jeden Eintrag `120`
  (nur gelesen) — der Knoten misst also gegen eine selbst erzeugte, abgeleitete Frist, nicht gegen
  eine Konstante.
* **Der Knoten kann weiterhin fallen.** Zwei Mutationen:
  * Gate 3 um 2,0 s verlangsamt (`sleep` vor `decide()`) → `1 passed`. Das ist richtig so: der
    Budget-Wächter feuert früher, und genau „antwortet vor seiner Registrierung" ist der Satz des
    Tests. Sein Subjekt ist der Wächter, nicht die Rohgeschwindigkeit des Gates — das habe ich
    gemessen, damit es nicht als Deckung gelesen wird, die es nicht ist.
  * Budget-Wächter abgeschaltet (`threading.Thread(target=_the_budget_is_spent…)` entfernt) →
    `Failed: the gate answered after 11.76s while its registration gives it 4.50s ... this host's
    own process start is 0.25s with 0.06s of noise -- that FITS in the reserve, so the overrun is
    the gate's and not the machine's`. Der Knoten nimmt also den **fail**-Zweig, nicht den Skip, und
    unterscheidet „Maschine" von „Gate" korrekt.
* Rig-Verweigerungen ohne Fenster, alle vier gemessen: ohne Fenster, mit `cap 300`, mit einem
  Breiten-Argument, und außerhalb des eigenen Verzeichnisses. Es wurde nichts geschrieben.
* `os.cpu_count()` auf diesem Host = **16**, also 8 Brenner — die Zahl im Protokoll stimmt.

**Löcher, Nähte, Läufe**
* `H160`, `H161`, `H162`: Nummern im reservierten Bereich, keine weitere Nummer im Patch; jede
  Zitierung trägt ihr Modulpräfix (`tools/test_kitupdate.py::…`, `.claude/hooks/test_gates.py::…`).
* `H161` gegen die zitierte Datei geprüft: `test_gates.py:5660-5662` — die Uhr startet in 5660, die
  Zeile wird in 5662 gebaut. Das Zitat stimmt.
* Protokoll: Nahttabelle vorhanden; `kitupdate.py` steht dort ausdrücklich als „gehört diesem Strom
  allein und ist G4-2 verboten"; verworfener Weg, vorläufiger Stempel, Wanduhr vorhanden; die
  Token-Zahl ist **als Schätzung gekennzeichnet** und nicht als Messung — richtig so.
* Läufe in meiner Kopie: `ruff check .` → `All checks passed!`; `tools/validate.py` → `all
  structural checks passed`; `tools/bump_kit_version.py` → alle drei `unchanged`;
  `test_ci_lint_pinned + test_context_budget` → `46 passed, 2 skipped` (die 2 Skips, weil meine
  Baumkopie kein `.git` hat) — zusammen mit den 28 aus `test_repo_hygiene` sind das die 76 Knoten
  des Protokolls;
  `test_gates.py::test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`
  → `1 passed` (die in Backticks genannten Testnamen lösen auf).

### Nicht gemessen (bewusst offen gelassen)

* **Die Last-Hälfte von AC-4 (`H162`).** Ich habe **kein** Fenster geöffnet und **keine** Brenner
  gestartet. Damit ist auch die vom Umsetzer berichtete Deckel-Verweigerung
  („refused: cap 300s is over the 120s…") von mir **nicht** nachgemessen — sie steht hinter der
  Fenster-Verweigerung, und die habe ich gesehen. Kein Befund, ausstehend.
* `tools/test_kitupdate.py` als Ganzes (behauptet `86 passed, 1 skipped`, 5:23). Ich habe die vier
  Gedächtnis-Knoten gefahren, den Rest nicht — Host-Regel.
* `tools/test_office_duties.py` und `tools/test_reference_skills.py` als Ganzes (behauptet
  `55 passed` / Linux `54 passed, 1 skipped`). Ich habe je den betroffenen Knoten gefahren, auf
  Windows und auf Linux.
* `.claude/hooks/test_gates.py` als Ganzes — nicht gefahren (ein Knoten geändert, dieser einzeln
  gefahren, plus der Namens-Prüfknoten).
* Die **Nachher-Richtung von AC-1**: der nächste gehostete Lauf. Braucht den Push des Nutzers.
* Der Merge-Schritt `normalise_line_endings.py --apply` im Haupt-Checkout — nicht gefahren, nur
  seine erwartete Wirkung nachgerechnet (52 / 1).
* Die volle Suite (DEC-0050 — gehört dem Merge, nicht dem Prüfer).

---

## Was in die Nacharbeit gehört, und was in die Löcherliste

**Nacharbeit vor dem Merge (nicht blockierend, aber Hausregel 3 und 5):** F1 (eine
`check-attr`-Zusicherung), F2 (Grund und Abhilfe für einen CRLF-Blob in `HEAD`, in Werkzeug **und**
`docs/line-endings.md`), F3 (ein Prädikat für Prüfung und Abhilfe, plus die Protokollzeile 196),
F4 (der Satz über Tötungspfad 2 in `under_load.py:28` und `stream-protocol.md:331`), F5 (die vier
Zahlenkopien auf eine Eigenschaft plus eine Stelle im Protokoll reduzieren).

**Rig-Reste, klein, gehören zum `H162`-Eintrag statt in eine neue Nummer:** F6 (Wort „refused"),
F7 (`cap + 2 s`), F8 (PID-Kill ohne Identitätsprüfung). Die Nummern H160–H162 sind ausgeschöpft;
diese drei sind Eigenschaften **desselben** Rigs, das `H162` schon führt, also gehören sie als Sätze
dorthin und nicht in eine vierte Nummer.

**Merge-Vorbedingung, kein Befund:** `python tools/normalise_line_endings.py --apply` im
Haupt-Checkout, sonst ist die neue Prüfung dort rot (52 Dateien, eine bleibt).

---

## Urteil

**FAIL — Nacharbeit, nichts davon blockierend.** Das Paket erfüllt AC-1 bis AC-4 in der Sache: jeder
Rot-Zuerst ist von mir selbst reproduziert (ubuntu `....` unter WSL, Cross-Mount über einen echten
zweiten Mount, der Kit-Update-Pilot am echten Prozess, der Gate-3-Knoten solo an `75a00d1`), jeder
neue Test lässt sich durch eine Mutation rot machen, der Patch ist sauber und trägt genau einen Test
in `test_gates.py`, und die vier Verweigerungen des umgebauten Lastrigs greifen ohne Fenster. Was
den Durchlauf verhindert, sind vier Sätze und eine Lücke, die alle derselben Hausregel unterliegen:
`normalise_line_endings.py` nennt einen Grund, den `git status` widerlegt; das Protokoll behauptet
für die kanonische Auditdatei einen Schutz, den das Werkzeug nicht baut (heute nur durch die Größe
dieser Datei gehalten); das Lastrig behauptet einen Tötungspfad in einer Reihenfolge, die es nicht
gibt; und die Zeile, auf der AC-2 ruht — `* text=auto eol=lf` — kann gelöscht werden, ohne dass
irgendeine der drei neuen Prüfungen rot wird, während ein frischer Klon auf diesem Host dann wieder
CRLF trägt (von mir in zwei Wegwerf-Repos gemessen). Fünf kleine Fixes, keiner davon größer als ein
paar Zeilen, und das Paket ist abnahmefähig; die Last-Hälfte bleibt `H162` und wartet auf das
Fenster des Leads.
