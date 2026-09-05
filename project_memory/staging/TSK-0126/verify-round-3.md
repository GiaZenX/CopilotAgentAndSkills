# TSK-0126 — Merge-Prüfung Runde 3 (harness-verifier), Nacharbeit 2

Gemessen am Arbeitsbaum `C:/Offline Repos/AgentAndSkills` (read-only) in einer FRISCHEN `.git`-losen
Kopie `verify/merged3` und an drei FRISCH gescaffoldeten Piloten `verify/pilots3/{dev,office,research}`
(Kit-Store als Kopie unter `verify/home3/.claude/team-kits`; der globale Store wurde nicht angefasst).
Rig unter `verify/rig/` (`_rig3.refuse_outside_rig()`, ausschliesslich binäres I/O, `DEC-0070`).

**URTEIL: FAIL — mit einem einzigen blockierenden Befund, und der ist zwei Sätze gross.**
Alle vier blockierenden und alle drei mittleren Befunde der Runde 2 sind behoben und von mir
unabhängig nachgemessen; die stärkste Einzelmessung dieser Runde ist, dass ein Rückbau auf den
Runde-2-Leser die Suite rot macht — der Defekt kann nicht still zurückkommen.

---

## Befund, blockierend

### R3-B1 — `DEC-0079` (4) verspricht einen Satz in der Verweigerung, den der Code nicht baut; im fail-closed Zweig bekommt office/research wieder die alte Sackgasse

`project_memory/decisions/active/DEC-0079.yaml`, `decision` (4): *„Where the kit store is not
reachable at dispatch time, the derivation fails CLOSED (asked), **stated in the remedy**."*

Gemessen (`verify/rig/r3_msg.py`, echter Kernel an gescaffoldeten office-Piloten, VOLLER Text):

```
[record names a kit the store does not hold] REFUSED, full text:
    TSK-0001 hangs from PROC-0001 (class 'feature'), and no SR in status ACCEPTED hangs from that
    goal -- the architect step has not happened ... Remedy: have the architect derive the technical
    requirement -- `python scripts/harness.py capture SR` with `derives_from: PROC-0001`, then
    `transition <id> ACCEPTED` -- or ... capture it in a class the duty does not ask (small,
    technical_enabler).

[NO scaffold record]        REFUSED, full text:  <wortgleich>
[kit store not under HOME]  REFUSED, full text:  <wortgleich>
```

Kein Wort über den wirklichen Grund. Ein office-Projekt bekommt dort exakt die Abhilfe, die `H163`
ausgelöst hat — `capture SR` und „the architect", zwei Wörter, die in seinen Texten nicht vorkommen.

**Wie erreichbar das ist**, gemessen statt geschätzt: der Store-Pfad kommt aus
`presets.staging_root()` = `os.path.expanduser("~") + .claude/team-kits` — also aus dem AKTUELLEN
HOME, **nicht** aus dem Scaffold-Datensatz. Mit einem Store, der nicht unter dem laufenden HOME
liegt, ist derselbe office-Pilot REFUSED (`r3_b1.py`, Zeile „office, kit store NOT under the current
HOME"). Das trifft eine zweite Maschine, ein anderes Konto, einen CI-Runner, ein verschobenes
Heimatverzeichnis — nichts Exotisches.

`H163`s Rest benennt die RICHTUNG („wo kein Scaffold-Datensatz das Kit nennt oder das Kit auf
dieser Maschine nicht gestaged ist, … FRAGT"), begrenzt sie aber mit „die Richtung, die eine Frage
kostet statt einen Schritt zu überspringen". Für office und research ist diese Frage in den eigenen
Kit-Texten **nicht beantwortbar** — und genau das ist der Gegenstand des Eintrags.

**Minimalfix, zwei Sätze:** im `except`-Zweig den Grund festhalten und an die Verweigerung anhängen
(„dieser Leser konnte nicht sagen, welches Kit dieses Projekt führt / seinen Kit-Store unter `<Pfad>`
nicht erreichen, darum wird gefragt statt übersprungen"), und `H163`s Begrenzung um den Satz
ergänzen, dass die Frage in einem Kit ohne `SR` keine Antwort in den eigenen Texten hat.

## Klein

### R3-M1 — der Satz für eine Klammergruppe ohne Top-Level-Komma nennt einen von zwei Gründen

`python -m pytest tools/{test_*}.py -q` → rc 2 mit „a brace group with no top-level comma is a
**range**". Gemessen mit der echten Shell und dem argv-Shim: Git Bash lässt dieses Wort **literal**
stehen (`1 positional: tools/{test_*}.py`), es ist kein Bereich; ein Bereich ist `{1..9}`
(`9 positionals`). Beide Male ist die Verweigerung die richtige Richtung und in `H165` benannt —
die Zeile sagt dem Aufrufer nur etwas Falsches über sein eigenes Wort.

### R3-M2 — `radar/decided.md` bleibt inhaltlich geändert und ausserhalb `allowed_scope`

`git diff --numstat HEAD -- radar/decided.md` = **9/0**. Das Protokoll benennt es an zwei Stellen
(Abschnitt 8 und R2-M3) als Änderung des Leads — damit ist es eine Notiz für die Abnahme, kein
offener Befund.

---

## Ergebnis je erwarteter Ausgabe

| # | Ausgabe | Urteil |
|---|---|---|
| 1 | vier Patches in Nahtreihenfolge | **PASS** |
| 2 | zehn Nähte + Schiedsrichter | **PASS** |
| 3 | Löcherliste H151–H165 | **FAIL** (R3-B1: `H163`s Begrenzung understated, `DEC-0079` (4) unerfüllt) |
| 4 | Merge-Befunde behoben oder benannt | **PASS** |
| 5 | EIN Stempel, Läufe, Gate 5 als Prozess | **PASS** |
| 6 | Hostregel | **PASS** |
| 7 | Protokoll mit allen Tabellen | **PASS** (Zeigertabelle 13, Urteil 14, EVD-Zeilen jetzt zustandsrelativ) |

## Ergebnis je Ziel

| Ziel | AC | Urteil |
|---|---|---|
| **PR-0004** | AC-1 Gate 5 | **PASS** — beide Shell-Expansionen geschlossen, zwei Über-Verweigerungen benannt |
| | AC-2 Fristen | **ABWEICHUNG, vom Lead angenommen**, in §14 samt Codex-Seite benannt |
| | AC-3 | in dieser Runde **nicht gemessen** |
| | AC-4 | **PASS** |
| **PR-0005** | AC-1..AC-5 | **PASS**; R3-B1 trifft die Verweigerungs-PROSA und `H163`s Begrenzung, nicht die Regel |
| **PR-0006** | AC-1..AC-4 | **PASS** |
| **PR-0007** | AC-1 CI | **OFFEN** — braucht den Push |
| | AC-2 / AC-3 / AC-4 | **PASS** |

---

## Ausdrückliche Negativbefunde — GEMESSEN

**Die Angriffe der Runde 2, neu gefahren (`verify/rig/r3_b1.py`, frische Piloten):**

```
dev, as shipped                                    -> REFUSED
dev, live system/active DELETED (R2 rest)          -> REFUSED     <- der Rest ist weg
office, as shipped                                 -> GRANTED (not asked)
office, after mkdir system/active                  -> GRANTED (not asked)
office, after a real capture SR (SR-0001 angelegt) -> GRANTED (not asked)   <- R2-B1 geschlossen
research, origin = root / HYP / EXP                -> GRANTED x3
office, record names a kit the store does not hold -> REFUSED (fail closed)
office, NO scaffold record                         -> REFUSED (fail closed)
dev, store copy whose dev TEMPLATE lost system/    -> GRANTED (not asked)
```

Die letzte Zeile ist unter `DEC-0079` **richtig**: entschieden ist die AUSLIEFERUNG des Kits, also
entscheidet die Vorlage im Store — ein Kit, das den Typ verliert, fällt aus der Pflicht, ohne dass
eine Zeile geändert wird. Genau das war die Absicht von Variante (A).

**Der Spawn stimmt mit der Lease überein** (`r3_spawn.py`, Kit-Haken `gate_dispatch.py` als Prozess):
office nach einem echten `capture SR` — `create_lease` GRANTED, **Spawn rc 0**; dev ohne `SR` Lease
REFUSED mit dem Architektenschritt-Satz, mit ACCEPTED `SR` Lease GRANTED und **Spawn rc 0**.

**Die zwei neuen Knoten messen alles, was sie behaupten** (`r3_mut.py`, vier Mutationen, jede
byte-exakt zurückgesetzt):

```
as shipped                              rc 0 | 196 passed
always True (duty everywhere)           rc 1 | 1 failed  -> ..._by_the_kits_delivery_not_the_projects_stock
always False (duty nowhere)             rc 1 | 4 failed  -> beide neuen Knoten + die zwei aus H163
fail OPEN instead of closed             rc 1 | 3 failed  -> ..._a_project_that_names_no_kit_is_asked...
back to the round-2 STOCK reader        rc 1 | 3 failed  -> die Regression wird rot, nicht still
restored                                rc 0 | 196 passed
```

**R2-B4 (Klammern), gegen die echte Shell geprüft** — Gate-Urteil (`r3_brace.py`) neben dem, was
Git Bash dem Läufer wirklich übergibt (`r3_shell.py`, `python`-Shim auf `PATH`, argv in eine DATEI):

| Zeile | Shell übergibt | Gate | richtig? |
|---|---|---|---|
| `tools/{test_*,conftest}.py` | **41** Pfade (ganze Fläche) | **rc 2** | ✓ |
| `{tools,docs}` | `tools docs` | **rc 2** | ✓ (der Zwischenfehler der Nacharbeit ist weg) |
| `tools/{,test_}*.py` | **94** Pfade | **rc 2** | ✓ |
| `{tools/test_*,docs/x}.py` | **41** Pfade | **rc 2** | ✓ |
| `tools/test_{a{b,c},d}.py` | 3 nicht existierende | rc 0 | ✓ Auswahl |
| `tools/test_{board,state}.py` | 2 | rc 0 | ✓ |
| `tools/test_{board.py` (unpaarig) | 1 literal | rc 0 | ✓ |
| `tools/{test_*}.py` | 1 literal | rc 2 | Über-Verweigerung, benannt (Satz: R3-M1) |
| `tools/test_{1..9}.py` | 9 nicht existierende | rc 2 | Über-Verweigerung, benannt |
| `"tools/{…}.py"` / `'…'` quotiert | 1 literal | rc 2 | Über-Verweigerung, benannt (R2-M1) |
| `.claude/hooks/{test_gates,nope}.py` | — | rc 2 | ✓ Datei-Wurzel gedeckt |
| Klammer + `DELIVERY_RUN` | — | rc 0 | ✓ |
| `tools/test_*.py` / `tools/test_re*.py` | 40 / 2 | rc 2 / rc 0 | ✓ unverändert |

**R2-B3 (EVD-Verweis)**: beide Zeilen in Abschnitt 11 sind zustandsrelativ
(`staging/TSK-0126/run-full-suite.txt`, `…/run-gates-suite.txt`), tragen KEINEN Diff-Hash, und die
Flaggen stimmen mit dem laufenden Parser überein (`evidence --help` gelesen: `--kind --result
--related --summary --artifact-ref` Pflicht, `--run-command --run-scope` optional). Beide Dateien
liegen jetzt IM Repo neben dem Protokoll. Die zweite Zeile mit `--result fail` schliesst Gate 3
nicht: das Gate verlangt EIN aktives `pass`, das den Diff-Hash nennt, und ein zweiter `fail`-Satz
nimmt es nicht weg (`.claude/hooks/gate_commit_evidence.py:25/416` gelesen). *Nicht gefahren, wie
verlangt.*

**Migration, unabhängig neu gemessen** (`r3_migrate.py`, frische `project_memory`-Kopie ausserhalb
des Repos): Probelauf **155 written, 0 already in the store, 0 Kollisionen**; Lauf 1 **155 Items /
155 Prosadateien**, Dokument **804 292 → 192 003 B**, sha **`61988c1592b26a1a`**; Lauf 2 **0
written**, sha identisch; **155 Indexzeilen**, `H165`-Zeile und `docs/holes/H165.md` vorhanden,
0 CR.

**Stempel und Reihenfolge**: `2026.09.05-4` ×3, `bump_kit_version.py --check` „unchanged" ×3;
`VERSION` 15:16, Lieferlauf 16:01 — **keine** Datei im `allowed_scope` trägt eine spätere mtime
(einzige spätere Schreibung: `staging/generation-4-streams.md` 16:28, Lead).

**Läufe**: `project_memory/staging/TSK-0126/run-full-suite.txt` **4684 passed / 14 skipped / 0
failed, 44:45**; `run-gates-suite.txt` **7 failed / 541 passed** (die sieben migrierten Richter).
`validate.py` grün.

**Ruff, selbst gemessen**: `python -m ruff check .` in der Kopie → **All checks passed** (rc 0),
ebenso `ruff check project_memory/staging/generation-5/`. Der rc-1-Befund des Umsetzers auf der
Lead-Datei ist **nicht mehr wahr**; der Stand des Leads gilt, und `run-short-commands.md` hält beide
Läufe mit ihrer Ausgabe fest.

**Spiegel**: `hooks/gate_test_scope.py` ×3 `47cb66f39a3c`, `hooks/_kernel.py` ×3 `13e47244d9aa`,
`kit_browser_checks.py` und `parallel-streams/SKILL.md` dev == research. Die Repo-Kopie
(`.claude/hooks/gate_test_scope.py`) ist konstruktionsbedingt eine andere Datei, kein Spiegel.

**Baum**: 82 inhaltlich geänderte Dateien, 52 im Arbeitsbaum berührte ohne Inhaltsänderung, **alle
byte-gleich zu HEAD**; 0 CR ausser `project_memory/.audit/hook_events.jsonl` (611).

**Abschnitt 14** ist vollständig und nennt bei `PR-0005` ausdrücklich `DEC-0074` **und** `DEC-0079`;
die AC-2-Abweichung steht mit der Codex-Messung dabei. **Abschnitt 12b** hält fest, warum
`capture SR` in office erlaubt BLEIBT (kit-neutraler Befehl, EIN Typenvertrag, nach `DEC-0079`
folgenlos — gemessen) — das ist die zweite der beiden Optionen, die `DEC-0079` (2) offenlässt.

## Ausdrücklich NICHT gemessen

* Die volle `tools/`-Suite (`DEC-0050`) — `run-full-suite.txt` gelesen, die Reihenfolge nachgerechnet.
* Ob der Lieferlauf das Präfix wirklich trug (kein Umgebungs-Echo im Log; Gate 5 bindet erst beim
  nächsten Sitzungsstart).
* Die beiden EVD-Zeilen wurden **nicht ausgeführt** (so verlangt).
* `PR-0004` AC-3 (Browser-Checks an einer gebauten App); `PR-0007` AC-1 (gehosteter Lauf, Push);
  die härtere Lastklasse von `H162`.
* Die Klammer-/Glob-Lücke in einem KIT-Projekt: die Kits liefern keine `test_surface`-Erklärung aus.

## Eigene Fehlgriffe

* Mein erster Spawn-Lauf schrieb `acceptance_criteria` als Zeichenketten statt als Datensätze; der
  Haken verweigerte darum mit „criteria that exist nowhere", nicht mit dem Architektenschritt. Mit
  der richtigen Form ist der office-Spawn **rc 0**. Rig-Fehler, kein Befund.
* Aus den Runden 1 und 2 stehen drei eigene Fehlgriffe in den dortigen Berichten; sie bleiben
  eingestanden.

---

## Was blockiert

Nur **R3-B1**, und er ist zwei Sätze gross: eine Klausel an die Verweigerung im fail-closed Zweig,
ein Satz an `H163`s Begrenzung. Alles andere dieser Runde ist gemessen grün.
