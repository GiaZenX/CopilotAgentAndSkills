# TSK-0123 — Prüfbericht Runde 3 (harness-verifier): nur N1, N2 und der Nit

| | |
|---|---|
| Umfang | ausschließlich die zwei Reste und der Nit aus Runde 2; alles andere steht aus Runde 2 auf PASS |
| Gemessen in | **frische** Kopie `_round-scratch/TSK-0123/verify/tree` (ohne `.git`), Referenz `verify/head` (`git archive 75a00d1` + Patch, `-c core.autocrlf=false`), Rigs `rig_r2.py`, `rig_r2b.py`, `rig_r3.py`, `probe_words3.py`, `eolcheck2.py` — ein Fall pro Aufruf, binäres I/O, Verweigerung außerhalb des eigenen Verzeichnisses |
| Basislauf | `tools/test_review_procedure.py` **18 passed** (vor und nach allen Mutationen) |
| **N1** | **PASS** |
| **N2** | **PASS**, mit einem **neuen kleinen Rest** (N3, nicht blockierend) |
| **Nit** | **PASS** |
| **Abschlussurteil** | **PASS** — auslieferbar; N3 gehört als benannter Rest ins Protokoll (ein Satz) oder wird mit drei Zeilen Code geschlossen |

---

## N1 — Positions-Leser: **PASS**

`tools/test_review_procedure.py:518-547` läuft jetzt über **jede** Zeile, die die Überschrift nennt
(`for named, line in enumerate(lines)` statt `next(...)`), und der Docstring benennt die verbliebene
Hälfte selbst.

| meine Mutation (Runde 2) | rc jetzt | |
|---|---|---|
| saubere Zeigerzeile bleibt, eine **zweite, fett eingeleitete** Nennung wird weiter unten in den Satz „…is empty today. Wishes whose file lists / overlap are merged…" gesetzt | **1** | `FAILED …::test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix` (Runde 2: rc 0) |
| Zeigerzeile zurück an die Runde-1-Stelle (Befund B1) | **1** | dito |
| derselbe Zerriss **ohne Fettung** | 0 | erwartete, jetzt benannte Grenze |

Die Grenze steht an beiden Orten, die sie tragen müssen: im Docstring von `_torn_sentence_above`
(„WHAT IT STILL CANNOT SEE … an insertion that is NOT bold-led") und im Protokoll §6 (7), das
zusätzlich sagt, welche Hälfte von N1 zu ist. Beides gegen die Datei geprüft, nicht gegen die
Meldung.

## N2 — Ehrlichkeits-Vokabular: **PASS**, mit einem neuen Rest

`tools/test_review_procedure.py:170-197` liest die Haken-Namen jetzt aus `settings/settings.json`
statt aus dem Verzeichnis.

| Fall | rc | |
|---|---|---|
| Streudatei `team-kits/dev-team/hooks/reading.py`, nirgends registriert | **0**, 18 passed | Runde 2: 2 failed — Falschalarm ist weg |
| Fall 30: „gate_dispatch refuses an order that skipped either reading." in allen drei Lead-SKILLs | **1** | `FAILED …::test_the_order_reading_claims_no_enforcement_it_does_not_have` — R1 bleibt zu |
| dieselbe Überbehauptung **in Backticks** | **1** | dito |
| ein REGISTRIERTER Haken, dessen Datei fehlt (`gate_dispatch.py` gelöscht, Registrierung bleibt) | **0**, 18 passed | der Leser sieht das Dateisystem nicht an: kein Absturz, kein Signal, das Wort bleibt im Vokabular. Für diese Modulgrenze harmlos; wer eine tote Registrierung finden will, findet sie hier nicht |

**Zahlen des Umsetzers nachgerechnet** (`probe_words3.py`): Vokabular je Kit dev 27 / office 26 /
research 24 Wörter, davon 5 Basiswörter (`gate`, `guard`, `hook`, `notify`, `permission`) — also
**22 / 21 / 19 hinzugefügte Haken-Namen**, genau die gemeldeten Zahlen. Nicht registrierte
Helferdateien draußen: 11 / 16 / 11 (`_audit`, `_compat`, `_root`, `_stdlib_guard` …).

### N3 (neu, nicht blockierend) — `tools/test_review_procedure.py:191`: gelesen wird nur das LETZTE Wort einer verketteten Registrierung

`base = os.path.basename(entry["command"].split()[-1].strip('"'))` nimmt aus einer Kommandozeile
genau ein Wort. Die Kits registrieren ihre Haken aber teilweise **verkettet** über `_gate.py`, und
dann fällt alles außer dem letzten Glied heraus. Gemessen, je Kit die registrierten Namen, die das
Vokabular NICHT enthält:

```
dev-team:      ['_gate', 'gate_subagent_output', 'guard_agent_spawn']
office-team:   ['_gate', 'gate_filing', 'gate_proc_approved', 'gate_subagent_output',
                'guard_agent_spawn', 'record_filing_reading']
research-team: ['_gate', 'gate_subagent_output', 'guard_agent_spawn']
```

Und das ist wirksam, nicht nur theoretisch — dieselbe Überbehauptung wie Fall 30, nur mit einem
verketteten Namen:

```
CASE n2_attack_overclaim_with_a_CHAINED_registered_hook_name -> rc 0
18 passed in 7.07s
   ("guard_agent_spawn refuses an order that skipped either reading.", in allen drei Lead-SKILLs)
```

Damit sagt der Docstring mehr, als der Code liest: „the names of the hooks it **REGISTERS**" — es
sind die zuletzt genannten je Registrierung. Das ist dieselbe Klasse wie R1, nur enger geworden.
**Schwere:** Rest, nicht blockierend (die gebräuchliche Schreibweise ist gedeckt, die Richtung ist
fail-open nur für 3–6 Namen je Kit). **Minimalfix, drei Zeilen:** über ALLE Wörter der Kommandozeile
laufen, die auf `.py` enden, statt über das letzte — sonst ein Satz in §6 (5) und im Docstring, der
die Verengung benennt.

## Nit — Journalzeilen: **PASS**

`git apply --numstat` gegen den unberührten `75a00d1`-Baum: `21  1  docs/reviews/phase0-disposition.md`.
Aufschlüsselung im Patch nachgezählt: 17 Journal-Einträge hinzugefügt, davon 1 nur verschoben (eine
Entfernung derselben Zeile), plus 4 Leerzeilen → **16 neue** = 13 Pin-Zeilen + 3 Größenzeilen.
Protokoll §3 sagt genau das, samt der Erklärung für die Differenz zu 21. Stimmt.

## Weiter mitgemessen (unverändert in Ordnung)

* **Patch**: 20 Köpfe, 126 305 B, **0 CR**, keine `VERSION`-Hunks; `git -c core.autocrlf=false apply`
  auf `75a00d1` **rc 0**, Ergebnis byte-gleich zum Arbeitsbaum bis auf die drei `VERSION`-Dateien.
* **Stempel**: `bump_kit_version.py --check` → alle drei „unchanged (2026.09.05-2)"; die
  Abschlusszeile hat wirklich nur `tools/` berührt.
* **Zeilenenden**: 23 berührte Dateien, 0 CR-Bytes.
* **Suiten** (eine nach der anderen): `test_review_procedure` 18 passed, `test_role_contracts`
  30 passed, `ruff` clean, `validate.py` clean. Volle Suite und die übrigen Suiten weiterhin
  **nicht** gefahren (gehören zum Merge, `DEC-0050`).
* Nach allen Mutationen ist meine Kopie wieder deckungsgleich mit `head` (außer den drei Stempeln) —
  nichts blieb stehen.

---

## Abschlussurteil

**PASS.** Beide Reste sind an der Wurzel behandelt: der Positions-Leser urteilt über jede Nennung
statt über die erste, und seine verbliebene Hälfte (unfetter Einschub) steht jetzt dort, wo eine
Grenze hingehört — im Docstring des Lesers und im Protokoll. Das Ehrlichkeits-Vokabular kommt aus der
Registrierung statt aus dem Verzeichnis; die Streudatei ist grün, Fall 30 in beiden Schreibweisen rot.
Der Nit ist mit `numstat` belegt. Offen bleibt genau eine Kleinigkeit, die ich in dieser Runde neu
gemessen habe (N3): verkettete Registrierungen liefern nur ihr letztes Glied ins Vokabular, sodass
eine Überbehauptung mit `guard_agent_spawn` durchgeht — nicht blockierend, aber entweder mit drei
Zeilen zu schließen oder mit einem Satz zu benennen, damit die nächste Runde sie nicht als Fund
wiederfindet.
