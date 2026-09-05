# TSK-0126 — Merge-Prüfung Runde 4 (harness-verifier), Nacharbeit 3 + Nachtrag

Gemessen am Arbeitsbaum `C:/Offline Repos/AgentAndSkills` (read-only) in einer FRISCHEN `.git`-losen
Kopie `verify/merged4` und an drei FRISCH gescaffoldeten Piloten `verify/pilots4/{dev,office,research}`
(Kit-Store als Kopie unter `verify/home4`; der globale Store wurde nicht angefasst). Rig unter
`verify/rig/` (`_rig4.refuse_outside_rig()`, ausschliesslich binäres I/O, `DEC-0070`).

**URTEIL: PASS.** Kein blockierender Befund. `R3-B1` und `R3-M1` sind behoben und von mir
unabhängig nachgemessen; der Nachtrag (Migration als Kernel-Kommando) ist als Prozess gemessen und
delegiert wirklich an EINE Tür; die Gate-1-Feststellung des Umsetzers ist wahr und ich reproduziere
sie.

---

## Messung je Punkt

### 1. `R3-B1` — die drei fail-closed Fälle, an frischen Piloten — **PASS**

`verify/rig/r4_msg.py`, echter Kernel, voller Text der Verweigerung:

```
[office, store under HOME (control)]                 GRANTED
[record names a kit the store does not hold]         REFUSED
    TSK-0001 hangs from PROC-0001, and whether this project's kit runs an architect step at all
    could not be read: the kit 'ghost-team' this project records is not in the kit store this
    process can reach (…/home4/.claude/team-kits) … The duty is therefore ASKED rather than
    skipped, which is the fail-closed direction of DEC-0079 (4) … Remedy: make the kit's own
    delivery readable again … the kit store is the RUNNING home directory's … Do NOT capture a
    technical requirement to get past this: whether this kit has that item type at all is exactly
    what could not be read.
[NO scaffold record]        REFUSED  -> „this project carries no readable scaffold record
                                       (.claude/team_kit_roles.txt)"
[kit store not under HOME]  REFUSED  -> „the kit 'office-team' … is not in the kit store this
                                       process can reach (…/empty-home/.claude/team-kits)"
```

Jeder der drei Fälle nennt **welchen** er getroffen hat, sagt, dass gefragt wird **weil die
Auslieferung nicht lesbar war**, nennt den Store als den des LAUFENDEN Heimatverzeichnisses, die
passende Abhilfe — und `scripts/harness.py capture` steht in keinem der drei Texte.

**dev behält die gewöhnliche Abhilfe** (`r4_dev_mut.py`): `capture SR` im Text **True**,
„could not be read" **absent**.

**Rot zuerst, einmal, in der Kopie:**
```
as shipped                     rc 0 | 3 passed
fail-closed BRANCH removed     rc 1 | 1 failed, 2 passed
restored                       rc 0 | 3 passed        (dispatch.py byte-gleich zurückgesetzt)
```

### 2. `R3-M1` — der Satz für eine Klammergruppe ohne Top-Level-Komma — **PASS**

Gemessen als Prozess: `tools/{test_*}.py` und `tools/test_{1..9}.py` sind beide rc 2 mit
*„a brace group with no top-level comma **is either left literal or a range, and it does not decide
which**"*. Der Docstring (`gate_test_scope.py:243`) trägt dieselbe Unterscheidung samt der
R3-M1-Messung. Vier Kopien tragen `_brace_expanded` und den Satz; die drei Kit-Spiegel sind
byte-gleich (`087cabbc10fd` ×3), `_kernel.py` ×3 `13e47244d9aa`.

Die übrigen Klammerzeilen unverändert richtig: `{test_*,conftest}` rc 2, `{tools,docs}` rc 2,
`{,test_}*.py` rc 2, `{tools/test_*,docs/x}.py` rc 2, echte Auswahlen und die unpaarige `{` rc 0.

### 3. Der Nachtrag — EINE Tür, zwei Kommandozeilen — **PASS**

`verify/rig/r4_door.py`, gelesen am Parse-Baum, nicht an der Prosa:

```
migrate_holes.py: 74 Zeilen, 1 Definition (main); write-capable calls: 0
holes.py:        398 Zeilen, 17 Definitionen;   write-capable calls: 6 (makedirs, capture_migrated_hole, open x2, replace x2)
der dünne Aufrufer re-exportiert 13 Namen aus kernel.holes und ruft holes.migrate / holes.reindex
```

Kein zweiter Schreiber. **Das Kommando als Prozess** gegen eine Kopie ausserhalb des Repos
(`r4_kernelcmd.py`, alles über `python -B -m kernel.cli … migrate-holes`):

| Lauf | gemessen |
|---|---|
| `--help` | trägt den Vertrag (`--related-pr` „required unless --reindex", `--apply`, `--reindex`, `--doc`, `--holes-dir`) |
| `--apply` ohne `--related-pr` | **rc 2**: „migrate-holes needs `--related-pr <PR-nnnn>` … `--reindex` is the one shape that writes no item" |
| Probelauf | rc 0, **155 written, 0 prose files**, Dokument **unverändert** |
| `--apply` | rc 0, **155 Items / 155 Prosadateien** |
| `--apply` erneut | rc 0, **0 written**, byte-gleich |
| `--reindex` | rc 0, „index rewritten from the store: 155 hole(s)", byte-gleich, **155 Indexzeilen**, 0 CR |
| Dokument | 805 946 → **192 003 B**, sha **`61988c1592b26a1a`** |

**Eigener Zwischenfehler, hier statt als Befund:** mein erster `--apply` gab ein ABSOLUTES
`--holes-dir` mit und ergab 202 767 B / `333f2b29b72f8b9f`. Die Ursache ist gemessen: die
Indexzeilen tragen den Pfad, den die Flagge nennt. Mit dem voreingestellten relativen
`--holes-dir` reproduziert derselbe Bestand exakt **192 003 B / `61988c1592b26a1a`**
(`r4_reindex.py`, erste Zeile `| [H1](docs/holes/H1.md) | BUG-0093 | VERIFIED | …`). Die Zeile in
Abschnitt 11 gibt die Flagge **nicht** mit — sie ist also die Zeile, die die protokollierten Zahlen
erzeugt. *Ein Satz dazu in Abschnitt 11 wäre eine billige Härtung, keine Forderung.*

**Kommandofläche und Ratsche** — `tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`
grün; die drei Verfassungen (§0-Zeile) und `README.md:336` nennen `migrate-holes`; die Ratsche ist
exakt **+17 B je Kit** (dev 51 847 → 51 864, office 56 728 → 56 745, research 54 162 → 54 179 —
gegen meine eigenen Runde-3-Messwerte), `record_lead_package_sizes.py` meldet „every size is the one
on record"; Abschnitts-Pins einmal nachgezogen (numstat 42/18). Suiten in einem Lauf:
`test_shortening_net.py` + `test_migrate_holes.py` + `test_role_contracts::test_a_paragraph…` +
der Kommandoflächen-Knoten → **50 passed** (der eine rote Knoten war meine Kopie ohne `radar/`;
mit `radar/` 1 passed).

**Die sieben migrierten Richter**: an einer migrierten Kopie des gemergten Baums **7 passed**.

### 4. Gate 1 auf BEIDEN Zeilen — die Feststellung des Umsetzers ist **wahr** — **PASS**

`verify/rig/r4_gate1.py`, der ausgelieferte Haken als Prozess, JSON auf stdin, `cwd` = die Kopie:

```
rc 0 ALLOWED | PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory migrate-holes --related-pr PR-0003 --apply
rc 0 ALLOWED | python -B tools/migrate_holes.py --root project_memory --related-pr PR-0003 --apply
rc 0 ALLOWED | dieselbe Zeile ohne --apply
rc 2 REFUSED | echo x > project_memory/probe.txt
rc 2 REFUSED | sed -i 's/a/b/' project_memory/project_config.yaml
rc 2 REFUSED | cp README.md project_memory/probe.md
rc 2 REFUSED | python -c "open('project_memory/probe.txt','w').write('x')"
rc 0 ALLOWED | python -B tools/bump_kit_version.py
```

**Was wahr ist:** die Darstellung des Umsetzers. Ein Interpreter mit einem SKRIPT- oder
`-m MODUL`-Argument ist diesem Gate kein Schreibverb; `python -c` ist ausgenommen und wird
verweigert. Der Satz aus G4-2 §7 („aus einer Sitzung heraus rc 2") beschrieb nie, was gebaut ist.
**Keine neue Nummer nötig**, und das habe ich geprüft statt geglaubt: `H11` nennt in seinem eigenen
Mechanismus genau diese beiden Befehlsformen (`PYTHONPATH=team-kits python -B -m kernel.cli …`,
`python tools/bump_kit_version.py`) als den Grund, aus dem die Interpreter-Ausnahme existiert, und
führt die Kette bis zu Gate 3 und der Buchungsschicht weiter. Der Sachverhalt ist damit
aufgeschrieben, nicht bloss protokolliert.

### 5. Stempel und Reihenfolge — **PASS**

`2026.09.05-6` ×3, `bump_kit_version.py --check` „unchanged" ×3. `VERSION` 18:54:39, Lieferlauf
`run-full-suite.txt` 19:41 — **keine** Datei im `allowed_scope` trägt eine spätere mtime; die
einzige spätere Schreibung ist `staging/generation-4-streams.md` (20:02, Lead).
Läufe: **4687 passed / 14 skipped / 0 failed (46:24)**; Haken-Suite **7 failed / 541 passed**;
`validate.py` grün; `ruff check .` über die ganze Kopie **All checks passed**.

### 6. Abschnitt 11 / 13 / 14 — **PASS**

Abschnitt 11 trägt die Kernel-Zeile (ohne `--holes-dir`), die `--reindex`-Zeile und den Push.
Beide EVD-Zeilen sind **zustands-relativ** (`staging/TSK-0126/run-full-suite.txt`,
`…/run-gates-suite.txt` — beide Dateien liegen im Repo), tragen **keinen** Diff-Hash, und ihre
Flaggen decken sich mit dem laufenden Parser. **Nicht ausgeführt**, wie verlangt. Abschnitt 13
(Zeigertabelle, 10 Zeilen) und Abschnitt 14 (Urteil je Ziel, mit `DEC-0074`/`DEC-0079` bei PR-0005
und der AC-2-Abweichung samt Codex-Messung) sind vollständig.

### 7. Baum — **PASS**

84 inhaltlich geänderte Dateien; 52 im Arbeitsbaum berührte ohne Inhaltsänderung, **alle
byte-gleich zu HEAD**; 0 CR ausser `project_memory/.audit/hook_events.jsonl`. Ausserhalb
`allowed_scope`: `radar/decided.md` (inhaltlich 9/0, im Protokoll zweimal als Änderung des Leads
benannt), `.gitignore` und `user/claude/statusline.py` (nur Zeilenenden, Z6), zwei untracked
`radar/*.md`. **Notiz für die Abnahme, kein Befund.**

---

## Abschliessendes Urteil für TSK-0126

### Je erwarteter Ausgabe

| # | Ausgabe | Urteil |
|---|---|---|
| 1 | vier Patches in Nahtreihenfolge | **PASS** |
| 2 | zehn Nähte von Hand mit Schiedsrichter | **PASS** — mit EINER benannten Abweichung: (5) verlangt den schreibenden Lauf als Zeile für eine Shell **ausserhalb** von Claude Code; er ist jetzt eine **Kernel**-Zeile, die der Lead in der Sitzung nimmt (Nutzer ist entfernt). Vom Lead entschieden, in 12d als Abweichung geführt — und meine Gate-1-Messung zeigt, dass „ausserhalb" nie durchgesetzt war |
| 3 | Löcherliste H151–H165 | **PASS** — jeder Eintrag urteilt über das, was gemessen ist; `H163` GESCHLOSSEN mit dem fail-closed Rest, `H164` OFFEN, `H165` GESCHLOSSEN für beide Expansionen mit zwei benannten Über-Verweigerungen |
| 4 | Merge-Befunde behoben oder benannt | **PASS** |
| 5 | EIN Stempel, Läufe, Gate 5 als Prozess | **PASS** |
| 6 | Hostregel | **PASS** |
| 7 | Protokoll mit allen Tabellen | **PASS** |

### Je Ziel

| Ziel | AC | Urteil |
|---|---|---|
| **PR-0004** | AC-1 Gate 5 | **PASS** — beide Shell-Expansionen geschlossen, drei Über-Verweigerungen benannt |
| | AC-2 Fristen | **ABWEICHUNG, vom Lead angenommen**, in §14 samt Codex-Messung benannt |
| | AC-3 Design-Checks | **in den Merge-Runden nicht gemessen** (der Strom hat sie gemessen); gehört so in die Abnahme |
| | AC-4 Kostenseite | **PASS** |
| **PR-0005** | AC-1..AC-5 | **PASS**, Reichweite mit `DEC-0074`/`DEC-0079` entschieden und gebaut |
| **PR-0006** | AC-1..AC-4 | **PASS**, `H158` offen und gemessen bestätigt |
| **PR-0007** | AC-1 CI | **OFFEN** — braucht den Push; kein lokales Rig ist der Runner |
| | AC-2 / AC-3 / AC-4 | **PASS** |

### Was nach dem PASS noch offen bleibt (kein Befund, sondern die zwei Zeilen und drei Löcher)

1. Der **eine schreibende Migrationslauf** (Kernel-Zeile, Abschnitt 11) — danach werden die sieben
   Richter grün; an einer Kopie gemessen: 7 passed.
2. Der **Push** für `PR-0007` AC-1.
3. `H163` (fail-closed Rest), `H164` (Modulname als Zitat), `H165` (zwei Über-Verweigerungen),
   `H158` — alle vier mit Mechanismus, Kette, Urteil und Begrenzung.

## Ausdrücklich NICHT gemessen

* Die volle `tools/`-Suite (`DEC-0050`) — `run-full-suite.txt` gelesen, die Reihenfolge nachgerechnet.
* Ob der Lieferlauf das Präfix `DELIVERY_RUN=TSK-0126` wirklich trug (kein Umgebungs-Echo im Log).
* Die beiden EVD-Zeilen (nicht ausgeführt, so verlangt).
* `PR-0004` AC-3; `PR-0007` AC-1; die härtere Lastklasse von `H162`.

## Eigene Fehlgriffe

* Mein erster `--apply` gab ein absolutes `--holes-dir` mit und ergab darum 202 767 B statt
  192 003 B; mit der voreingestellten Flagge reproduziert derselbe Bestand die protokollierte Zahl
  exakt. Rig-Parameter, kein Befund.
* Ein roter Knoten (`test_every_repo_path_the_document_names_exists`, „radar/README.md") kam daher,
  dass meine Kopie `radar/` nicht enthielt; mit dem Verzeichnis 1 passed.
* Aus den Runden 1–3 stehen vier eigene Fehlgriffe in den dortigen Berichten; sie bleiben
  eingestanden.
