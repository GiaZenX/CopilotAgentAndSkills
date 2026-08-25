# Lieferprotokoll (Lead) — TSK-0083 + TSK-0084, 2026-08-24

Zwei Aufgaben, eine Lieferung. Die Messprotokolle der Runden sind
`staging/TSK-0083/acceptance.md` (1444 Zeilen, sieben Durchgänge) und
`staging/TSK-0084/acceptance.md` (vier Durchgänge). Dieses Dokument sagt nur, was der **Lead**
entschieden und selbst gemessen hat.

## Was geliefert wird

**TSK-0083** (`BUG-0063`, dazu `BUG-0064`, `BUG-0065`): das Ledger-Gate des Office-Kits liest eine
Befehlszeile jetzt so, wie eine Shell sie liest — nicht so, wie sie geschrieben aussieht. Die
Kette der Runde in einem Satz: eine Ausnahme, die einem verbürgten Lauf gilt, befreit nur **seine
eigene Stufe** und nicht die Nachbarn einer Pipeline; ein Name, der über den kanonischen
hinausläuft, ist eine andere Datei; Quotierung ändert nicht, welche Datei ein Wort benennt; jedes
Umleitungsziel eines Segments wird gelesen, nicht nur das erste; und die beworbene Remedy des
Gates wird von ihm selbst akzeptiert (`BUG-0064`).

**TSK-0084** (`BUG-0066`): ein blankes Wagenrücklaufzeichen hebelte `gate_write_scope` in **allen
drei ausgelieferten Kits** aus — PowerShell beendet dort eine Anweisung, `shlex` sieht gewöhnlichen
Leerraum, also wurde die ganze Zeile eine harmlose Pipeline. Gemessen mit echtem Shell-Prozess und
Dateizeugen: `.claude/settings.json` — die Datei, aus der der Provider lernt, **welche** Hooks
laufen — wurde in einem einzigen gegateten Aufruf überschrieben. Geschlossen an der **geteilten**
Vorbereitung (`_compat`), nicht in einem Gate, damit kein Aufrufer die Regel ohne sie bekommt;
welche Zeichen Anweisungstrenner sind, ist gegen echte Shell-Prozesse gemessen statt aufgezählt.
Zwei Nachbarn fielen mit: die Verschweißung zweier Wörter unter der Bash-Schiene und die
Fortsetzungsregel, die die Vereinigung beider Shell-Escapes war (jetzt werkzeugabhängig).

## Die Urteile des Prüfers

- **TSK-0084: PASS**, zweimal bestätigt (`verify1/REPORT-FINAL.md`, `verify2/REPORT-FD.md`): „Das
  Verhalten habe ich in dieser Runde erneut gegen echte Gate-Prozesse gemessen … und es ist
  richtig."
- **TSK-0083: FAIL** in derselben Prüfung, mit **genau einem** blockierenden Befund (F-D2) — nicht
  am Verhalten, sondern an einer Behauptung: der neue Vollständigkeits-Draht des Ledger-Gates
  behauptete eine Vollständigkeit, die er nicht hatte. Der Prüfer hat die **Abnahmebedingung vorab
  benannt**: „Der Fix ist EIN Satz — entweder die Klasse benennen oder den Leser definitorisch auf
  ‚welche Patterns werden wirklich gerufen' umstellen. Kein erneuter Suite-Durchlauf nötig, wenn
  nur der Docstring geändert wird."

## Wie F-D2 geschlossen wurde, und was der Lead daran selbst gemessen hat

Der Umsetzer hat **beide** vom Prüfer genannten Wege genommen, nicht einen: die Klasse steht im
Docstring, **und** ein zweiter, definitorischer Leser ist gebaut (`_patterns_called_by`
instrumentiert jedes modulweite Muster und zeichnet auf, welche beim Laufen wirklich gefragt
werden); der Draht nimmt die **Vereinigung** beider Leser, weil ihre blinden Flecken sich nicht
überschneiden.

Der Lead hat davon selbst gemessen, was von innen messbar ist:

1. **Der zweite Leser ist lebendig, kein stiller Blindgänger.** Der Draht behauptet das nicht,
   er erzwingt es: `tools/test_hooks_v2.py:10533` verlangt, dass der laufende Leser **etwas**
   aufgezeichnet hat, sonst fiele die Vereinigung still auf den anderen Leser zurück. Der Test ist
   grün, also hat er aufgezeichnet.
2. **Die Docstrings behaupten keine Vollständigkeit mehr.** Gelesen im laufenden Code: der Draht
   sagt ausdrücklich „HOW FAR THAT REACHES IS THE TWO READERS' ANSWER AND NOT THIS DOCSTRING'S",
   und `_patterns_called_by` nennt, was **keiner** von beiden sieht, als **Klasse** statt als
   Liste von Schreibweisen.
3. **Der Draht und seine Nachbarn sind grün**: 304 passed über den Draht, die Öffnungs-Zeichen und
   die gestapelten Öffnungen.

**Was der Lead ausdrücklich NICHT selbst gemessen hat, und warum es hier steht:** die Restklasse
(eine Ausnahme, die **gar kein** Muster befragt, bleibt unsichtbar) ist von Umsetzer und Prüfer
unabhängig gemessen — vom Lead nicht. Vier Anläufe mit einer selbstgebauten Sonde meldeten „blind"
auch für Formen, die beide Rollen übereinstimmend als rot gemessen hatten; die Sonde war falsch,
nicht der Code. Ein fünfter Anlauf hätte ein Instrument neu gebaut, das zweimal unabhängig
dasteht. Das ist als **fremde Messung** gekennzeichnet, im Löcherlisten-Eintrag `H70` und hier.

## Was der Lead in dieser Lieferung geschrieben hat

- **Löcherliste** `docs/POST_V2_WISHLIST.md`: `H62`–`H68` (TSK-0083), `H69` (TSK-0084) und `H70`
  (die Messlücke des Drahts, `H10`/`H41`-Klasse) — je mit Mechanismus, gemessener Kette und
  Urteil, dazu Tabellenzeilen und Herkunftszeile. `H41(d)` ist nachgeführt: der neue Zeiger auf
  einen Test einer **anderen** Datei hebt den handaufgelösten Bestand von zehn auf **elf**.
- **`CLAUDE.md`** trägt `DEC-0050`: der Testumfang einer Runde richtet sich nach dem, was sie
  berührt; die volle Suite ist ein **Lieferkriterium** und läuft **einmal**. Der Fall dahinter ist
  gemessen — an TSK-0083 lief sie in sechs Runden mit, rund vier Stunden, und **kein einziger
  Befund kam aus ihr**; alle kamen aus dem Messrig und den Mutationsläufen.
- **`BUG-0067`** erfasst den Hinweis des Prüfers an den Lead: ein Messlauf hat am 23.08.
  Office-Kit-**Vorlagen** in das Zustandsverzeichnis dieser Werkstatt geschrieben. Sie sind
  **nicht** Teil dieses Commits (nicht gestaged, geprüft), und `kernel validate` bleibt bei
  0 Fehlern. Nachbar mit derselben Richtung: `BUG-0052`.

## Lieferkriterien

- Stempel aktuell, geprüft: dev `2026.08.24-7`, office `2026.08.24-16`, research `2026.08.24-7`.
- `kernel validate`: **0 error(s)**, 23 warning(s) (die erwarteten „NOT SEARCHED"-Hinweise über
  Prosa unter `staging/`).
- Löcherlisten-Drähte: 7 passed.
- **Volle Suite (Lieferlauf, DEC-0050): 3842 passed, 14 skipped, 1 failed in 33:43.** Der eine
  Fehlschlag ist `test_the_id_scan_is_linear_on_the_worst_legal_input`, und er ist **die
  Rausch-Sperre dieses Tests selbst**: seine erste Zusicherung verweigert das Urteil, wenn die
  Messung nicht klar über der Streuung des Wirts steht — genau so, wie sein eigener Docstring es
  ansagt („where it does not, this FAILS with that reading instead of asserting on noise").
  Gemessen: Signal 0,187 s gegen Streuung 0,041 s, Schranke Faktor 5, also knapp darunter — der
  Rechner war frisch nach einem Absturz. **Dreimal in Folge grün nachgemessen** auf der ruhigen
  Maschine. Kein Produktbefund; die Linearitäts-Aussage selbst wurde nie verletzt, sie wurde gar
  nicht erst gefällt.
- **Nachmessung der während des Laufs geschriebenen Prosa** (H70, H41-Zahl, `BUG-0067`, dieses
  Protokoll): nach `DEC-0050` die Suiten, die diese Dateien **lesen** —
  `test_disposition.py + test_repo_hygiene.py + test_shortening_net.py` **46 passed**, der
  V1-Draht und die Löcher-Referenzen **41 passed**, die Löcherlisten-Drähte in
  `.claude/hooks/test_gates.py` **7 passed**.
- Push: durch `DEC-0045` vorab freigegeben, wird beim Ausführen angesagt.
