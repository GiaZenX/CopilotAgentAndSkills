# TSK-0121 (PR-0004, G4-1) — Prüfbericht Runde 2 (Nacharbeit 1)

Rolle: `harness-verifier`. Read-only im Repo. Alles gemessen in einer **frischen** Kopie ohne
`.git` (`…/verify/wt2`) und auf einem **frisch gebauten** dev-Piloten (`…/verify/pilot2`), beides
unter `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/verify/`. Am Ende:
`rig/integrity2.py` → *differing: NONE / missing: NONE (0)* — jede Mutation zurückgesetzt.

AC-2 ist unter der vom Lead angenommenen Lesart beurteilt: ein fehlendes `timeout` ist das
**bekannte Vorgabefenster** des Providers, der Leser leitet daraus ab und verweigert ein Fenster,
das er nicht halten kann.

**Urteil: FAIL.** Ein blockierender Befund (B2′), drei benannte, gemessene und **nicht
aufgeschriebene** Restklassen (B2″), ein neuer fail-open-Fall in der Optionslesung (B1′), zwei
kleinere Befunde (F8, F9). Alle Befunde aus Runde 1 sind **geschlossen und nachgemessen**.

---

## Urteil je Kriterium und Pflicht

| | Runde 1 | Runde 2 | Grund |
|---|---|---|---|
| AC-1 | FAIL | **FAIL** | B1 geschlossen; B2 nur für die `.`/`..`/absolut-Schreibweisen geschlossen — B2′ (falsche Bezugsbasis) und B2″ (Identitätsklasse) offen; B1′ neu |
| AC-2 | FAIL | **PASS** | unter der angenommenen Lesart: F3 und F4 geschlossen und nachgemessen, F6 behoben, F7 behoben |
| AC-3 | PASS | **PASS** | `kit_browser_checks.py` sha256 `1a707745…` **unverändert** gegenüber Runde 1 → kein zweiter Chromium-Lauf nötig |
| AC-4 | PASS | **PASS** | Kosten unverändert im Rahmen (0,19–0,43 s gegen 120 s) |
| Pflicht 5 (rot zuerst) | teilweise FAIL | **PASS** | der Stolperdraht misst jetzt die Eigenschaft; meine Runde-1-Gegenmutation ist rot |
| Pflicht 6 (Nähte) | PASS | **PASS, mit F9** | Naht an G4-3 unverändert (2 rote Tests); F9 = Neuformatierung einer geteilten Datei |
| Pflicht 7 (Übergabe) | PASS | **PASS** | Patch 24 Dateien, `git apply --check` rc 0 gegen 75a00d1, 0 CR, 0 VERSION-Hunks, Spiegel-Hashes bestätigt |

---

## Runde-1-Befunde: alle geschlossen (nachgemessen)

**B1 (sieben Einträge, die nichts verengen).** Meine zwölf Durchlässer aus Runde 1 sind jetzt
alle rc 2:

```
rc=2 python -B -m pytest tools/ --ff        rc=2 … --nf     rc=2 … --lf     rc=2 … --sw
rc=2 python -B -m pytest tools/ -k ""       rc=2 … -m ""    rc=2 … -k=      rc=2 … -m " "
rc=2 python -B -m pytest tools/ -k " "      rc=2 … -x       rc=2 … --maxfail=1  rc=2 … --exitfirst
rc=2 python -B -m pytest tools/ -p no:cacheprovider --lf
rc=0 python -B -m pytest tools/ --co   rc=0 … --collect-only   rc=0 … --version   (sammeln nur — richtig)
```

**Der Stolperdraht misst jetzt die Eigenschaft.** Meine Runde-1-Gegenmutation, die vorher grün
blieb, ist rot:

```
$ python -B rig/r2_mutate_decl.py add-verbose      # -v, --tb, --durations als „Verengung"
FAILED …::test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests
E  … and the runner executed just as many tests with them as without:
   ['-v ran 3 of 3', '--tb=short ran 3 of 3', '--durations=3 ran 3 of 3']
```
und zwei weitere eigene Gegenmutationen:
`readd-ff` → 2 failed (`--ff ran 3 of 3` **und** `…ordering_or_cache_option[--ff]`),
`readd-ff-no-probe` → `assert not ['--ff']` (Eintrag ohne Sondenwert). Der Stolperdraht kostet
**12 pytest-Läufe einer Drei-Test-Sonde pro Testlauf**, nicht pro Option und Zeile — gemessen 14 s
allein, 59 s im mutierten Fall.

**B2 (Pfad als Text), die gemeldeten acht Schreibweisen:** alle rc 2 —
`tools/.`, `tools/./`, `./tools/.`, `tools/../tools`, `..`, `./tools/../tools/`, absolut
(vorwärts, rückwärts, kleiner Laufwerksbuchstabe), `\\?\`, `//?/`, `/c/…`.

**F3** `start_the_deadline` sagt jetzt ausdrücklich, was **nicht** gebaut ist („an entry that names
NO window is not refused"), in AC-2s eigenen Worten — deckt sich mit der Lesart des Leads.
**F4** gemessen am Piloten, in beiden Reihenfolgen:

```
one entry 0.9s                 rc=2 :: … gives this gate 0.9s, which is not enough time …
0.9s + a silent second entry   rc=2 :: … gives this gate 0.9s …
a silent first + 0.9s second   rc=2 :: … gives this gate 0.9s …
1.4s + 30s / 30s + 1.4s        rc=2 :: … gives this gate 1.4s …
30s + a silent second          rc=2 :: (gewöhnliches Urteil — 30 s sind beantwortbar)
```

**F5** jede unbrauchbare Gestalt verweigert mit eigenem Satz (Liste, `str`, `int`, `null`,
`surfaces` als String/Objekt/`null`); `{}` und `{"surfaces": []}` sind absichtlich ALLOW;
`seconds` nicht-numerisch wird beurteilt. **F6** der QS-Block steht hinter dem Satzende (Zeile 96);
Zeile 92/93 lesen wieder „…grep the report / FILE for details…". **F7** beide überholten Sätze
sind aktualisiert, und `_kernel.py:946-949` **zeigt** auf die Messung statt sie zu zitieren
(„it is a POINTER to the occasion, not a quotation of the current state").

**Zahl korrigiert, N-1 zurückgezogen** — beides deckt sich mit meiner Runde-1-Messung.

---

## B2′ — BLOCKIEREND: `_covers` relativiert gegen die falsche Basis

`.claude/hooks/gate_test_scope.py:446` (`_covers(word, entry["root"], data.get("cwd"))`),
identisch `team-kits/*/hooks/gate_test_scope.py:452`.

Die erklärten Wurzeln sind **repo-relativ** (`"root": "tools"`, `".claude/hooks/test_gates.py"`).
Relativiert wird aber gegen `data["cwd"]`. Solange die Shell in der Repo-Wurzel steht, fällt beides
zusammen; sobald nicht, vergleicht das Gate gegen eine falsche Basis. Gemessen mit variiertem
Payload-`cwd` (`rig/r2_b2b.py`):

```
rc=2 cwd = repo root, '.'
rc=2 cwd inside tools, '.'
rc=2 cwd inside tools, no target
rc=2 cwd inside tools, absolute
rc=0 cwd OUTSIDE, absolute in      <ALLOWED>   python -B -m pytest "C:/…/wt2/tools"
rc=0 cwd OUTSIDE, relative         <ALLOWED>   python -B -m pytest wt2/tools
rc=2 no cwd in the payload
rc=2 cwd = a bare drive
```

Kit-Hälfte identisch am frischen Piloten (`rig/r2_kit.py`):
`cwd OUTSIDE, absolute in` **rc 0**, `cwd OUTSIDE, relative` **rc 0**.

Das ist keine Umgehungsschreibweise: eine Shell, die eine Ebene über dem Repo steht (Worktree-
oder Scratch-Arbeit ist in diesem Projekt der Normalfall) und den absoluten Pfad schreibt — also
genau das, wozu `gate_lead_write_scope` in **jeder** Verweigerung auffordert — fährt die mit
3465 s erklärte Fläche, und das Gate schweigt. Die Kette läuft in einer Sitzung, ohne Absicht.

**Minimaler Fix:** `decide()` hält `root = _harness.repo_root(data)` bereits in der Hand
(`gate_test_scope.py:~333`, Kit: `_kernel.find_repo_root(data.get("cwd"))` in `:426`). Diese Wurzel
als Basis übergeben statt `data.get("cwd")`, und ein **relatives** Wort vorher an `cwd` anhängen,
bevor es gegen die Repo-Wurzel relativiert wird. Beide Hälften, byte-gleich. Ein Testknoten pro
Hälfte mit einem Payload-`cwd` ausserhalb der Repo-Wurzel.

---

## B2″ — Die Identitätsklasse ist offen und **nicht aufgeschrieben**

`_normalised`/`_is_absolute`/`_covers` (`gate_test_scope.py:175-232`, Kit `:214-262`) entscheiden
wieder auf **Text**. Gemessen gegen den echten Läufer (`--collect-only`, dieselbe Fläche):

```
pytest tools     rc=0 collected 4627 node ids      Gate: rc=2
pytest TOOLS     rc=0 collected 4627 node ids      Gate: rc=0   <ALLOWED>
pytest Tools     rc=0 collected 4627 node ids      Gate: rc=0   <ALLOWED>
pytest C:tools   rc=0 collected 4627 node ids      Gate: rc=0   <ALLOWED>
```
und mit einer Junction (`rig/r2_junction.py`):
```
mklink /J toolsjn tools ; same (st_dev, st_ino) as tools: True
pytest toolsjn   rc=0 collected 4627 node ids      Gate: rc=0   <ALLOWED>
```
Kit-Hälfte gleich: `TESTS` rc 0, `C:tests` rc 0.

**Diese Klasse ist in diesem Repo schon einmal gemessen und als Eigenschaft geschlossen worden** —
für Gate 1, `docs/POST_V2_WISHLIST.md:2615-2631` (TSK-0007/TSK-0008): „«Dieselbe Datei» ist, was
das Dateisystem sagt … `_harness` vergleicht darum die **Identität** des tiefsten existierenden
Vorfahren plus den textlichen Rest darunter (`_anchored`, `_ancestor_identities`, `under`) — das
deckt Junction, Symlink, `\\?\` …". Gate 5 hat statt dessen einen neuen Text-Normierer gebaut und
erbt davon nichts. Dass `\\?\`, `//?/` und `/c/…` trotzdem rc 2 sind, ist **nicht** Verständnis,
sondern der fail-closed-Zweig (nicht relativierbar → deckend).

**Was daran ein Befund ist**, unabhängig davon, wie der Lead die Klasse einstuft: sie ist gemessen
und steht **nirgends**. H152 nennt nur die Werte-Restklasse, H151 und H153 etwas anderes, und ein
Loch, das gemessen und nicht aufgeschrieben ist, ist dieselbe Fehlerklasse wie ein Kommentar, der
verspricht, was der Code nicht baut. Das Item reserviert **nur** H151–H153, also gehört die Klasse
als benannte Restklasse in H152 (bzw. eine vom Lead vergebene Nummer) — mit dem Mechanismus
(„die Identität des Ortes entscheidet, dieser Leser entscheidet auf Text"), nicht mit den drei
Schreibweisen, die ich zufällig probiert habe.

**Minimaler Fix, falls geschlossen werden soll:** `_covers` auf `(st_dev, st_ino)` des tiefsten
existierenden Vorfahren umstellen — die Maschinerie liegt in `_harness` und ist gemessen; das
kostet einen `stat` je Positional, also nichts gegen die gemessenen 0,2 s.

---

## B1′ — fail-open: eine erklärte Option ZWEIMAL, die letzte mit leerem Wert

`.claude/hooks/gate_test_scope.py:277-308` (`_narrowing_option` gibt beim **ersten** Treffer
zurück), Kit `:289`. `argparse` nimmt die **letzte** Angabe. Gemessen an der Drei-Test-Sonde
(`rig/r2_optprobe.py`, Tests schreiben ihr Laufen in eine Datei):

```
-k alpha            rc=5   3 deselected        (verengt)
-k alpha -k ""      rc=0   3 passed            (fährt alles)   Gate: rc=0  <ALLOWED>
-k alpha -k=        rc=0   3 passed            (fährt alles)   Gate: rc=0  <ALLOWED>
-k "" -k alpha      rc=5   3 deselected        (verengt)       Gate: rc=0  (richtig)
```
Kit-Hälfte gleich: `-k alpha -k ""` rc 0.

Das ist eine absichtliche Schreibweise, kein Vertipper — also nach DEC-0056 dieselbe Einstufung wie
H152s zweite Restklasse. **Aber H152 nennt sie nicht:** dort steht nur „eine ERKLÄRTE Option mit
einem wohlgeformten Wert, der nichts trifft". Hier ist der Wert wohlgeformt **und** trifft; erst
eine zweite Angabe hebt ihn auf. Anderer Mechanismus, gleiche Pflicht.

**Minimaler Fix (eine Zeile, schliesst die Klasse ganz):** nicht beim ersten Treffer je Options-
NAME zurückgeben, sondern das **letzte** Vorkommen dieses Namens entscheiden lassen. Sonst: in
H152 aufnehmen.

---

## F8 — die fail-closed-Verweigerung behauptet etwas Falsches über die Zeile

`.claude/hooks/gate_test_scope.py:458`, Kit `:465`. Ein Wort, das der Leser nicht platzieren kann,
gilt als deckend (richtig, fail-closed) — aber der gedruckte Satz ist der gewöhnliche:

```
rc=2  python -B -m pytest "D:/other-project/tests/test_x.py"
  :: [harness gate] this line runs the WHOLE declared test surface `tools` (pytest), and nothing
     on it says this is the delivery run.
rc=2  python -B -m pytest "D:/other-project/tests/test_x.py::test_one"
rc=2  python -B -m pytest "//server/share/proj/tests/test_x.py"
rc=0  python -B -m pytest "D:/other-project/tests" -k selected
```

Die Zeile fährt `tools` nicht — sie nennt ein anderes Laufwerk. Der Satz behauptet über die Zeile
etwas, das nicht stimmt, und der Remedy-Block schickt den Aufrufer auf `judged_above_seconds` und
das Lieferpräfix, statt zu sagen, was wirklich los ist. Der `_covers`-Docstring (`:213-218`) trägt
die Wahrheit, die Verweigerung nicht.

**Minimaler Fix:** im nicht-platzierbaren Zweig einen eigenen Satz („dieses Gate konnte `%s` nicht
gegen die Repo-Wurzel platzieren und liest es darum als möglicherweise die ganze Fläche"), und die
Über-Verweigerung mit dieser Messung in die Löcherliste.

---

## F9 — `tools/provider_observations.json` ist komplett neu eingerückt

`git diff 75a00d1 --numstat` → **146/146**; `--ignore-all-space` → **1/1**. Gemessen
(`rig/r2_ws.py`): 149 der 153 Zeilen unterscheiden sich nur in der Einrückung — die Datei wurde mit
`indent=1` statt `indent=2` neu geschrieben. Semantisch ist genau **ein** Wert geändert
(`rig/r2_obs.py`: `VALUE .hook_deadlines.what_follows_for_the_kits`, sonst nichts, keine Schlüssel
verloren) — also inhaltlich sauber, aber `tools/**` ist die Naht mit G4-2, G4-3 und G4-4, und eine
ganzflächige Neuformatierung dort kollidiert mit jedem anderen Strom, der die Datei anfasst, und
begräbt die eine echte Zeile.

**Minimaler Fix:** mit der ursprünglichen Einrückung zurückschreiben, so dass der Diff eine Zeile ist.

---

## Rot zuerst — eigene Reproduktionen dieser Runde

| Mutation (in meiner Kopie, danach zurückgesetzt) | Knoten | Ergebnis |
|---|---|---|
| `-v`, `--tb`, `--durations` als Verengung erklärt (meine Runde-1-Gegenmutation) | `test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests` | **rot** — war in Runde 1 grün |
| `--ff` mit Sondenwert wieder eingetragen | dto. **und** `test_gate5_refuses_a_full_run_carrying_only_an_ordering_or_cache_option[--ff]` | **2 rot** |
| `--ff` ohne Sondenwert eingetragen | dto. (`assert not ['--ff']`) | **rot** |

---

## Läufe (nur lesende Suiten, einer nach dem anderen)

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or …narrowing… or …path… or …absolute… or …selector… or ordering_or_cache…"` | **41 passed**, 106 s |
| `tools/test_hooks.py -k "gate_test_scope or qe_skill or window or deadline_reader or …"` | **49 passed**, 76 s |
| `tools/test_context_budget.py -k no_shipped_hook_refuses_outside_the_one_funnel` | **1 passed**, 2,7 s — Präambel-Fix bestätigt |
| `tools/test_shortening_net.py` | **34 passed, 2 failed** = die Naht an G4-3, unverändert |

Volle Suite **nicht** gefahren (DEC-0050 — Lieferkriterium des Merges).

## Paket-Hygiene

Patch: 24 Dateien, `git apply --check` **rc 0** und `--3way` rc 0 gegen einen aus 75a00d1
materialisierten Baum, 4387 +/160 −, **0 CR-Bytes**, **0 VERSION-Hunks**. Spiegel nachgemessen:
`gate_test_scope.py` sha256 `42732894801fd73a…` ×3, `_kernel.py` `13e47244d9aa2eea…` ×3,
`kit_browser_checks.py` `1a7077452cf49a46…` dev = research — alle drei genau wie berichtet.
`ENFORCEMENT.md` trägt die Zeile ×3. Alle 27 berührten Dateien liegen im `allowed_scope`.

## Ausdrückliche Negativbefunde

**Gemessen und in Ordnung:** die zwölf B1-Durchlässer aus Runde 1; `-x`/`--maxfail=1`/`--exitfirst`
nicht als Verengung erklärt (rc 2, und die Sonde bestätigt: 3 von 3 liefen); `--co`/`--collect-only`/
`--version` erlaubt (sammeln nur); `--ignore=` leer → rc 2; `-k " "` → rc 2; `--ignore` ohne Wert →
rc 0, aber `pytest` bricht dabei mit einem argparse-Fehler ab, es läuft nichts; die acht
B2-Schreibweisen aus Runde 1; Auswahl (Unterpfad, Knoten-Id, gepunkteter Unterpfad, absoluter
Unterpfad) passiert weiter; F3/F4/F5/F6/F7 wie oben; Präambel-Fix; Naht an G4-3 unverändert;
Spiegel byte-gleich; Patch sauber; `provider_observations.json` semantisch nur an einer Stelle
geändert.

**Nicht gemessen (offen benannt):** die volle Suite (Merge, DEC-0050); AC-3 nicht erneut gefahren,
weil die Datei byte-identisch zu Runde 1 ist (sha256 `1a707745…`); office- und research-Piloten
(nur ein dev-Pilot; die drei Gates und `_kernel.py` sind byte-gleich); `.codex/hooks.json`;
archiviertes `EVD` gegen den zweiten Volllauf; ein zweites offenes Item als Präfix; der
PowerShell-Zweig der QS-Rollenzeile; die restlichen 10 der 13 gemeldeten Mutationen; Laufzeit unter
echter Parallel-Last (BUG-0033).

## Verdikt

**FAIL — B2′ blockiert die Runde; B2″ und B1′ sind gemessene Restklassen, die aufgeschrieben
gehören, bevor die Runde durchgeht.** Die Nacharbeit ist gut: B1 ist als Eigenschaft geschlossen,
nicht als Liste — der neue Stolperdraht fragt den Läufer, zählt Tests, die wirklich gelaufen sind,
und meine Runde-1-Gegenmutation, die vorher grün blieb, ist jetzt rot; F3 bis F7 sind sauber
erledigt, die falsche Zahl ist korrigiert und N-1 zurückgezogen. Gescheitert ist es daran, dass
B2 nur auf der Ebene behoben wurde, auf der ich es gemeldet hatte: die sechs Punkt-Schreibweisen
und der absolute Pfad sind zu, aber der neue Leser relativiert gegen `data["cwd"]`, während die
erklärten Wurzeln repo-relativ sind — eine Shell eine Ebene über dem Repo fährt mit dem absoluten
Pfad, den Gate 1 verlangt, die ganze 3465-s-Fläche bei **rc 0**, in beiden Hälften. Und der Leser
entscheidet weiter auf Text, wo dieses Repo die Frage schon einmal als Eigenschaft beantwortet hat:
`TOOLS`, `C:tools` und eine Junction sammeln gemessen dieselben 4627 Knoten und passieren, während
`_harness` seit TSK-0008 genau dafür `(st_dev, st_ino)` vergleicht. Beides ist wenige Zeilen weit —
die Repo-Wurzel steht in `decide()` schon bereit, und die Identitätsmaschinerie liegt nebenan.
Zusammen mit der Ein-Zeilen-Änderung an `_narrowing_option` (letztes Vorkommen statt erstem), dem
eigenen Satz für den nicht-platzierbaren Zweig und der zurückgenommenen Neueinrückung ist AC-1
abnehmbar; AC-2, AC-3 und AC-4 sind es jetzt schon.
