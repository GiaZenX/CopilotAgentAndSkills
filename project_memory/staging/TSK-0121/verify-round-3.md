# TSK-0121 (PR-0004, G4-1) — Prüfbericht Runde 3 (Nacharbeit 2)

Rolle: `harness-verifier`. Read-only im Repo. Gemessen in einer **frischen** Kopie ohne `.git`
(`…/verify/wt3`) und auf einem **frisch gebauten** dev-Piloten (`…/verify/pilot3`), beides unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/verify/`. Abschluss: `rig/integrity2.py`
→ *differing: NONE / missing: NONE (0)* — jede Mutation zurückgesetzt.
AC-2 unter der vom Lead angenommenen Lesart.

**Urteil: FAIL — aber kein blockierender Befund.** Jeder Befund der Runden 1 und 2 ist geschlossen
und von mir nachgemessen; das Verhalten des Gates hält gegen alles, was ich in drei Runden gefunden
habe. Offen sind **zwei Dokumentationspflichten**: eine gemessene Über-Verweigerung, die nirgends
aufgeschrieben ist (F10), und ein Docstring-Satz, der eine Differenz behauptet, die es nicht gibt
(F11). Beides ist nach den Hausregeln ein FAIL-Grund, beides ist eine kurze Prosa-Nacharbeit weit.

---

## Urteil je Kriterium und Pflicht

| | R1 | R2 | R3 | Grund |
|---|---|---|---|---|
| AC-1 | FAIL | FAIL | **PASS (Verhalten)** | B1, B1′, B2, B2′, B2″, F8 alle geschlossen und nachgemessen |
| AC-2 | FAIL | PASS | **PASS** | unverändert |
| AC-3 | PASS | PASS | **PASS** | `kit_browser_checks.py` sha256 `1a707745…` unverändert seit Runde 1 |
| AC-4 | PASS | PASS | **PASS, mit F10** | Kosten 0,20–0,36 s gegen 120 s; die Kostenseite dieser Runde (Über-Verweigerung) ist nicht benannt |
| Pflicht 5 (jede Eigenschaftsbehauptung gemessen; benannter Test kann scheitern) | teilw. FAIL | PASS | **FAIL (F11)** | eine Behauptung im Kit-Docstring ist gemessen falsch |
| Pflicht 5 / Löcherliste (gemessen ⇒ aufgeschrieben) | — | FAIL | **FAIL (F10)** | die Über-Verweigerungsklasse steht in keinem Eintrag |
| Pflicht 6 (Nähte) | PASS | PASS | **PASS** | Naht an G4-3 unverändert (2 rote Tests), `session_status.py`/`_routine.py` unberührt |
| Pflicht 7 (Übergabe) | PASS | PASS | **PASS** | 24 Dateien, `git apply --check` rc 0 gegen 75a00d1, 0 CR, 0 VERSION-Hunks, Spiegel bestätigt |

---

## Runde-2-Befunde: alle geschlossen (nachgemessen)

**B2′ — Bezugsbasis.** Beide Hälften, echte Hook-Prozesse:

```
REPO   rc=2 cwd OUTSIDE, absolute in     FULL-RUN      (Runde 2: rc 0)
REPO   rc=2 cwd OUTSIDE, relative        FULL-RUN      (Runde 2: rc 0)
REPO   rc=2 cwd two levels up, relative  FULL-RUN
REPO   rc=2 NO cwd key, absolute         FULL-RUN
REPO   rc=2 NO cwd key, relative         UNPLACEABLE   (fail-closed)
REPO   rc=2 cwd on another drive, absolute  FULL-RUN
KIT    rc=2 cwd OUTSIDE, absolute in / relative   FULL-RUN   (Runde 2: rc 0 / rc 0)
```
Der echte `..`-Fall INS Repo, mit einem `cwd`, das ein **Geschwister** der Kopie ist
(`rig/r3_dotdot.py`, `../wt3/tools` existiert von dort):
```
rc=2 ../wt3/tools  (IS the root)            FULL-RUN
rc=2 ../wt3        (ancestor of the root)   FULL-RUN
rc=0 ../wt3/tools/test_hooks.py (selection) <ALLOWED>
rc=2 ../rig        (unrelated sibling)      UNPLACEABLE
```
*(Eigener Fehler: in meinem ersten Anlauf war `cwd` das Elternverzeichnis, von dem aus
`../pilot3/tests` gar nicht existiert — das gemeldete UNPLACEABLE war mein Testfall, nicht das
Gate. Korrigiert und oben richtig gemessen.)*

`cwd` **durch eine Junction** auf die Kopie (`rig/r3_cwdjn.py`): Wurzel rc 2 FULL-RUN, Auswahl
rc 0, absoluter Pfad über die Junction rc 2, und dasselbe mit `CLAUDE_PROJECT_DIR` ebenfalls durch
die Junction — der Identitätsleser sieht überall denselben Ort.

**B2″ — Identität statt Text.** Gegen den echten Läufer gemessen und dann gegen das Gate:

```
pytest toolsjn collected 4633,  pytest tools collected 4633
rc=2 junction OVER tools                FULL-RUN     (Runde 2: rc 0)
rc=2 junction, trailing slash / absolute / + case   FULL-RUN
rc=0 junction to a SUBDIR of tools      <ALLOWED>    (Auswahl — nicht über-verweigert)
rc=2 TOOLS / Tools                      FULL-RUN     (Runde 2: rc 0)
rc=2 C:tools (drive-relative)           UNPLACEABLE  (Runde 2: rc 0)
rc=2 \\?\…\tools  und  //?/…/tools      FULL-RUN     (Runde 2: fail-closed — jetzt aus dem richtigen Grund)
rc=2 /c/…/tools                         UNPLACEABLE
rc=2 Junction AUS dem Repo hinaus       UNPLACEABLE
rc=2 .claude/HOOKS/TEST_GATES.PY        FULL-RUN     (zweite erklärte Wurzel, Schreibweise egal)
rc=0 tools/does_not_exist_yet           <ALLOWED>    (noch nicht existierender Pfad UNTER der Wurzel = Auswahl)
rc=0 docs (sibling)                     <ALLOWED>
```
Der Kit-Pilot antwortet in jedem dieser Fälle gleich.

**Der Drift-Pin scheitert aus JEDER Richtung einzeln** — das war meine Hauptfrage an die zweite
Implementierung:

```
$ python -B rig/r3_mutate.py kit-text        # nur der KIT-Leser wird wieder textuell
FAILED tools/test_hooks.py::test_the_kit_reader_and_the_workshops_agree_on_what_one_place_is
E  … disagree about these places: ['…\project\TESTS', '…\project\tests-junction']

$ python -B rig/r3_mutate.py harness-text    # nur der WERKSTATT-Leser wird wieder textuell
FAILED tools/test_hooks.py::test_the_kit_reader_and_the_workshops_agree_on_what_one_place_is
```

**B1′ — die letzte Angabe entscheidet.** Gegen die Sonde (Tests schreiben ihr Laufen in eine Datei)
und gegen das Gate:
```
-k alpha             rc=5  3 deselected     Gate rc=0   (verengt — richtig)
-k alpha -k ""       rc=0  3 passed         Gate rc=2   (Runde 2: rc 0)
-k=alpha -k ""       rc=0  3 passed         Gate rc=2
-m slow -m ""        rc=0  3 passed         Gate rc=2
-k "" -k alpha       rc=5  3 deselected     Gate rc=0   (Gegenrichtung erhalten)
-k alpha -k          rc=4  argparse error, es läuft NICHTS   Gate rc=0  (harmlos)
```
Kit-Hälfte identisch.

**F8 — eigener Satz für den nicht platzierbaren Zweig.** Keine der Zeilen trägt mehr die falsche
Behauptung:
```
rc=2 "D:/other/tests"                UNPLACEABLE
rc=2 "D:/other/tests/test_x.py"      UNPLACEABLE
rc=2 "//server/share/proj/tests"     UNPLACEABLE
rc=2 tools/../../tools               UNPLACEABLE   (das Seitenfindung des Umsetzers — bestätigt)
rc=2 tools/../..                     FULL-RUN      (ein echter Vorfahr — richtig unterschieden)
```

**F9 — `tools/provider_observations.json`:** `git diff 75a00d1 --numstat` → **1 1**. Die
Neueinrückung ist zurückgenommen.

**Eigenbefund des Umsetzers bestätigt:** der Zeiger im Kit-Docstring steht jetzt auf
`tools/test_hooks.py::test_the_kit_reader_and_the_workshops_agree_on_what_one_place_is`
(`team-kits/dev-team/hooks/gate_test_scope.py:267`), und `test_repo_hygiene.py -k pointer` ist
**4 passed**.

---

## F10 — Die Über-Verweigerung ist gemessen und steht in keinem Eintrag

`.claude/hooks/gate_test_scope.py:262` (`return True, str(word)`), Kit `:344`.

Ein Ziel, das der Leser nicht gegen das Repo platzieren kann, deckt — richtig und fail-closed. Was
darunter fällt, ist aber breiter als „ein anderes Laufwerk": **jede** Suite ausserhalb des Repos,
auch eine einzelne Datei, wird verweigert. Gemessen (`rig/r3_outside.txt`, cwd = Repo-Wurzel):

```
rc=2 python -B -m pytest "C:/…/verify/pytestprobe/suite"              UNPLACEABLE
rc=2 python -B -m pytest "C:/…/verify/pytestprobe/suite/test_1.py"    UNPLACEABLE   ← eine AUSWAHL
rc=0 python -B -m pytest "C:/…/verify/pytestprobe/suite" -k test_a1                 (eine Verengungsoption hebt es)
```
dazu `../rig` (unverwandtes Geschwister) rc 2, eine Junction aus dem Repo hinaus rc 2, und ohne
`cwd` im Payload auch eine Auswahl im Repo rc 2.

**Warum das mehr als Kosmetik ist:** genau dieses Vorgehen schreibt dieses Repo vor. CLAUDE.md
verlangt für jeden Fix, „den Defekt in einem Klon **außerhalb** des Repos wiederherzustellen, den
Test zu fahren, rot zu **sehen**" — und die Zeile, die das tut, ist ab jetzt rc 2, solange sie kein
`-k` oder das Lieferpräfix trägt. Das ist DEC-0056s Kostenseite auf dem legitimen Pfad, und AC-4
verlangt sie ausdrücklich **je Gate benannt**. Sie steht weder in H151 noch in H152 noch in H153
(deren Mechanismen sind die Erklärung, die Optionen und der Läufername), noch im AC-4-Abschnitt
des Protokolls. Jede andere Über-Verweigerung dieses Apparats trägt einen Eintrag mit Kette
(H18/H19/H20/H23/H33/H150); diese nicht.

**Zwei Wege, einer reicht.**
1. *Aufschreiben*: als zweite benannte Klasse in H153 (oder eine vom Lead vergebene Nummer) mit
   der Kette oben und der Begrenzung („eine Verengungsoption oder das Lieferpräfix hebt sie").
2. *Verengen* (klein und sicher): ein Wort, das der Leser **platzieren kann** und das schlicht
   ausserhalb der Repo-Wurzel liegt, ist entscheidbar **nicht** die erklärte Fläche — also Auswahl,
   nicht deckend. „Nicht platzierbar" bliebe für das, was der Leser wirklich nicht ausrechnen kann
   (laufwerksrelativ, `/c/…`, fremdes Laufwerk/UNC, kein `cwd`). Über einen Link, der ins Repo
   zeigt, entscheidet der Identitätsleser vorher — die Verengung öffnet also nichts.

**Blockiert die Runde nicht** (Über-Verweigerung, auf der Zeile beantwortbar), gehört aber als
benannter Rest in die Löcherliste, bevor die Runde durchgeht.

---

## F11 — Der Kit-Docstring nennt eine Differenz, die es nicht gibt

`team-kits/*/hooks/gate_test_scope.py:270-271`:

> WHAT IT IS NOT is the workshop's version in full: `_harness` puts every filesystem question
> under its gate's deadline (`probe`) **and case-folds the tail**.

Gemessen: **beide** Leser rufen `os.path.normcase` an derselben Stelle —
`.claude/hooks/_harness.py:365-367` (`return os.path.normcase(text), …` / `names.append(os.path.normcase(name))`)
und `team-kits/dev-team/hooks/gate_test_scope.py:283-284` (dieselben zwei Zeilen). Die einzige echte
Differenz ist der `probe`-Mantel um die Dateisystemfragen (`_harness._resolved` =
`probe(os.path.realpath, os.path.abspath(...))` gegen `os.path.realpath(os.path.abspath(...))`) —
und die nennt derselbe Satz korrekt.

Die Hausregel schneidet in beide Richtungen: eine unter-behauptende Aussage über den eigenen Code
ist so falsch wie eine über-behauptende, und dieser Satz lädt die nächste Runde ein, eine
Case-Behandlung „nachzurüsten", die schon da ist.

**Minimaler Fix:** die Case-Folding-Teilaussage streichen; der Rest des Satzes stimmt.

---

## Rot zuerst — eigene Reproduktionen dieser Runde (5)

| Mutation (nur in meiner Kopie, danach zurückgesetzt) | Knoten | Ergebnis |
|---|---|---|
| Kit-`under` wieder textuell | `test_the_kit_reader_and_the_workshops_agree_on_what_one_place_is` | **rot** (`TESTS`, `tests-junction`) |
| `_harness.under` wieder textuell | derselbe | **rot** — der Pin fängt **jede** Seite einzeln |
| `_placed` hängt ein relatives Wort nicht mehr an `cwd` | `test_gate5_measures_the_declared_root_against_the_REPO_and_not_against_the_shells_cwd` | **rot** („from a shell above the repo, 'python -B -m pytest project/tools' was allowed") |
| laufwerksrelativer Zweig entfernt | `test_gate5_says_so_when_it_cannot_place_a_target_at_all` | **rot** (`C:tools` bekam wieder den gewöhnlichen Satz) |
| erste statt letzter Angabe entscheidet | `test_gate5_lets_the_LAST_occurrence_of_an_option_decide[…]` ×2 + `test_gate5_still_reads_a_narrowing_last_occurrence_as_a_selection` | **3 rot** — Regel und Gegenrichtung beide gemessen |

## Läufe (nur lesende Suiten, einer nach dem anderen)

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or …"` | **48 passed**, 110 s |
| `tools/test_hooks.py -k "gate_test_scope or … or kit_reader_and_the_workshops"` | **55 passed**, 80 s |
| `tools/test_repo_hygiene.py -k pointer` | **4 passed**, 66 s |
| `tools/test_shortening_net.py` | **34 passed, 2 failed** = Naht an G4-3, unverändert |

Volle Suite **nicht** gefahren (DEC-0050 — Lieferkriterium des Merges).

## Paket-Hygiene

Patch: **24 Dateien**, `git apply --check` **rc 0** und `--3way` rc 0 gegen einen aus 75a00d1
materialisierten Baum, 4824 +/15 −, **0 CR-Bytes**, **0 VERSION-Hunks**. Spiegel nachgemessen und
genau wie berichtet: `gate_test_scope.py` sha256 `800db1a0fbcebe95…` ×3, `_kernel.py`
`13e47244d9aa2eea…` ×3, `kit_browser_checks.py` `1a7077452cf49a46…` (dev = research). Vorläufige
Stempel `2026.09.05-4` ×3. H152 trägt jetzt genau **eine** offene fail-open-Klasse
(„eine ERKLÄRTE Option mit einem wohlgeformten Wert, der nichts trifft"), und die ist von mir
nachgemessen: `--deselect x -k ""` und `-k "" --deselect x` sind rc 0 und liessen an der Sonde drei
von drei Tests laufen. *(Kleiner Vorschlag, kein Befund: H152 illustriert die Klasse mit
`--deselect does::not::exist`; die billigste lebende Schreibweise ist das unauffällige
`--deselect x`.)*

## Ausdrückliche Negativbefunde

**Gemessen und in Ordnung:** alle Befunde der Runden 1 und 2 (oben je mit Zeile); `..`-relativ ins
Repo, `cwd` durch eine Junction, `cwd` zwei Ebenen darüber, fehlendes `cwd`, `cwd` auf einem anderen
Laufwerk, `cwd` in einem nicht existierenden Verzeichnis; noch nicht existierende Ziele unter der
Wurzel als Auswahl; Junction auf ein Unterverzeichnis als Auswahl; zweite erklärte Wurzel in jeder
Schreibweise; `-k alpha -k` harmlos (argparse bricht ab); Drift-Pin aus beiden Richtungen; Zeiger-
Prüfer grün; Spiegel, Patch, Stempel, Naht.

**Nicht gemessen (offen benannt):** volle Suite (Merge); AC-3 nicht erneut gefahren (Datei
byte-identisch zu Runde 1, sha256 `1a707745…`); office- und research-Piloten (nur dev; die drei
Gates und `_kernel.py` sind byte-gleich); `.codex/hooks.json`; archiviertes `EVD` gegen den zweiten
Volllauf; ein zweites offenes Item als Präfix; der PowerShell-Zweig der QS-Rollenzeile; die
restlichen 5 der 10 gemeldeten Mutationen; Laufzeit unter echter Parallel-Last (BUG-0033); das
Verhalten auf einem case-sensitiven Dateisystem.

## Verdikt

**FAIL, ohne blockierenden Befund — zwei Prosa-Pflichten weit von PASS.** Diese Nacharbeit hat den
Kern richtig angefasst: statt den Text-Normierer noch einmal zu flicken, ruft die Repo-Hälfte jetzt
`_harness.under` auf — eine Antwort auf eine Frage —, und die Kit-Hälfte, die ohne `_harness`
ausgeliefert wird, trägt die Eigenschaft ein zweites Mal **mit einem Pin, der aus jeder Richtung
einzeln rot wird**; das habe ich in beide Richtungen mutiert und gesehen. Junction, Gross-/
Kleinschreibung, laufwerksrelativ, `\\?\`, die Bezugsbasis und die doppelt angegebene Option sind
alle zu, in beiden Hälften, und die Gegenrichtungen (Auswahl, Junction auf ein Unterverzeichnis,
`-k "" -k alpha`) sind erhalten geblieben — genau die Über-Verweigerung, an der so ein Fix sonst
kippt. Was fehlt, ist nichts am Code: die neue Über-Verweigerung — **jede** Suite ausserhalb des
Repos ist rc 2, auch eine einzelne Datei, und das ist die Zeile, die dieses Repo für jeden roten
Test vorschreibt — ist gemessen und in keinem Eintrag der Löcherliste und in keinem AC-4-Abschnitt
gelandet, und ein Docstring nennt eine Case-Folding-Differenz zwischen den beiden Lesern, die es
gemessen nicht gibt. Ein Eintrag (oder die kleine, sichere Verengung) und ein gestrichener
Halbsatz, dann ist AC-1 abnehmbar; AC-2, AC-3 und AC-4 sind es.
