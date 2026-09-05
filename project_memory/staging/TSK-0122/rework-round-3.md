# TSK-0122 — Nacharbeit zu Prüfrunde 3, und die (g)-Zeile des Stroms

Prüfrunde 3 fand **kein Loch im Code** mehr; FAIL nur auf Pflicht 6 — zwei Sätze und eine
Deckungslücke. Alle vier Punkte sind geschlossen, jeder mit einer Messung und einem roten Test.

## N1 — die Auflösung geht gegen die WURZEL, nicht gegen den Ursprung

Der Befund ist richtig und mein Satz war falsch. Gemessen (der Prüfer am ausgelieferten Haken, ich
im Kernel nachgestellt) — und die LEASE wird in allen drei Fällen erteilt, verweigert wird am
**Spawn**:

| Ursprung | `acceptance_refs` | Ergebnis |
|---|---|---|
| `BUG` mit `acceptance_criteria: []` | keine | Lease erteilt, Spawn **rc 2** `carries no acceptance_refs` |
| `BUG` mit `acceptance_criteria: []` | `AC-9`, existiert nirgends | Lease erteilt, Spawn **rc 2** `exist nowhere` |
| `BUG` mit `acceptance_criteria: []` | `AC-1`, existiert **an der Wurzel** | Lease erteilt, Spawn **rc 0** |

Der Grund für die dritte Zeile steht jetzt an beiden Stellen: das Universum, gegen das
`validate_dispatch` auflöst, ist `_known_acceptance_ids_locked` — **Wurzel, Ursprung und
genehmigte Amendments zusammen**. Der benannte Rest, den es vorher gab („Ursprung leer UND keine
Referenz"), **existiert nicht** — dieser Fall wird verweigert. Der wirkliche Rest ist: *Ursprung
mit leeren Kriterien, Referenz löst gegen die Wurzel auf* — der Auftrag wird gegen die Kriterien
genau des Ziels gemessen, dessen Architektenschritt fehlt.

Neu geschrieben: `dispatch.architect_step_owed` (Docstring, inklusive der Angabe, dass Lease und
Spawn verschiedene Momente sind) und **H155 zweite Restklasse** mit der Drei-Zeilen-Tabelle.

**Rot ohne den Fix:**
`tools/test_approvals_dispatch.py::test_an_empty_origin_excuses_the_step_while_the_root_criteria_measure_it`
— rc 0 sauber, **rc 1** mit auf den Ursprung verengter Auflösung. Der Test hält alle drei Zeilen
und ist so geschrieben, dass er rot wird, sobald jemand die Zeile schließt; die Meldung sagt dann,
dass H155 der zu korrigierende Eintrag ist.

## N2 — der Test maß die CLI-Stelle nicht

Der Befund trifft genau. Die Zeile prüfte `returncode != 0`, und ohne den CLI-Check war der rc ein
**unbehandelter `KeyError`**, während der Auftrag geschrieben wurde und das Flag still fiel. Ein
Absturz und eine Verweigerung sind nicht dieselbe Antwort, und nur eine lässt den Speicher in Ruhe.

Der Test prüft jetzt **den Verweigerungstext** (`a hole is a BUG`) **und** dass kein `TSK` im
Speicher steht. **Rot ohne den CLI-Check:** rc 0 → **rc 1**.

**Welche Stelle welcher Nachweis reproduziert** (die Präzisierung, die der Befund verlangt):

| Nachweis | mutierte Stelle | Wirkung |
|---|---|---|
| „Ableitung → alte Aufzählung" (`if item_type == "TSK"`) | **Kernel**, `state.assert_capturable_as_hole` | reproduziert R1 dort; der CLI-Aufruf bleibt stehen, aber der Kernel lässt jeden Typ durch → Prozess-Test rot |
| „CLI-Prüfstelle entfernt" | **CLI**, `cli.py` vor der Produzentenwahl | reproduziert die Stelle, die N2 als ungemessen fand → jetzt rot |

Beide sind gemessen; vor dieser Runde deckte nur der erste eine Stelle ab.

## N3 — die Ableitung las den halben Vertrag

`hole_type()` sagte „read off the field contract" und las `OPTIONAL_FIELDS`. Ein zweiter Typ, der
das Feld als **Pflichtfeld** deklariert, kam damit lautlos durch. Jetzt liest sie `_contract_fields()`
— beide Hälften, wie die Schwester-Ableitung `_carries_its_own_criteria`.

**Gemessen mit der Mutation** (`"PROC": (..., "hole_number")` in `REQUIRED_FIELDS`):

```
carriers: ['BUG', 'PROC']
AssertionError: 2 types declare hole_number, so what a hole IS has no single answer: ['BUG', 'PROC'].
```

**Rot ohne den Fix:** `tools/test_state.py::test_only_the_type_a_hole_is_can_be_captured_as_one`,
rc 0 → **rc 1**, und die Meldung ist nachweislich die Ableitung.

**Ein untauglicher Mutationsversuch, protokolliert:** der erste N3-Lauf setzte `HOLE_NUMBER_FIELD`
in `REQUIRED_FIELDS` ein — ein Name, der an dieser Stelle der Datei noch nicht gebunden ist. Der
rote Lauf war ein `NameError` beim Import, nicht die Ableitung; also genau die Klasse, die N2
beanstandet. Mit dem Literal nachgemessen.

## N4 — Nahttabelle

`_over_refusal` steht in **beiden** Ständen unverändert und gehört in keine der drei Listen; die
Zeile sagt das jetzt.

---

## Die (g)-Zeile des Stroms

**Wandzeit.** Gearbeitet: rund **4 h 40** reine Arbeitszeit über vier Anläufe und drei
Nacharbeiten. Spanne: 2026-09-04 06:00 bis 2026-09-05, also gut zwei Kalendertage — die Differenz
ist Ausfall, nicht Arbeit: **vier Host-Abstürze** (Ursache gemessen, G4-4s 16-Kern-Lastrig, nicht
dieser Strom) mit jeweils vollständigem Neuaufsetzen des Kontexts. Reine Rechenzeit der
protokollierten Läufe: rund **1 h 45** (fünf Migrationsläufe Ende zu Ende à 5–12 min, vier
Rot-zuerst-Rigs, acht Suitenläufe).

**Tokens (Umsetzer), je Abschnitt geschätzt aus dem Kontextverbrauch:**

| Abschnitt | Tokens |
|---|---|
| Erstbericht (DEC-Vorlagen, AC-1..AC-5, Migration, erste Suiten) | ~550 k |
| Nacharbeit 1 (F1–F22) | ~110 k |
| Nacharbeit 2 (R1–R7) | ~55 k |
| Abschluss (N1–N4, (g)-Zeile) | ~35 k |
| **zusammen** | **~750 k** |

**Runden.** 1 Erstbericht, 4 Nacharbeiten, **4 Prüfungen**: FAIL / FAIL / FAIL nur auf
Pflicht 6 ohne Code-Loch / **PASS mit einer benannten Nacharbeit** (N3'). Damit ist der Strom
geschlossen; die nächste Lesung ist der Merge-Prüfer über den ganzen Patch.

**N3' (Abschluss, Prüfrunde 4).** Der Schutz in `tools/test_state.py` las selbst noch
`OPTIONAL_FIELDS` — also die Hälfte, VON der `hole_type()` korrigiert worden war. Damit war die
Korrektur von nichts gemessen: mit auf `OPTIONAL_FIELDS` zurückgedrehter Ableitung blieben die
drei Suiten grün (122 passed). Der Schutz liest jetzt `_contract_fields()` und trägt den Fall,
der die beiden Hälften trennt: ein ZWEITER Typ, der das Feld als **Pflichtfeld** deklariert,
muss den lauten Abbruch auslösen. Rot-zuerst gemessen: sauber rc 0 → auf `OPTIONAL_FIELDS`
zurückgedreht **rc 1** → zurückgebaut rc 0, und die Ursache ist nachweislich der
REQUIRED-Fall.

**Rot-zuerst-Messungen: 22**, alle in `.git`-losen Kopien außerhalb des Repos, jede Mutation vor der
nächsten zurückgesetzt — 8 (Erstrunde) + 7 (F1, F2, F3, F4, F6, F18, F19) + 3 (R1 ×2, R2) + 3
(N1, N2, N3) + 1 (N3'). Dazu **zwei protokollierte untaugliche Mutationsversuche** (F2 mit einem
argparse-Präfix, N3 mit einem noch nicht gebundenen Namen), beide erkannt und mit einer gültigen
Mutation wiederholt.

**Nähte übergeben.**

- **G4-3, wörtlich:** die korrigierte SR-Pflicht-Zeile, die Posteingangs-Regel, die
  Loch-als-Item-Sätze und die Lease-/Baum-Zeile — alle vier mit ihren neuen Testnamen, plus die
  **fünf Dateien mit dem toten Zitat** (`test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`
  in drei Verfassungen und zwei `parallel-streams`-Skills). Steht in Protokoll §8.
- **G4-1 / G4-4:** der Block in `.claude/hooks/test_gates.py`, mit dem AST-Vergleich
  (18 entfernt / 10 neu / 5 geändert) und jeder geänderten Definition namentlich. Kein Gate-5-Test
  und kein Timing-Test berührt.
- **Erwartet am Merge:** die Löcher der anderen drei Ströme im heutigen Format
  (`### H<n>` + Zusammenfassungszeile); die Migration übernimmt ihre reservierten Nummern
  (H151–H153, H157–H162) unverändert.

**H154–H156, Endstand:**

| Loch | Klasse | zweite Restklasse |
|---|---|---|
| **H154** | Migrationstür schreibt einen Endzustand ohne Evidenz/Freigabe; vier Bolzen als Begrenzung | ein unlesbares Loch-Item verschwindet lautlos aus allen drei Prüfern (F20) |
| **H155** | `class` ist Freitext, die Pflicht hängt an einer Ausnahmeliste (Über-Verweigerung) | Ursprung mit leeren Kriterien + Referenz, die gegen die WURZEL auflöst (N1) |
| **H156** | die Überlappungsverweigerung sieht nur laufende Leases | `--worktree` prüft nur, dass ein Verzeichnis dort liegt (F19) |

**Merge-Zeilen.**

1. **Der EINE schreibende Migrationslauf**, aus einer Shell **außerhalb** von Claude Code (Gate 1
   verweigert jeden Werkzeug-Schreibzugriff auf `project_memory/`), aus der Repo-Wurzel:
   `PYTHONPATH=team-kits python -B tools/migrate_holes.py --root project_memory --related-pr PR-0003 --apply`
2. **Danach**, sobald die Löcher der anderen Ströme erfasst sind:
   `python -B tools/migrate_holes.py --root project_memory --reindex` — schreibt nur den
   Zeigerindex, braucht kein `--related-pr`, und verweigert einen leeren Index über einem vollen.
3. **Bis Schritt 1 gelaufen ist, sind alle sieben Gate-Knoten rot** — sie lesen einen leeren
   Bestand und sagen es. Gemessen gegen die migrierte Kopie: 7 von 7 grün.
4. **Ungemessen und dem Merge-Prüfer übergeben:** was 178 aktive `BUG`-Items mit Board,
   `session_brief` und den Rollups machen; der Kit-Hash mit dem neuen Verzeichnis `docs/holes/`;
   die Laufzeit von `_iter_every_stored_item` bei jedem `capture` in einem großen Speicher; und ob
   `related_pr: PR-0003` für 143 Löcher die Abnahme dieses Ziels beeinflusst.
5. **Die volle Suite** gehört dem Merge (DEC-0050); dieser Strom hat nur die lesenden gefahren.
