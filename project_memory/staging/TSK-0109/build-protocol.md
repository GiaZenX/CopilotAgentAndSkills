# TSK-0109 — Build-Protokoll (Phase 2 von 2, Opus)

Stream I, FR-0032, DEC-0059/DEC-0060. Worktree `C:\Offline Repos\v2-testbed\_worktrees\g2-dashboard`
(Branch `g2/dashboard`, aus `6d18407`). Scratch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0109\`.
Kein Commit, keine Installation, keine volle Suite (DEC-0057 (b)/(d)/(e)).

Phase 1 (Fable) liegt daneben in diesem Verzeichnis; dieses Blatt trägt nur die Build-Phase. Die
Messungen im Detail: `docs/reviews/2026-09-02-tsk0109-measurements.md` im Worktree.

## 1. Was gebaut wurde

| Datei | Was |
|---|---|
| `team-kits/office-team/templates/repo/tools/finance_dashboard.py` | der Generator: liest Ledger + `project_memory/master_data.yaml` + `business_profile.yaml`, schreibt **eine** Datei |
| `team-kits/office-team/templates/repo/tools/finance_dashboard.template.html` | die Hülle aus Phase 1, unverändert in Gestaltung; zwei Änderungen: der Kopfkommentar sagt jetzt, was die Datei IST statt was aus ihr wird, und die Seitengröße der Liste ist ein Slot (`{{page_rows}}`) statt einer zweiten 100 |
| `team-kits/office-team/templates/repo/dashboards/ABOUT.txt` | Ordnerführer: was hier liegt, welcher Befehl es schreibt, dass es sich **nicht** selbst neu baut, und warum die Datei nicht `README.txt` heißt |
| `tools/test_finance_dashboard.py` | die Testsuite der Seite, je Fall rot gemessen (Stand nach der Nacharbeit: 16 Testfunktionen, 23 Fälle, gemessen 23 passed) |
| `tools/fixtures/finance/…` | die drei Beispielprojekte aus Phase 1, eingefroren (`regular`, `empty`, `alarm`); die Nacharbeit legte `crossyear` und `founding` daneben |
| `docs/reviews/2026-09-02-tsk0109-measurements.md` | die Messungen dieser Runde |
| `docs/POST_V2_WISHLIST.md` | H117, H118, H119 (Zeile in der Tabelle + Eintrag + Herkunft + `**Urteil …**`) |
| `team-kits/office-team/VERSION` | vorläufiger Stempel; nach der Nacharbeit `2026.09.02-14` |

Nicht angefasst: jede Datei im `forbidden_scope` des Items, insbesondere `team-kits/*/hooks/**`,
`templates/project_memory/**`, `templates/repo/scripts/**` und `team-kits/repo_kit_owned.txt`.
`team-kits/office-team/hooks/document_trays.txt` wurde vom Stempler **nicht** neu geschrieben —
siehe Abschnitt 5.

## 2. Die Antworten des Leads, und was aus ihnen wurde

1. **Generator kit-owned.** Gebaut unter `templates/repo/tools/`, wie die Bauanleitung sagt. Die
   Zeile in `repo_kit_owned.txt` (Stream K) und die Verdrahtung in `gate_ledger_valid.py`
   (Stream G) sind Seams, wörtlich in Abschnitt 6. **Folge, eingehalten:** solange die Verdrahtung
   fehlt, ist der Generator ein Hand-Schritt, und **kein ausgelieferter Text behauptet
   „automatisch neu erzeugt"** — `ABOUT.txt` sagt ausdrücklich das Gegenteil, und wie man es
   trotzdem merkt.
2. **`dashboards/finanzen.html` ignorieren.** Die `.gitignore`-Zeile ist ein Seam (unowned),
   wörtlich in Abschnitt 6. Bis dahin würde ein Projekt die erzeugte Datei tracken; die Zeile ist
   die einzige offene Folge davon.
3. **Zahlungsfrist.** Konstante `PAYMENT_TERM_DAYS = 30` im Generator mit der Rechtsquelle daneben
   (§ 286 Abs. 3 BGB), und die Seite druckt beides. Das Profilfeld ist ein Seam an G.
4. **BuyPlugGo-Vorlage:** bis zum Ende dieser Runde **nicht** eingetroffen. Nichts daraus verwendet,
   nichts blockiert; der Vergleich der Ansichtenliste bleibt offen und ist ein Follow-up, kein
   stiller Umbau.

## 3. Was gemessen ist

- **Parität mit `euer_report.py`: 8 von 8 Quartalen.** Verglichen werden die Zahlen **auf der
  Seite** (DOM geparst) gegen den Bericht, den das ausgelieferte Skript als Prozess schreibt.
  Zahlen: Messprotokoll Abschnitt 1.
  **Eine Eigenschaft, die in Phase 1 noch Zufall war**, ist jetzt abgeleitet: die Zahl der offenen
  Posten zählt je Ledgerjahr (`open_until`), weil `ledger_add.validate_cross` jede Zeile in die
  Datei von `payment_date or doc_date` legt — eine offene Zeile liegt also in der Datei ihres
  Belegjahres, und genau die öffnet der Bericht. Vorher stimmte es nur, weil keine Fixture eine
  offene Zeile aus einem früheren Jahr trägt.
- **Rot-zuerst: 14 von 14.** Kopie außerhalb des Repos, je ein Defekt eingesetzt, ein Test gefahren,
  zurückgesetzt (`_round-scratch/TSK-0109/redfirst.py`); danach die Kopie wieder grün (16 passed).
  Die Tabelle mit Defekt je Test steht im Messprotokoll Abschnitt 2; die beiden Enden des
  Aktenfach-Drahts sind einzeln mutiert.
- **Sicht-Schleife (BUG-0076): 54 Bilder aus dem gebauten Stand, 0 Konsolen-/Seitenfehler.**
  Datensatz `review-build/render.json`. Drei Zustände × fünf Reiter × 1280/390/dunkel, dazu
  gefilterte Liste, offene Detailzeile, Mahnfilter und **ein Lauf ohne Skript**. Gesichtet, nicht
  nur erzeugt: Überblick 1280/390, Rechnungen 1280/390, Rechnungen gefiltert, Offene Posten dunkel,
  EÜR, Kleinunternehmer (Alarm), Überblick leer, ohne Skript.
  **Zwei Befunde, beide korrigiert und nachgerendert:**
  1. Ein Betrag stand zweimal verschieden auf einer Seite — das Seitenskript trennte Betrag und
     Eurozeichen mit einem geschützten Leerzeichen, der Generator mit einem gewöhnlichen. Jetzt
     eine Konstante (`CURRENCY_GAP`) mit dem Grund daneben, und der Filtertest vergleicht die
     Seitenschrift gegen eine dritte, unabhängige Schreibweise.
  2. „1 Rechnungen zu zahlen" — im Bild sofort sichtbar, im Test nicht. `plural()`.
- **`python -m ruff check .`** sauber. **`python tools/validate.py`** sauber (nach `git add -N`).

## 4. Die Suiten dieser Runde (DEC-0050, DEC-0060 Regel 2 — abgeleitet aus den geänderten Dateien)

| Suite | Warum sie betroffen ist | Ergebnis |
|---|---|---|
| `tools/test_finance_dashboard.py` | neu | 16 passed |
| `tools/test_repo_hygiene.py` | liest die Löcherliste und `docs/` | 9 passed |
| `tools/test_hooks.py -k "office or dashboard or kit_owned"` | liest die Office-Vorlagen und die Spiegelregeln | 35 passed |
| `.claude/hooks/test_gates.py -k "hole or measurement or reference"` | die Löcherliste wächst um drei Einträge | 8 passed |
| `tools/test_kitupdate.py`, `tools/test_shortening_net.py`, `tools/test_context_budget.py` | Kit-Inhalt geändert → Ratschen und die Owned-Liste lesen ihn (DEC-0060 Regel 1) | siehe Bericht |

## 5. Eine Entscheidung, die aus dem Kernel folgt und nicht aus Geschmack

Der Ordnerführer heißt **`ABOUT.txt`**, nicht `README.txt`. Grund: `kernel/trays.py` erklärt ein
Verzeichnis zum **Dokumentenfach**, wenn alles, was das Kit darin ausliefert, den Stamm `readme`
trägt — und in einem Fach tritt `guard_no_adhoc` zurück. Gemessen an der laufenden Definition:

```
ausgeliefert:                       ['archive', 'inbox', 'outbox']
mit dem Führer als README.txt:      ['archive', 'dashboards', 'inbox', 'outbox']
```

`dashboards/` ist das Gegenteil eines Fachs: alles darin schreibt ein Befehl dieses Repos. Mit
`README.txt` hätte der Stempler außerdem `team-kits/office-team/hooks/document_trays.txt`
umgeschrieben — eine Datei im `forbidden_scope` dieses Streams. Beide Enden sind ein Test
(`test_the_dashboards_directory_is_not_a_document_tray`), beide einzeln rot gemessen.

## 6. Seam-Items, wörtlich

### 6.1 Stream K — `team-kits/repo_kit_owned.txt`

Eine Zeile, ans Ende der Liste:

```
tools/finance_dashboard.py
```

…und in den Kopf der Datei, als eigener Absatz (die Datei verlangt zu jedem Eintrag den Grund):

```
# tools/finance_dashboard.py is owned for the FIRST reason, one hook further on: gate_ledger_valid
# starts it after every ledger change, and a hook that runs a project's forked copy runs code the
# kit cannot fix. It is also the one command that turns the books into the picture a non-developer
# reads, so a fork of it is a second answer about the same money -- the einvoice_extract reason,
# one step later in the same pipeline.
```

**Wenn diese Zeile ohne 6.2 landet**, ist die einzige Folge, dass das Kit die Datei bei jedem
Scaffold überschreibt statt sie copy-if-absent zu lassen — kein Fehler, aber auch kein Gewinn.
Beide Zeilen gehören in **einen** Merge-Schritt.

### 6.2 Stream G — `team-kits/office-team/hooks/gate_ledger_valid.py`

In `handle_post_tool_use`, **nach** der Schleife `for absolute in changed:` und **vor**
`if not verdicts:` — also auch dann, wenn der Ledger ungültig ist (die Seite IST der Bericht über
diesen Zustand und trägt den Befund im Banner):

```python
    # The dashboard is rendered where the ledger CHANGES, because this is the one place both of
    # its writers pass (`scripts/ledger_add.py` and the allowed hand edit). It runs even when the
    # ledger is invalid: the page carries the validator's findings in its banner, so refusing to
    # render would take away the view somebody looks for the broken row in.
    # FAIL-SOFT: this is comfort, not enforcement -- a failed render is one line on stderr and
    # never a refusal.
    dashboard = os.path.join(root, "tools", "finance_dashboard.py")
    if os.path.isfile(dashboard):
        try:
            subprocess.run([sys.executable, "-B", dashboard], cwd=root, capture_output=True,
                           text=True, timeout=60)
        except Exception as problem:      # noqa: BLE001 -- comfort must not become a refusal
            sys.stderr.write("[%s] dashboard not regenerated: %s\n" % (HOOK, problem))
```

(`subprocess` ist in dieser Datei noch nicht importiert; `sys` und `os` schon.)

**Was zu diesem Schritt gehört und ihn erst wahr macht:**
- ein rot-zuerst gemessener Test: buchen → Seitenbytes bewegen sich; die Kette ohne die
  Verdrahtung steht als H117 mit Zahlen im Messprotokoll;
- die Frist des Hooks: der Lauf über 318 Zeilen dauert unter einer Sekunde, ist aber unter dem
  Budget des Hooks zu messen, nicht anzunehmen;
- **im selben Schritt** der Absatz „IT DOES NOT REBUILD ITSELF YET" in
  `templates/repo/dashboards/ABOUT.txt` — er wird dann falsch. Bis dahin darf kein Text
  „automatisch" behaupten.

### 6.3 unowned — `team-kits/office-team/templates/repo/.gitignore`

Ans Ende des Blocks „regenerated state artifacts":

```
# the generated finance dashboard: rebuilt from the ledger by `python tools/finance_dashboard.py`,
# so a committed copy is an always-stale second answer plus a merge conflict on every branch (the
# reason project_memory/generated/ is ignored above). The folder guide stays tracked -- `dir/*`
# plus negation, never `dir/`, for the reason the inbox/archive/outbox rules give.
dashboards/*
!dashboards/ABOUT.txt
```

### 6.4 Stream G — `team-kits/office-team/templates/project_memory/business_profile.yaml`

Unter `tax:`, hinter `fiscal_year`:

```yaml
  # Zahlungsziel in Tagen: ab wann eine unbezahlte Forderung im Finanz-Dashboard als
  # Mahnkandidat erscheint. Leer heißt die gesetzliche Verzugsfrist (§ 286 Abs. 3 BGB, 30 Tage);
  # ein eigener Wert gehört hierher, weil das Ledger kein Fälligkeitsdatum trägt.
  payment_term_days: null
```

Dazu gehört ein Satz im Onboarding-Interview („Nach wie vielen Tagen soll eine offene Rechnung als
mahnfällig gelten?") — sonst füllt das Feld niemand — und im Generator der Wechsel von der
Konstanten zum Profilwert **mit** der Konstanten als Rückfall. Ohne den Interview-Satz ist das Feld
eine Zeile, die für immer `null` bleibt.

### 6.5 Stream E — die Texte

Drei Sätze, je in die Rolle, die den Weg wirklich geht (BUG-0075-Regel: wer ein Dokument besitzt,
trägt den Weg, der es schreibt):

- **bookkeeper:** „Nach einer Buchungssitzung `python tools/finance_dashboard.py` laufen lassen —
  das schreibt `dashboards/finanzen.html` neu: Einnahmen und Ausgaben des Jahres, offene Posten mit
  Mahnkandidaten, die EÜR-Summen je Quartal und die Kleinunternehmergrenze. Die Seite schreibt
  nichts zurück, sie zeigt nur, was im Ledger steht."
- **office-manager:** „Wie das Geschäft steht, steht in `dashboards/finanzen.html`, erzeugt mit
  `python tools/finance_dashboard.py`. Zeigt der Kopf der Seite einen älteren Datenstand als die
  letzte Buchung, ist die Seite alt — dann den Befehl noch einmal laufen lassen."
- **office-developer:** „`tools/finance_dashboard.py` und `tools/finance_dashboard.template.html`
  SIND die Finanzseite; `dashboards/finanzen.html` ist ihr Ergebnis und wird bei jedem Lauf
  überschrieben. Zahlen ändert man im Ledger, die Darstellung in diesen beiden Dateien — eine
  Handänderung an der erzeugten Datei ist beim nächsten Lauf weg."

## 7. Was bewusst nicht geschlossen, aber benannt ist

- **H117** — kein Auslöser: eine Buchung bewegt die Seite nicht. Kette mit Hashes gemessen.
  Begrenzt durch den Datenstand im Kopf und den Befehl im Ordnerführer; zwei Seams (6.1, 6.2).
- **H118** — Alter, Mahnzähler und jeder Stempel entstehen im Browser: dieselbe Datei antwortet mit
  der Uhr auf 2026-09-02 „2 Mahnkandidaten" und auf 2026-07-01 „0". Ohne Skript sagt sie „—" und
  „…" statt einer Null. Begrenzt dadurch, dass die Seite beide Hälften ausspricht; die Frist ist
  Seam 6.4.
- **H119** — keine Herkunft, und `_BLOCKED_SCRIPT_RX` kennt den Generator nicht: er läuft gegen
  einen ungültigen Ledger (rc 0), wo `euer_report` verweigert wird (rc 2), und sagt es im Banner;
  eine von Hand geschriebene Seite ist von einer erzeugten nicht zu unterscheiden. Nach DEC-0056
  kein Härtungsziel.
- **Die Nummernvergabe selbst, offen benannt:** der Auftrag nennt drei Grenzen (Uhr, ohne Skript,
  `_BLOCKED_SCRIPT_RX`) und reserviert drei Nummern, die Bauanleitung §6 nennt drei **andere**
  (kein Auslöser, keine Herkunft, Frist+Uhr). Zusammen sind es vier Sachverhalte. Vergeben ist:
  H117 = kein Auslöser, H118 = Uhr **und** ohne Skript (ein Mechanismus, zwei gemessene Folgen),
  H119 = keine Herkunft **und** `_BLOCKED_SCRIPT_RX` (dieselbe Wurzel: nichts unterscheidet eine
  erzeugte Seite von einer geschriebenen). Die Alternative wäre gewesen, den Auslöser ohne Nummer
  zu lassen — und das ist die Lücke, die der Nutzer als Erstes merkt.
- **Die BuyPlugGo-Vorlage** ist nicht eingetroffen; der Vergleich der Ansichtenliste steht aus.
- **Kein `--root`-Argument im ausgelieferten Text.** Es existiert für die Tests, steht aber in
  keinem Dokument, das ein Nutzer liest: eine Zeile, die `project_memory` als Wurzel nennt, wird
  von `gate_write_scope` verweigert (gemessen als das zweite Ende von
  `test_the_documented_command_passes_the_write_scope_gate`).
- **Die Fixtures sind erfunden** (Seed 2026/2027 aus Phase 1), nicht aus einem Live-Projekt. Sie
  bestehen den Kit-Validator; mehr behaupten sie nicht.
- **Ein kosmetischer Punkt, gesehen und stehen gelassen:** filtert man auf „nur Mahnkandidaten",
  bleibt bei den Verbindlichkeiten der Tabellenkopf ohne Zeilen über „Summe (0 Posten)" stehen.
  Das ist das gewöhnliche Verhalten eines Tabellenfilters und beim Zurücknehmen des Hakens sofort
  weg; eine Änderung daran wäre Gestaltung ohne Befund.

## 8. Übergabe

- `git add -N` für die neuen Dateien ist gelaufen (sonst meldet `validate.py` „hashed into a kit
  VERSION but not git-tracked").
- Patch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0109\stream-dashboard.patch`.
- Vorläufiger Stempel der Bauphase: `office-team 2026.09.02-13`; nach der Nacharbeit
  `2026.09.02-14` (dev und research unverändert `-10`, Kernel unberührt).
- Kein Commit, kein Push, keine Installation.

## Wall-Clock

Beginn 2026-09-02 11:47 (erste Lesung des Designpakets), Ende 13:00 — 1 h 13 min. Davon Lesen und Ableiten
~20 min, Generator + Vorlage + Ordnerführer ~15 min, Tests ~20 min, Rot-zuerst 14 Läufe ~8 min,
Sicht-Schleife und die zwei daraus folgenden Korrekturen ~12 min, Löcher, Messprotokoll und dieses
Blatt ~15 min, Stempel und Suiten der Runde ~15 min (davon ~12 min reine Laufzeit).
Modell: Opus (DEC-0059).

---

# Nacharbeit 1 (2026-09-02, Opus) — 13 Prüferbefunde + der Inhaltswunsch des Nutzers

Eine Runde, zwei Eingaben: der FAIL-Bericht des Prüfers (`_round-scratch/TSK-0109/verify-2/`) und
`user-feedback.md`. Messungen im Detail: `docs/reviews/2026-09-02-tsk0109-measurements.md`,
Abschnitt 8. Die Rigs des Prüfers wurden **gefahren**, nicht nachgebaut.

## N1. Der Nutzerwunsch: Brutto / Netto / USt unter jeder Zahl

Überblick und EÜR-Reiter zeigen unter Einnahmen, Ausgaben und Überschuss je drei Zeilen; beim
Überschuss heißt die dritte **USt-Zahllast** (vereinnahmte USt minus Vorsteuer), die zweite ist das
Nettoergebnis nach USt. Ein Renderer für beide Orte (`split_lines`), die Beträge tragen
`data-figure`-Namen, damit die Tests sie beim Namen fragen statt an der Spaltenposition.

**Was dabei gemessen wurde und den Entwurf geändert hat.** Eine Aufteilung, die nur den Ledgerzeilen
folgt, druckte für die `regular`-Fixture „USt-Zahllast −6.077,56 €" — die Einnahmen sind dort als
`kleinunternehmer` gebucht, die Ausgaben als `standard`. Das ist ein Erstattungsanspruch, den § 19
Abs. 1 UStG ausschließt (kein Vorsteuerabzug). Deshalb entscheidet ein **Steuerzustand** und nicht
die einzelne Zeile — `tax_state()`, drei Fälle ohne Rückfall:

1. Profil sagt nicht `kleinunternehmer: true` → volle Aufteilung aus den Zeilen, Zahllast mit
   Vorzeichenkonvention (negativ = Vorsteuerüberhang = Erstattung), Satz steht auf der Seite.
2. Profil sagt `true` **und** die § 19-Wache sagt „innerhalb" → Brutto = Netto in **beiden**
   Richtungen, USt-Zeile ist die Aussage „keine USt — Kleinunternehmer § 19 UStG", keine Zahllast.
3. Profil sagt `true`, die Wache sagt **nicht** „innerhalb" (Grenze überschritten oder kein Vorjahr)
   → „USt nicht belastbar", mit dem Grund darunter und dem Verweis auf die Steuerberatung.

**Abweichung vom Auftrag, benannt:** der Auftrag ordnet den Alarm-Zustand der Regelbesteuerung zu
(„volle Aufteilung + Zahllast"). Gebaut ist dort Fall 3. Grund: in dieser Fixture sind die
Einnahmen ohne USt gebucht, die Ausgaben mit — die „volle Aufteilung" wäre dort wieder die
Erstattung von 5.932,60 €, und ob für den Zeitraum Umsatzsteuer galt, sagt keine Datei des
Projekts. Die informativen Zahlen des Berichts stehen trotzdem auf der Seite (EÜR-Reiter,
`data-figure="report-vat-out|in|payload"`), mit dem Satz daneben, dass sie nicht die Zahllast sind
— so ist die Parität mit `euer_report.py` sichtbar und die Aussage trotzdem richtig.

**Parität:** der Bericht druckt Brutto **und** USt je Quartal, also wird gegen ihn verglichen; Netto
druckt er nicht, dafür rechnet der Test eine dritte, unabhängige Aggregation aus der CSV
(`csv_quarter`). Acht Quartale, drei Lesarten, gleich.

## N2. Die Befunde, je Befund die Änderung und der rote Test

| Befund | Was geändert wurde | roter Test |
|---|---|---|
| **B1** offene Posten | zwei Lesarten im Generator: `rows` (Stornos aller Dateien) für die eigenen Ansichten, `report_rows` (Stornos je Datei) für den EÜR-Reiter, weil `euer_report.py` genau eine Datei öffnet. Neue Fixture `crossyear` mit der gemessenen Falle. Die Seite sagt, wo die Lesarten auseinanderfallen. Beide Docstrings auf das Gemessene gekürzt | `…agree_on_every_quarter[crossyear]` (zwei Mutationen) |
| **M2** Gründungsjahr | vierter Zustand `previous_unknown`; kein stiller Rückfall auf „within". `business_profile.yaml` trägt kein Gründungsjahr (gelesen) → die Seite **verweigert** die Aussage und nennt beide Fälle und die Steuerberatung | `…threshold…[None-2600000-previous_unknown]` |
| **M3** Balken | dritter Zweig `value is None`: gestrichelter, leerer Balken, „kein Ledger für 2025", „nicht belastbar", kein „über der Grenze" | dieselbe Fallzeile |
| **M4** Shell-Gates | der Test fährt die **registrierten Kommandozeilen** (Starter `_gate.py` mit seiner ganzen Liste), nicht das letzte Wort je Eintrag; die Einzelentscheidung bleibt nur als Zuordnung | `…passes_the_write_scope_gate` mit einem verweigernden `gate_filing`; Gegenmessung: alte Lesart rc 0, neue rc 2 |
| **M5** Datenstand | `ABOUT.txt` und die H117-Begrenzung sagen jetzt, was gemessen ist: der Kopf bewegt sich nur, wenn die neue Buchung jünger ist als alles Bisherige; ein Nachtrag lässt ihn byte-identisch | keiner (Textänderung; die Messung ist `stale.py`, Abschnitt 8.5) |
| **M6** Währungslücke | der Filtertest liest `[data-sum]` **aus der geschriebenen Datei** (die Schreibweise des Generators) und nach dem Filter aus dem Browser (die des Skripts); der Kommentar sagt genau das | `test_filters_narrow_rows_and_the_sum_follows` |
| **N7** Zählungen | die drei falschen Kopfzahlen im Messprotokoll ersetzt; die Zählungen dieser Runde stehen gemessen in Abschnitt 8 | — |
| **N8** Streudatei | nicht passende Dateien in `ledger/` werden nicht mehr still übersprungen: eigener Hinweiskasten und Zeile in der Quellenliste, im Wortlaut von `ledger_add.validate_file`. Der Ledger bleibt „gültig" — die Summen kommen aus den Jahresdateien | `…a_file_in_ledger_that_no_report_reads…` |
| **N9** PyYAML | erklärende Verweigerung in der Form der Nachbarverweigerung, rc 1 (Abweichung zum verlangten rc 2 in Abschnitt 8.6 begründet) | `…a_missing_pyyaml_is_a_sentence…` |
| **N10** Spiegelregel | `test_hooks.py` leitet die Verzeichnisse jetzt ab: **jedes** Verzeichnis unter `templates/repo/`, in das ein Kit `*.py` ausliefert. Damit ist `templates/repo/tools/` gedeckt, ohne dass jemand es einträgt | `test_shared_kit_files_identical` mit einer abweichenden Kopie in einem zweiten Kit |
| **N11** Hole-Zitate | **nicht geschlossen**, liegt in `.claude/` (forbidden). Siehe „Reste" | — |
| **N12** H119-Zeile | die Tabellenzeile nennt jetzt beide Sachverhalte (kein `_BLOCKED_SCRIPT_RX`-Eintrag **und** kein `render.json`-Gegenstück) mit je ihrer Begrenzung | — |
| **N13** Validator-Satz | der englische Satz wird mit „Meldung des Prüfers:" eingeleitet — im Alarmbanner und im neuen Hinweiskasten. Die Übersetzung selbst bleibt Naht (sie gehört `scripts/ledger_add.py`) | — |

Dazu ein Befund aus der **eigenen Sichtung**: „1 Mahnkandidaten". Beide Schreibweisen kommen jetzt
aus dem Generator (`data-one`/`data-many`), das Seitenskript wählt nur — roter Test
`…dunning_candidates…[crossyear]`.

## N3. Neue Dateien dieser Runde

| Datei | Was |
|---|---|
| `tools/fixtures/finance/crossyear/` | Regelbesteuerung, Jahresgrenzen-Storno, zweite offene Zeile, OSS-Beleg, Gutschrift — beide Ledgerdateien `--validate`-gültig |
| `tools/fixtures/finance/founding/` | ein Ledgerjahr, 26.000 €, `kleinunternehmer: true` — der § 19-Fall ohne Vorjahr |

## N4. Nähte dieser Runde, wörtlich (nicht geschrieben)

### N4.1 Stream G — `templates/project_memory/business_profile.yaml`

Unter `tax:`, hinter `fiscal_year` (zusätzlich zu `payment_term_days` aus Abschnitt 6.4):

```yaml
  # Gründungsjahr des Betriebs (JJJJ). Ohne dieses Feld kann die § 19-Wache im Finanz-Dashboard
  # den Fall "kein Vorjahr im Ledger" nicht entscheiden: seit 2025 gilt für ein Gründungsjahr die
  # Grenze von 25.000 EUR für das LAUFENDE Jahr, sofort wirksam — ein fehlendes Vorjahr kann aber
  # auch nur eine fehlende Datei sein. Leer heißt: die Seite verweigert die Aussage.
  founding_year: null
```

Dazu der Onboarding-Satz — sonst füllt das Feld niemand: **„In welchem Jahr hast du das Geschäft
angemeldet?"** Und im Generator der Wechsel von der Verweigerung zur Rechnung: ist
`founding_year` gleich dem laufenden Jahr, gilt `KLEINUNTERNEHMER_LIMIT_PREVIOUS_YEAR` als Grenze
des laufenden Jahres, und eine Überschreitung heißt „ab dem überschreitenden Umsatz pflichtig".

### N4.2 Stream scripts — die zwei Sätze, die `scripts/` gehören

1. **Übersetzung des Validator-Satzes.** `ledger_add.validate_row` schreibt englische Befunde
   („re-read the document; a value you cannot read is UNCLEAR, never guessed"); sie stehen im
   Alarmbanner der Seite vor einem deutschsprachigen Nutzer. Die Übersetzung gehört in die Datei,
   die den Satz besitzt — nicht in eine zweite Fassung im Dashboard. Bis dahin leitet die Seite ihn
   mit „Meldung des Prüfers:" ein.
2. **Die Zählweise der offenen Posten in `euer_report.py`** (BUG-Vorschlag, nicht in diesem Strom
   entschieden): der Bericht zählt eine offene Rechnung als offen, obwohl ein Storno in der Datei
   des Folgejahres sie aufhebt — er liest nur `ledger/<Jahr>.csv`, während `validate_cross` den
   Jahresgrenzen-Storno ausdrücklich zulässt. Gemessen: 2025 Q4, Bericht 2 offene Posten, die
   ledgerweite Lesart 1. Solange der Bericht die Autorität ist, folgt ihm die Seite und benennt
   den Unterschied; ist die Zählung des Berichts falsch, ist das ein `BUG`-Item an `scripts/`.

### N4.3 Stream E — ein Satz mehr für die Rollen

Zusätzlich zu den drei Sätzen in Abschnitt 6.5, für **bookkeeper** und **office-manager**:

> „Die Seite zeigt Einnahmen, Ausgaben und Überschuss je dreifach: Brutto, Netto und USt. Steht
> bei einem Kleinunternehmen dort keine Zahl, sondern ein Satz, ist das kein Fehler — nach § 19
> UStG wird keine Umsatzsteuer ausgewiesen und keine Vorsteuer abgezogen."

## N5. Reste für die Merge-Runde (keine neuen Hole-Nummern in diesem Strom)

- **Hole-Zitate in `.claude/hooks/test_gates.py`** (Prüferbefund N11): der Leser löst Testnamen nur
  ohne Punkt und nur gegen `test_gates.py` auf, also ist ein Zitat auf
  `test_finance_dashboard.py::…` ungedeckt — genau die Form, die die neuen Hole-Einträge nennen.
  **Korrektur der Nacharbeit 2 an diesem Absatz:** hier stand, die Datei sei „jedem
  Sitzungsteilnehmer verschlossen". Das ist falsch und war eine Behauptung über den
  Durchsetzungsapparat, die niemand gemessen hat. Richtig: Gate 1 verweigert `.claude/` dem
  **Sitzungsagenten**, nicht jedem; H80 verweigert **jedem** eine Shell-Zeile, die eine
  Haken-Datei benennt, während `Edit`/`Write` dieselbe Datei einem **Subagenten** offenhalten
  (CLAUDE.md, Absatz zu H80). Der Rest gehört also in die Merge-Runde und ist dort von einem
  Umsetzer mit `Edit` zu schließen — außerhalb dieses Items, weil `.claude/**` in seinem
  `forbidden_scope` steht.
- **Waagerechter Überlauf des EÜR-Reiters bei 390 px** (456 px statt 390): nicht neu, gemessen vor
  und nach dieser Runde derselbe Wert, breitester Knoten `table.ledger.cats`. Gestaltungsarbeit,
  kein Befund dieser Runde.
- **Der Balken „laufendes Jahr" im Zustand `previous_unknown`** war gegen 100.000 € gezeichnet,
  während im Gründungsfall 25.000 € gälten — **in der Nacharbeit 2 geschlossen** (Befund M3): der
  Balken steht dort jetzt im selben `unknown`-Zustand wie der Vorjahresbalken, ohne Prozent und
  ohne Rest, und nennt beide Grenzen. Kein Rest mehr.

## N6. Übergabe der Nacharbeit

- Patch neu: `_round-scratch/TSK-0109/stream-dashboard.patch` (+ `git-status.txt`).
- Sicht-Schleife neu: `review-build/` ersetzt, 98 Bilder, `render.json` mit neuen Hashes.
- Stempel: `python tools/bump_kit_version.py` -> `office-team 2026.09.02-14` (vorläufig).
- Kein Commit, kein Push, keine Installation.

---

# Nacharbeit 2 (2026-09-02, Opus) — 10 Prüferbefunde, davon 2 blockierende AM FIX der Runde davor

Zweiter Prüfbericht (`_round-scratch/TSK-0109/verify-3/`), FAIL: B 2, M 3, N 5. Beide B-Befunde
entstanden an der Nacharbeit 1 — der Steuerzustand schloss **eine Schreibweise** statt der Klasse,
und die informativen Berichtszahlen wurden zum **zweiten Druckort** derselben unmöglichen Zahl.
Messungen: `docs/reviews/2026-09-02-tsk0109-measurements.md`, Abschnitt 9. Die Rigs des Prüfers
wurden gefahren, nicht nachgebaut (`l_spellings.py`, `m_quoted.py`, `n9_mut.py`, `n10_mut.py`,
`h_founding.py`, `i_gauge.py`, `pristine.py`).

**Unterbrechung, protokolliert:** dieser Lauf wurde gegen 16:35 vom Sitzungslimit abgebrochen,
mitten in Befund B2. Vorgefunden um 17:16: B1 vollständig im Baum (Dreizustand, beide
Anschlussstellen, Rechtsgrundlage), B2 zur Hälfte (Etikett und Druckstelle geändert, Tests noch
nicht) — die Suite stand an dieser Stelle auf **1 failed, 22 passed**, und zwar genau am
Paritätstest, der die alte dritte Zahl noch erwartete. Ab dort fortgesetzt, nichts doppelt
geschrieben.

## N2.1 Die zwei blockierenden Befunde

**B1 — eine Aufzählung mit einem Wert.** `if kleinunternehmer is not True: applies = True` liest
jede Schreibweise außer `true` als Regelbesteuerung. Gemessen mit `l_spellings.py` gegen die
Fixture `regular` (Ausgaben mit 19 %):

```
true (baseline)        USt-Zahllast(2026) = keine USt — Kleinunternehmer § 19 UStG
yes                    USt-Zahllast(2026) = keine USt — Kleinunternehmer § 19 UStG
quoted "true"          USt-Zahllast(2026) = −6.077,56 €
Ja                     USt-Zahllast(2026) = −6.077,56 €
missing tax: block     USt-Zahllast(2026) = −6.077,56 €
```

Die Kette beginnt im **Auslieferungszustand**: die Profilvorlage des Kits trägt
`kleinunternehmer: null`. Gebaut ist jetzt die Definition statt der Aufzählung — `True` → § 19,
`False` → Regelbesteuerung, **alles andere → unbekannt**, und unbekannt wird behandelt wie der
nicht entscheidbare Fall der Schwellenwache: keine USt-Summe, keine Zahllast, ein Satz, der das
Feld und **beide** Werte nennt, die es beantworten. Der Satz steht auf **jedem Reiter, der
Kennzahlen zeigt** (im Test abgeleitet, nicht aufgezählt) und zusätzlich in der Liste „Jetzt
ansteht" — dort hing die Milderung vorher an `is None` und erschien bei `"true"` nirgends
(`m_quoted.py`).

**B2 — der zweite Druckort.** Der EÜR-Reiter druckte „Zahllast: −6.077,56 €" vier Zeilen unter dem
Satz „es gibt keine Zahllast". Und der Satz „Diese drei Zahlen stehen so auch im EÜR-Bericht" war
falsch: `euer_report.py` druckt **zwei** Zahlen und nie eine Zahllast (`grep -c Zahllast` auf einem
erzeugten Bericht: 0). Gebaut: wo `tax["applies"]` falsch ist, wird die Differenz **gar nicht**
gedruckt — auch das Etikett „USt-Zahllast" fällt weg, denn ein Etikett trägt dieselbe Behauptung
wie eine Zahl. Wo Regelbesteuerung gilt, steht sie oben und unten unter demselben Namen.

## N2.2 Die übrigen acht

| Befund | Was geändert wurde | roter Test |
|---|---|---|
| **M1** | der PyYAML-Test pinnte die Gleichheit zweier rc, nicht die Verweigerung: jetzt `!= 0` für beide, dazu „es wurde keine Seite geschrieben" | `…a_missing_pyyaml…` bei `SystemExit(1)` → `(0)` |
| **M2** | die Testauswahl der Runde nannte nicht den einen Test, den diese Arbeit in `test_hooks.py` ändert; `or shared_kit` ergänzt und der Lauf wiederholt | — (Auswahlfehler, keine Codeänderung) |
| **M3** | der Balken „laufendes Jahr" steht im Zustand `previous_unknown` im selben `unknown`-Zustand wie der Vorjahresbalken: gestrichelt, leer, ohne Prozent und Rest, Fußzeile nennt **beide** Grenzen; der Überblickssatz ebenso. Der Urteilssatz, der den Balken vorher als „an der falschen Grenze gemessen" beschrieb, ist mitgezogen | `…threshold…[previous_unknown]`, zwei Mutationen |
| **N1** | `plural()` an allen vier Stellen: Kopfzeile, Quellenzeile unter jeder Kennzahl, Rechnungsliste (dort schreibt das Skript die Zahl, also reisen beide Schreibweisen als `data-one`/`data-many` mit) | `…every_count_on_the_page_reads_right_at_one`, drei Mutationen |
| **N2** | Rechtsgrundlage berichtigt: § 19 Abs. 1 UStG stellt die Umsätze **steuerfrei**, der Vorsteuerausschluss folgt aus **§ 15 Abs. 2 Satz 1 Nr. 1 UStG** (§ 15 Abs. 3 nimmt § 19 ausdrücklich aus). Nachgelesen auf gesetze-im-internet.de am 2026-09-02 | — (Textänderung, Beleg in Abschnitt 9.5) |
| **N3** | `crossyear`-Fixture: `legal_form` von `GmbH` auf `Einzelunternehmen` — eine GmbH bilanziert (§ 238 HGB, § 5 EStG) und macht keine EÜR; FR-0076 schließt sie aus. Zahlen unverändert | — (Fixture; die Parität lief unverändert durch) |
| **N4** | Messdokument beschrieb eine Fassung, die es nicht gab; an B2 angeglichen | — |
| **N5** | `_shipped_code_dirs` war an `.py` verankert, verglichen wird `.py` **und** `.html`: ein Verzeichnis, das nur eine Vorlage ausliefert, war von der Ableitung nicht erfasst | `test_shared_kit_files_identical`, **beide Enden** gemessen |

## N2.3 Nähte, wörtlich (nicht geschrieben)

### N2.3.1 Stream G — die Auslieferungszeile, die die B1-Kette beginnt

`templates/project_memory/business_profile.yaml` liefert `kleinunternehmer: null` aus. Das ist
nach dem Fix kein falscher Betrag mehr (die Seite verweigert die Aussage und sagt, was zu tun
ist), aber es heißt, dass **jedes frisch installierte Projekt** im Zustand „unbekannt" startet,
bis das Onboarding-Interview die Frage stellt. Der Satz gehört ins Interview, nicht in den
Generator:

> „Bist du Kleinunternehmer nach § 19 UStG — weist du also keine Umsatzsteuer aus? (ja/nein)"

Und im Template daneben der Hinweis, dass nur `true` und `false` Antworten sind:

```yaml
  # true/false (§ 19 UStG) — NUR diese beiden Werte sind eine Antwort. Alles andere (leer, "true"
  # in Anführungszeichen, Ja) liest das Finanz-Dashboard als "nicht beantwortet" und zeigt dann
  # weder USt-Summen noch eine Zahllast, weil beide ohne diese Antwort geraten wären.
  kleinunternehmer: null
```

### N2.3.2 Stream G — die Rechtsform, die niemand prüft

`business_profile.yaml` nennt im Kommentar `GmbH` als Beispielwert, und nichts im Kit prüft, ob die
Rechtsform zur EÜR passt (FR-0076 schließt bilanzierende Rechtsformen aus). Der Prüfer hat die
Naht dem G-Umsetzer geschickt; hier steht sie als Nachweis, dass sie benannt ist.

### N2.3.3 Merge-Runde — die Kollision zwischen Strom I und Strom K in `tools/test_hooks.py`

Beide Ströme ändern **denselben Docstring** von `test_shared_kit_files_identical` (`@@ -2821`) und
denselben Bereich darunter. Vorschlag zur Auflösung, in dieser Reihenfolge:

1. **Beide Absätze überleben** — sie sagen Verschiedenes: K's Absatz begründet, warum ein Eintrag
   kit-eigen ist, I's Absatz begründet, warum die **Verzeichnisse** abgeleitet statt aufgezählt
   sind. I's Absatz kommt zuletzt, weil er die Codeänderung direkt darunter erklärt.
2. **K's Zitat wird umgeschrieben.** K zitiert `_assert_mirrored("templates/repo/scripts", …)` —
   diese Zeile existiert nach der Schleife nicht mehr. Die Fassung, die dann stimmt: `_assert_mirrored`
   läuft über jedes Verzeichnis, das `_shipped_code_dirs()` liefert, also auch über
   `templates/repo/scripts`; wer den Aufruf sucht, findet ihn in der Schleife.
3. **Die zwei ersetzten Zeilen bleiben ersetzt** (Strom I), K's Ergänzungen an
   `KIT_SPECIFIC_SCRIPTS` gelten unverändert weiter — die Ausnahmeliste wird von der Schleife für
   jedes Verzeichnis benutzt.
4. Dazu die üblichen zwei: `docs/POST_V2_WISHLIST.md:2350` (Tabellenzeilen beider Ströme) und
   `team-kits/office-team/VERSION` (ein Stempel nach dem Merge, nicht zwei).

## N2.4 Reste

Unverändert die aus der Nacharbeit 1, mit **einer Streichung** (der Balken „laufendes Jahr" ist
geschlossen) und **einer Korrektur** (der `.claude/`-Rest ist nicht „für jeden verschlossen");
beide stehen oben in Abschnitt N5.

## N2.5 Übergabe der Nacharbeit 2

- Patch neu: `_round-scratch/TSK-0109/stream-dashboard.patch` (333 KB, 25 Dateien, +4346/−6, keine
  `.audit`-Zeile; `git apply --check --reverse` gegen den Arbeitsbaum sauber).
- Sicht-Schleife neu: `review-build/` ersetzt, 98 Bilder, 0 Konsolen-/Seitenfehler, davon **39
  angesehen** (jeder Reiter jeder Fixture bei 1280, dazu Überblick und EÜR bei 390 dunkel).
- Stempel: `python tools/bump_kit_version.py` → `office-team 2026.09.02-15`.
- Läufe: `test_finance_dashboard` 40 passed, `test_repo_hygiene` 9 passed,
  `test_hooks -k "office or dashboard or kit_owned or mirror or shared_kit"` 37 passed,
  `test_gates -k "hole or measurement or reference"` 8 passed (in einer Kopie), ruff und
  validate sauber. Volle Suite nicht (DEC-0050).
- Kein Commit, kein Push, keine Installation.

---

# Politur (2026-09-02, nach dem PASS) — sechs N-Reste geschlossen

Die sechs Reste aus der Nachprüfung 2, jetzt statt in der Merge-Runde. Messungen:
`docs/reviews/2026-09-02-tsk0109-measurements.md`, Abschnitt 10.

| Rest | Erledigt |
|---|---|
| N1 | Der Satz im Messdokument behauptete, der Generator habe sich auf einen „Satz 4" berufen. Er berief sich auf „§ 19 Abs. 1 UStG" — für den Vorsteuerausschluss die falsche Norm; der „Satz 4" stand im Prüfauftrag. Ersetzt. |
| N2 | Sechste Fixture `unclear` (`kleinunternehmer: "true"`, Ledger von `regular`) in `tools/fixtures/finance/` und in `STATES` des Renderers: der Zustand „unbekannt" hat jetzt ein Bild **mit** Kennzahlen. Beim Ansehen fiel auf, dass derselbe lange Satz zweimal auf dem Überblick stand — die Zeile in „Jetzt ansteht" ist jetzt kurz und verweist nach oben. |
| N3 | Der Plural-Test ist eine Ableitung über **alle** Fixtures: Paare aus den `plural(...)`-Aufrufen (AST), aus den Label-Tupeln und aus `data-one`/`data-many` der Seite; ein Wort nach einer „1" muss ein Singular sein oder im Korpus als unveränderlich belegt. Rot mit der Prüfer-Mutation `mut_n1b` (Beleg/Belege), die vorher grün blieb. |
| N4 | Drei Zahlwörter in Kommentaren gestrichen (`FOUR cases`, `FOUR verdicts, not three`, `the fourth case`); die Fälle stehen benannt statt gezählt — sie waren schon einmal überholt worden. |
| N5 | Backtick `vat_statement` → `vat_line_text`. |
| N6 | Der hängende Satz auf dem Überblick: „… — laufendes Jahr 26.000,00 € von 100.000,00 € oder 25.000,00 €, je nach Gründungsjahr; Vorjahr: keine Ledgerdatei für 2025". |
| Randnotiz | `_as_written` druckte Container als Python-`repr`; jetzt die Schreibweise der Profildatei (String in Anführungszeichen, „eine Liste", „eine Zuordnung"). |

Rot-zuerst: **5 Mutationen, 5 rote Läufe** (P0–P4), Grundlinie **42 passed**.

**Neu im Baum:** `tools/fixtures/finance/unclear/` (Profil, `master_data.yaml`, beide Ledgerdateien
als Kopie von `regular` — die Fixture unterscheidet sich ausschließlich in der Profilantwort).

## Übergabe der Politur

- Stempel: `office-team 2026.09.02-16`.
- Sicht-Schleife: **119 Bilder** aus sechs Zuständen, 0 Konsolen-/Seitenfehler; angesehen die vier
  `unclear`-Bilder (Überblick und EÜR, 1280 und 390 dunkel) und der geänderte Überblick von
  `founding`.
- Läufe: `test_finance_dashboard` **42 passed**, ruff und `validate.py` sauber.
- Patch neu + `git-status.txt`, keine `.audit`-Zeile. Kein Commit, kein Push.
