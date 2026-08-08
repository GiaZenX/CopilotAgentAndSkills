# Prüfverdikt TSK-0022, Runde 2 (2026-08-08) — FAIL, aber der Kern trägt

Gesichert in `staging/`, weil `project_memory/` für jeden Aufrufer gesperrt ist. Muss zu Items
werden, was hier als offen steht.

## Was BESTÄTIGT ist (der Prüfer hat es unabhängig gemessen)

- **expected_output 1 erfüllt.** 23 Schreibweisen, Gate-Prozess gegen echtes `bash` als
  Schiedsrichter über die Datei: **jede** Zeile, bei der bash die geschützte Datei schreibt, ist
  rc 2 (`~+/"team-kits"`, `/'team-kits'/`, `/"kernel"/`, `/"state.py"`, `te"am"-kits`,
  `state.p"y"`, `"state".py`, `~-`, `~0/"…"`, `~+0/"…"`); jede Zeile, bei der bash literal bleibt,
  ist rc 0 außer den drei dokumentierten Über-Verweigerungen. **F1 der Vorrunde ist geschlossen.**
- Der geliehene Lexer driftet in keiner geprüften Klasse (unbalancierte Quotierung, `bash -lc`,
  Spanne über das Trennzeichen, Escape vor dem Trennzeichen, getippte Maskenzeichen).
- Rote Tests selbst reproduziert: `readings` zurückgedreht → Tilde-Test rot; `PWD/OLDPWD` aus
  `_changes_the_protected_file` entfernt → Riegel-Test rot in 40 s; `TYPED_READING` nicht angehängt
  → Lexer-Test rot; zwei Prosa-Mutationen rot.
- Suite 137 grün (553 s + 330 s in zwei Selektionen). Laufzeit unkritisch: ein Gate-Prozess
  0,19–0,25 s auch bei 60 Tilde-Wörtern oder 800 quotierten Segmenten. Keine Fehlalarme auf den
  Arbeitszeilen dieses Repos.
- PowerShell-Hälfte stimmt mit dem Protokoll. Achse gegen RELATIVE_WRITE erzeugt (1440 → 1449).
- **Messdisziplin des Prüfers hat gehalten:** 11 geschützte Dateien vor/nach jedem Lauf gehasht,
  alle Läufe `unchanged`, `state.py` durchgehend `ca3e1735…`. Kein vierter Schaden.
- Beide Korrekturen des Umsetzers am Verdikt der Vorrunde sind **berechtigt** und vom Prüfer
  ausdrücklich anerkannt: 157 Präfixe (nicht 205); `OLDPWD` (nicht falsches cwd) war die
  Schadensursache.

## Was BLOCKIERT

- **F1 (mittel, blockierend):** `docs/POST_V2_WISHLIST.md:1868` (H31), `:1969` (H33) und
  `docs/reviews/2026-08-07-tsk0022-measurements.md:78` führen `x=~+/…` als gemessene
  Über-Verweigerung. Gemessen im Stellvertreterprojekt **außerhalb** des Heimatverzeichnisses:
  **rc 0**. Die rc 2 des Umsetzers kam vom **Heimatverzeichnis als Vorfahre** — er hat unter
  `C:\Users\zenti\…` gemessen, dieses Repo liegt in `C:\Offline Repos\AgentAndSkills`. Exakt die
  Zufalls-Verweigerung, die H33 zwei Absätze weiter oben für `~+`/`~+0` selbst protokolliert.
  Zweite Hälfte ebenfalls falsch: bash **erweitert** `x=~+/y` sehr wohl (`x=/c/…/y`); nur
  `--file=~+/y` bleibt literal. Keine Angriffskette (das `x=` bleibt am Wort, `sed` schreibt
  nichts), aber es ist eine Zeile, die „verweigert" sagt, wo das Gate erlaubt — die Klasse, für
  die die Vorrunde durchgefallen ist. Verfehlt expected_output 2 und 7.
- **F2 (hoch für die Aussage, blockierend):** `guard.pin()` des Umsetzers pinnt **nur cwd** und
  lässt `OLDPWD` auf dem echten Repo stehen — wörtlich der Mechanismus, den H37 dokumentiert.
  Gemessen mit Köder-Baum: die `~-`-Nutzlast schrieb den OLDPWD-Baum, während `guard.watch`
  „1 files unchanged" meldete. Dazu `guard.named_in`: liefert für die Rundenzeilen **eine** von
  vier geschützten Zieldateien (`_PATHISH` bricht an den Anführungszeichen,
  `os.path.join(REPO, "/settings.json")` wirft `REPO` weg) — `.claude/settings.json`,
  `_harness.py` und `DEC-0020.yaml` wurden nie gehasht. `docs/POST_V2_WISHLIST.md:2101-2104`
  nennt genau diese Vorrichtung als Begrenzung von H37. Verfehlt expected_output 5.

## Was als benannter Rest einzutragen ist (vor Rundenschluss)

- **F3 (hoch):** `bash <<EOF … EOF` schreibt geschützten Zustand mit **rc 0**, ein Werkzeugaufruf,
  keine Vorbereitung, kein Commit. Mechanismus: `_harness._prose_removed` →
  `gate_write_scope._HEREDOC_RX` entfernt **jeden** Heredoc-Rumpf als Prosa, also ist jedes
  Programm, das eine Shell aus einem Hier-Dokument liest, für beide Gates unsichtbar. Gemessen:
  `bash <<EOF\nsed -i "s/a/b/" team-kits/kernel/state.py\nEOF` → rc 0; dieselbe Nutzlast als
  `bash -c '…'` → rc 2. **Nicht von dieser Runde eingeführt**, aber `command_line`s Docstring
  (`_harness.py:1574-1580`) nennt als Blindstelle ausdrücklich nur `_MESSAGE_ARG_RX`, und H34 nur
  die Flag-/Nachrichtenhälfte. Als **H38** mit Mechanismus (nicht mit den zwei probierten
  Schreibweisen), Kette, Urteil und Begrenzung.
- **F5 (Löcherlisten-Rest, vom Sitzungsagenten unabhängig bestätigt):**
  `team-kits/*/hooks/_audit.py:60` schreibt über `find_repo_root()` nach
  `<root>/project_memory/.audit/`. Im **echten** Repo existiert
  `project_memory/.audit/hook_events.jsonl` mit Fixture-Einträgen (`neighbour-stack`,
  `myproject`), `ts` bis `2026-08-07T20:32:28`. Nachgemessen vom Lead: die Datei **existiert**,
  steht in **keiner** `.gitignore`-Regel — also schreibt `pytest tools/` kanonischen Zustand des
  Baums, den es misst, in genau den Bereich, den Gate 1 **jedem** verweigert. Der Sitzungsriegel
  sieht es nicht (Wachliste: eine Datei). Gehört in H37 als zweite Vorrichtung.
- **F4 (Ein-Satz-Korrektur, kein Rest):** `CLAUDE.md:166-168` behauptet Verweigerung für jedes
  nicht-leere Tilde-Präfix; für `~\+/…` ist sie nicht gebaut (rc 0; bash liest `\+` als Präfix,
  das Gate liest es als leer, weil `\` in `_PATH_SEPARATORS` steht). Der Hook-Kommentar
  (`_harness.py:1158-1167`) sagt es **richtig** — die interne Widersprüchlichkeit ist der Befund.

## Zur ungeklärten Wiederherstellung (Frage f)

Nicht attribuierbar. Gemessen: Arbeitsbaum-`state.py` byte-identisch mit dem Index
(`ca3e1735…`, 71 160 Byte, mtime 20:44:42). **Im ausgelieferten Paket gibt es keinen Pfad, der
das echte Repo zurückschreibt** — `test_gates.py` liest `ROOT` nur, jeder Schreibzugriff geht nach
`tmp_path`, der Riegel meldet und repariert nicht. Im **Apparat** der Runde gibt es genau einen
ungeschützten Rückschreibpfad: `%TEMP%\tsk0022\repair.py:14-21` schreibt `git show :<relative>`
nach `argv[1]/<relative>`, und `guard.pin()` prüft den **Prozess**, nicht das **Ziel**. Seine
mtime (20:52:11) liegt **nach** der Wiederherstellung, es ist also nicht der Täter von 20:44 —
aber dieselbe Klasse, vorhanden und unbewacht. `git checkout --` aus einer Außen-Shell erzeugt
dieselben Bytes und ist von hier nicht unterscheidbar. Befund bleibt: `repair.py` fehlt die
Zielprüfung.

## Vom Prüfer ungemessen gelassen

`pytest tools/` (Behauptung 2305/12), `ruff`, `tools/validate.py`; Gate-3-Tabelle 5a mit gültigem
Urteil (sein Stellvertreterprojekt trug keines); der argv-Übergabeweg des Provider-Bash-Werkzeugs;
Byte-Identität `clone-ship` ↔ Arbeitsbaum; der Suite-Lauf im Arbeitsbaum (1014 s); H22, H34, H35,
H36 unberührt.
