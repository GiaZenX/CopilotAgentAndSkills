# TSK-0121 (PR-0004, G4-1) — Prüfbericht Runde 1

Rolle: `harness-verifier`. Read-only im Repo; alles gemessen in einer Kopie ohne `.git` unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/verify/`. Jede Mutation wurde zurückgesetzt;
`rig/integrity.py` am Ende: *files differing from the worktree after all mutations: NONE*.

**Urteil: FAIL.** Zwei blockierende Befunde (B1, B2), beide am **Fix**, nicht am ursprünglichen
Angriff, beide mit einer Kette, die innerhalb einer Sitzung durchläuft. Fünf weitere Befunde
(F3–F7) sind Schutzbehauptungen bzw. Auslieferungsfehler, kein Blocker. AC-3 und AC-4 sind PASS.

---

## Urteil je Kriterium

| Kriterium | Urteil | Grund |
|---|---|---|
| AC-1 (FR-0086) | **FAIL** | B1 (sieben von 21 erklärten „Verengungs"-Optionen verengen nichts → Volllauf rc 0), B2 (`_covers` vergleicht Text → `tools/.`, `..`, absoluter Pfad rc 0). Alles Übrige gebaut und als Prozesse belegt. |
| AC-2 (FR-0057) | **FAIL** | Wörtliche Forderung nicht ausgeführt (Abweichung, vom Lead zu entscheiden — die Widerlegung habe ich nachgemessen und sie trägt); am gebauten Ersatz F3 (Docstring behauptet AC-2 zu erfüllen, tut es für genau den benannten Fall nicht) und F4 (`registered_window` widerspricht seinem eigenen Docstring in Richtung ALLOW); F6 (QS-Rollentext zerschneidet einen Bestandssatz). |
| AC-3 (H139) | **PASS** | C1/C2/C3 laufen gegen die wirklich ausgelieferte `frontend/dist` mit echtem Chromium; sechs Verletzungen je eigene Regel rot; Spiegel byte-gleich; rot-zuerst reproduziert. |
| AC-4 (DEC-0056) | **PASS** | Kosten selbst gemessen, Größenordnung des Berichts bestätigt. |
| Pflicht 5 (rot zuerst, benannte Tests) | **teilweise FAIL** | vier eigene Mutationen rot reproduziert; aber `test_every_declared_narrowing_option_earns_its_place` **kann nicht scheitern** (Tautologie über die Liste, aus der das Gate selbst entscheidet). |
| Pflicht 6 (Nähte) | **PASS, mit Korrektur** | `_kernel.py` ist **keine** Naht: TSK-0122 verbietet `team-kits/*/hooks/_*.py`, TSK-0123/0125 verbieten `team-kits/*/hooks/**`. Befund N-1 des Umsetzers ist damit erledigt. `session_status.py`/`_routine.py` unverändert. Abschnitt 8 trägt die G4-3-Sätze wörtlich, beide genannten Tests sind wirklich rot. |
| Pflicht 7 (Übergabe) | **PASS** | Patch `git apply --check` rc 0 gegen 75a00d1, 23 Dateien, keine VERSION-Hunks, 0 CR-Bytes, Spiegel byte-gleich, sha256-Präfixe des Berichts stimmen. |

---

## B1 — BLOCKIEREND: sieben der 21 erklärten „Verengungs"-Optionen verengen nichts

`tools/test_surface.json:29-35` (`--lf`, `--last-failed`, `--ff`, `--failed-first`, `--nf`,
`--new-first`, `--sw`, `--stepwise`) zusammen mit `.claude/hooks/gate_test_scope.py:209-222`
(`_narrowing_option` vergleicht nur den Optionsnamen).

`--ff`/`--nf` sind in pytest **reine Sortieroptionen**; `--lf`/`--sw` verengen nur, wenn ein Cache
mit Fehlschlägen existiert. Gemessen an einer Drei-Test-Suite (`rig/optprobe.py`):

```
(none)          rc=0  3 passed in 0.25s
--ff            rc=0  3 passed in 0.26s
--nf            rc=0  3 passed in 0.26s
--failed-first  rc=0  3 passed in 0.26s
--new-first     rc=0  3 passed in 0.28s
-k ""           rc=0  3 passed in 0.28s
-m ""           rc=0  3 passed in 0.28s
--sw            rc=0  3 passed in 0.25s
--lf (kein Cache) rc=0  3 passed in 0.21s
```

Und das Gate lässt genau diese Zeilen durch (`rig/batch.py rig/lines3.txt`, echte Prozesse gegen
die Kopie):

```
rc=0 0.138s python -B -m pytest tools/ --ff
rc=0 0.147s python -B -m pytest tools/ --nf
rc=0 0.159s python -B -m pytest tools/ --lf
rc=0 0.146s python -B -m pytest tools/ --sw
rc=0 0.138s python -B -m pytest tools/ -k ""
rc=0 0.135s python -B -m pytest tools/ -m ""
rc=0 0.141s python -B -m pytest --ignore=tools/x tools
```

`tools` ist mit **3465 s** erklärt. `python -B -m pytest tools/ --ff` ist keine
Umgehungsschreibweise, sondern die Zeile, die jemand tippt, der „die zuletzt gefallenen zuerst"
will — und sie kostet den vollen Lauf, also genau die Fehlerklasse, für die das Gate gebaut wurde.

**Die beiden genannten Stolperdrähte fangen das nicht, und einer kann überhaupt nicht scheitern.**
Mutation in der Kopie: `-v`, `--tb`, `--durations` in `options_that_narrow` eingetragen —

```
$ python -B -m pytest .claude/hooks/test_gates.py -k "declared_narrowing_option" -q
2 passed, 511 deselected in 17.66s
$ python -B rig/g5.py … "python -B -m pytest tools/ -v"
rc=0  0.206s
```

nach dem Zurücksetzen derselben Zeile: `rc=2`. `test_every_declared_narrowing_option_earns_its_place`
(`.claude/hooks/test_gates.py:6958`) fährt jeden Eintrag durch das Gate und fragt, ob das Gate ihn
liest — das ist eine **Tautologie über die Liste, aus der das Gate seine Antwort nimmt**;
`test_every_declared_narrowing_option_is_one_the_runner_still_has` (`:6940`) fragt nur, ob die
Zeichenkette in `pytest --help` vorkommt. Keiner der beiden fragt den Läufer, **was** die Option tut.

**Schutzbehauptungen, die daran hängen** (Hausregel 3):
* `docs/POST_V2_WISHLIST.md:9251` — „sie lässt nie einen Volllauf durch". Gemessen falsch.
* `docs/POST_V2_WISHLIST.md:9256-9257`, `tools/test_surface.json:46`,
  `.claude/hooks/gate_test_scope.py:32-36` — „Stolperdraht an BEIDEN Enden", „also fällt ein
  Eintrag auf, der nichts entscheidet". Beide Enden messen die Eigenschaft nicht.

**Minimaler Fix.** (a) Die zehn Einträge `--lf/--last-failed/--ff/--failed-first/--nf/--new-first/
--sw/--stepwise/--sw-skip/--stepwise-skip` aus `options_that_narrow` streichen — Über-Verweigerung
ist die sichere Richtung und H152 trägt sie bereits. (b) `_narrowing_option` zusätzlich am WERT
prüfen: `-k`/`-m` mit leerem Wert (`-k ""`, `-k=`) verengen nicht. (c) Den zweiten Stolperdraht auf
den **Läufer** umstellen (`--collect-only -q` an einer Fixture-Suite mit und ohne die Option, die
gesammelte Menge muss echt kleiner werden) — oder in H152 und im Feldkommentar ehrlich
hinschreiben, dass kein Ende die Verengung misst.

**Blockiert die Runde**: ja. Die Kette läuft in einer Sitzung, ohne Absicht, mit einer gewöhnlichen
Flagge.

---

## B2 — BLOCKIEREND: `_covers` vergleicht Zeichenketten, nicht Pfade

`.claude/hooks/gate_test_scope.py:145-163` (`_normalised` / `_covers`), byte-gleich gespiegelt in
`team-kits/*/hooks/gate_test_scope.py:211-227` (`covers`).

`_covers` prüft `here == there` oder `there.startswith(here + "/")` auf dem rohen Wort. Damit ist
weder ein `.`- oder `..`-Segment noch ein absoluter Pfad ein Treffer. Gemessen (Repo-Hälfte):

```
rc=0 0.150s python -B -m pytest tools/.
rc=0 0.142s python -B -m pytest tools/../tools
rc=0 0.145s python -B -m pytest "C:/Offline Repos/.../verify/wt/tools"
rc=0 0.146s python -B -m pytest ..
rc=0 0.159s python -B -m pytest tools/./
rc=0 0.155s python -B -m pytest ./tools/.
```

und identisch in der Kit-Hälfte am gebauten Piloten (`rig/kitcovers.py`):

```
rc=2 0.218s python -m pytest tests/
rc=0 0.123s python -m pytest tests/.
rc=0 0.134s python -m pytest tests/../tests
rc=0 0.144s python -m pytest ..
rc=0 0.129s python -m pytest tests/./
rc=0 0.168s python -m pytest C:/…/pilot-covers/tests
```

Zwei Punkte machen das blockierend statt kosmetisch:

1. **Der absolute Pfad ist die Schreibweise, zu der die anderen Gates dieses Repos zwingen.**
   `gate_lead_write_scope` beendet jede seiner Verweigerungen mit „Remedy: spell the path
   absolutely and without a tilde prefix" — wer dem folgt, umgeht Gate 5 ohne es zu merken.
   (Ich bin während dieser Prüfung selbst dreimal in genau diese Verweigerung gelaufen.)
2. `..` ist wörtlich der Fall, den der Docstring in `:156-158` zusagt: „True for the root itself and
   for every **ANCESTOR** of it".

**Minimaler Fix.** In `_normalised` `os.path.normpath` anwenden (nach dem Ersetzen der Backslashes),
und in `_covers` ein absolutes Wort vorher gegen `data["cwd"]` relativieren; ein Wort, das sich
nicht auflösen lässt, gilt als deckend (fail-closed). Beide Hälften, byte-gleich.

**Blockiert die Runde**: ja.

---

## F3 — `_kernel.start_the_deadline` behauptet, AC-2 zu erfüllen; für den benannten Fall tut es das nicht

`team-kits/*/hooks/_kernel.py:1036-1040`:

> TWO ANSWERS, and the first is the one AC-2 of PR-0004 calls "the deadline reader refuses that
> entry with a sentence": a registration whose window is at or under the reserve …

AC-2 lautet: „**When any hook entry lacks a timeout**, Then a shipped test is red and the
session-start reader refuses that entry with a sentence." Der gebaute Fall ist ein anderer: ein
**genanntes** Fenster ≤ 1,5 s. Gemessen am Piloten (`rig/deadline.py`, echte Hook-Prozesse):

```
no timeout (as shipped)  rc=2 0.226s :: this line runs the WHOLE declared test surface `tests` …
timeout=0.5              rc=2 0.114s :: this call could not be judged: the registration gives this gate 0.5s …
timeout=1.0              rc=2 0.113s :: … gives this gate 1s …
timeout=1.5              rc=2 0.115s :: … gives this gate 1.5s …
timeout=1.6              rc=2 0.136s :: this line runs the WHOLE declared test surface `tests` …
timeout=30               rc=2 0.139s :: this line runs the WHOLE declared test surface `tests` …
```

Ohne `timeout` gibt es **keine** Fristen-Verweigerung; der Haken entscheidet unter dem gemessenen
Vorgabefenster (560 s − 1,5 s). Genau so sind heute **alle** neuen Registrierungen eingetragen:
`rig/timeouts.py` zählt dev-team 30 von 31, office-team 30 von 30, research-team 27 von 28 Einträge
ohne `timeout` — der neue `gate_test_scope`-Eintrag in allen drei Kits eingeschlossen. Die
Repo-Hälfte tut das Gegenteil und das ist die „Form", die das Item verlangt:

```
registration WITHOUT timeout: rc=2 0.125s :: [harness gate] this call could not be judged, because
this gate cannot know how long it may take: no entry in .claude/settings.json registers
'gate_test_scope.py' for tool 'Bash' with a `timeout`.
```

**Die Abweichung selbst trägt** — ich habe sie nachgemessen, nicht geglaubt:
`tools/provider_observations.json` → `hook_deadlines` enthält die Messung (2026-08-23,
claude.exe 2.1.239, zwei Rigs, zwei Sitzungen): `timeout: 5` bei 20 s Bedarf → Haken **getötet**,
`marker.txt` geschrieben, Nutzerkanal still. Und die wörtliche Ausführung von AC-2 macht die
ausgelieferte Regel rot; ich habe sie ausgeführt (`rig/ac2_literal.py apply`, 87 Einträge bekamen
`timeout: 120`):

```
FAILED tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default
… office-team PreToolUse(Bash|PowerShell): gate_test_scope.py names a window of 120s although it
  bounds nothing of its own, so the window can only ever kill it mid-decision
  (+ 14 weitere office-team-Zeilen, dazu dev-team und research-team)
```

**Zahlkorrektur:** der Bericht sagt „fünf der acht Office-Einträge". Gemessen sind es **mindestens
15 office-team-Zeilen** und praktisch jeder Eintrag aller drei Kits, der kein eigenes Kind
begrenzt. Die Schlussfolgerung wird dadurch stärker, nicht schwächer.

**Was zu tun ist:** der Lead entscheidet über die Abweichung (Item vs. gemessene Widerlegung); der
**Befund** ist der Satz im Docstring. Minimaler Fix: die Zeile umschreiben auf das, was gebaut ist
(„ein Fenster, das dieses Gate nicht beantworten kann, wird verweigert; ein FEHLENDES Fenster ist
nach `provider_observations.hook_deadlines` das richtige und wird unter dem gemessenen
Vorgabefenster beantwortet"), und AC-2 im Item auf denselben Stand bringen statt im Code auf AC-2
zu zeigen.

---

## F4 — `registered_window` widerspricht seinem Docstring, in Richtung ALLOW

`team-kits/*/hooks/_kernel.py:1003` behauptet:

> THE SMALLEST APPLYING ENTRY ANSWERS: one gate may be registered in several groups and any of them
> can be the one that is asked, so the shortest is the window it has to survive.

`:1028` tut etwas anderes: sobald **irgendein** zutreffender Eintrag kein `timeout` nennt, wird
`None` zurückgegeben — und `None` heißt 560 s. Gemessen am Piloten mit zwei Einträgen für dasselbe
Gate, einer bei 1,0 s, einer ohne:

```
entries running the gate: 2
mixed: one 1.0s + one with none    rc=2 0.225s :: this line runs the WHOLE declared test surface …
```

Also: kein Fristen-Refusal, Budget 558,5 s, obwohl derselbe 1,0-s-Eintrag allein als „nicht
beantwortbar" verweigert würde. Wird der Haken über den kurzen Eintrag gerufen, ist er tot und der
Aufruf durch. Heute latent (kein Kit-Eintrag nennt ein `timeout`), live am Tag, an dem einer es tut
— und `gate_pipeline` (1800 s) ist genau so ein Kandidat.

**Minimaler Fix:** `min` über die genannten Werte bilden und die `None` ignorieren, statt bei einem
`None` alles zu verwerfen.

---

## F5 — „ein Gate, das seine Regel nicht lesen kann, verweigert" gilt nur für einen JSON-Syntaxfehler

`.claude/hooks/gate_test_scope.py:102-122`, Docstring `:106-108`:

> An UNREADABLE declaration is a different answer — the file is there, so somebody meant this gate
> to decide, and a gate that cannot read its own rule refuses rather than waving the call through.

Gemessen über alle Zustände der Erklärung (`rig/decl_states.py`, Zeile
`python -B -m pytest tools/ -q`):

```
as shipped                 rc=2   this line runs the WHOLE declared test surface …
truncated json             rc=2   … present but could not be read …
a JSON array               rc=0   <ALLOWED>
a JSON array with content  rc=0   <ALLOWED>
a JSON string              rc=0   <ALLOWED>
a JSON number              rc=0   <ALLOWED>
null                       rc=0   <ALLOWED>
empty object               rc=0   <ALLOWED>
empty file                 rc=2   … could not be read …
surfaces not a list        rc=0   <ALLOWED>
threshold as a string      rc=2   this line runs the WHOLE declared test surface …
file removed               rc=0   <ALLOWED>
```

Der ausgelieferte Test (`test_gate5_says_nothing_where_a_project_declares_no_test_surface`,
`.claude/hooks/test_gates.py:6847`) pflanzt nur `b"{ not json"` und misst diese Klasse nicht.
Eingegrenzt durch H151 (die Erklärung ist ohnehin nicht geschützt), aber der Satz behauptet mehr,
als der Code baut.

**Minimaler Fix:** in `declaration()` auch dann verweigern, wenn der geparste Wert kein `dict` ist
oder `surfaces` vorhanden und keine Liste ist; die Zustandsliste im Test erweitern.

*(Die Kit-Hälfte antwortet hier umgekehrt — ein unparsbares `INV` wird übergangen, gemessen
`malformed declaration: rc=0` — aber das steht so in `_items`'s Docstring und ist damit eine
benannte Differenz, keine falsche Behauptung.)*

---

## F6 — der neue QS-Prozedurblock zerschneidet einen Bestandssatz

`team-kits/dev-team/skills/quality-engineer/SKILL.md:92-102`. Der ausgelieferte Rollentext liest
sich jetzt:

```
 92    ran 11 full pipelines + 43 pytest invocations). Generate the coverage report ONCE, then grep the report
 93    **That ONE full run says on the LINE that it is the delivery run.** …
 …
101    project is one where this discipline rests on you alone.
102    FILE for details — never rerun pytest to re-read the same numbers. …
```

„grep the report **FILE** for details" ist mitten durchgeschnitten. AC-2 verlangt die Regel „als
PROZEDUR, gemessen gegen den Kit-Text" — ein Einschub, der die umgebende Anweisung zerlegt, ist die
Gegenrichtung. **Minimaler Fix:** den Block hinter Zeile 105 setzen (nach dem Ende des Satzes).

---

## F7 — zwei Sätze, die diese Runde selbst falsch gemacht hat, stehen unverändert

* `tools/test_hooks.py:2883-2884` (Docstring `_own_child_limit`): „`_compat.HOOK_DEADLINE_SECONDS`
  is the budget the hooks give themselves and **nothing enforces it**."
* `tools/provider_observations.json` → `hook_deadlines.what_follows_for_the_kits`: „A hook that
  spends the time INSIDE its own process is bounded by **nothing here**; that is what the harness's
  own construction closes … and **what no kit hook does**."

Seit dieser Runde tut es jeder Kit-Haken: `_kernel.start_the_deadline` setzt einen Wachhund-Thread
neben die Entscheidung (`os._exit(2)`), rot-zuerst von mir belegt (siehe unten). Der neue Kommentar
in `_kernel.py:947-951` **zitiert** genau diesen Satz als aktuellen Stand. Beide Dateien liegen in
`tools/**` und damit im `allowed_scope`. **Minimaler Fix:** beide Sätze auf den Stand nach dieser
Runde bringen und im `_kernel.py`-Kommentar aus dem Zitat einen Zeiger („die Messung, die diese
Konstruktion veranlasst hat") machen.

---

## Rot zuerst — eigene Reproduktionen (Pflicht 5a)

Alle in meiner Kopie, Defekt eingesetzt, rot gesehen, zurückgesetzt (`rig/mutate.py`).

| Mutation | Testknoten | Ergebnis |
|---|---|---|
| AC-2: `threading.Thread(target=watch…).start()` entfernt | `tools/test_hooks.py::test_a_gate_that_runs_past_its_window_mid_decision_refuses_instead_of_being_killed` | **rot**: `AssertionError: (2.401…, '', '')`, `returncode=0` — also ALLOW, die gefährliche Richtung |
| AC-1: `recorded[1] == "pass"` deaktiviert | `test_gate5_refuses_the_second_full_run_of_a_round_but_not_after_findings[pass-2]` | **rot**: „after a 'pass' full run (EVD-0084) the next one came back rc=0" |
| AC-1: `_handed_to` durch die alte Lesart über die ganze Stufe ersetzt | `.claude/hooks/test_gates.py -k gate5` | **rot**: 8 failed, 9 passed |
| AC-3: `for rule in (C1, C2, C3)` → `(C1, C2)` | `test_the_built_app_is_judged_on_c1_c2_c3…`, `test_each_planted_violation…[C3-*]` | **rot**: 3 failed, 4 passed |
| **Gegenprobe B1**: `-v`, `--tb`, `--durations` als „Verengung" erklärt | `-k declared_narrowing_option` | **grün geblieben** (2 passed) — der Stolperdraht kann nicht scheitern |

---

## Angriff auf den Fix — was gehalten hat (gemessen)

Alle als echte Hook-Prozesse, `rig/g5.py` / `rig/batch.py` (Repo) und `rig/pilot.py` (Kit-Pilot).

**AC-1, `_handed_to` und die Volllauf-Eigenschaft — rc 2 in jedem dieser Fälle:**
`python -B -m pytest tools/ -q`, `python -m pytest`, `py -3 -m pytest .`, `pytest --rootdir tools`,
`python -m pytest -q tools`, `timeout 600 python -m pytest tools/`, `cd tools && python -m pytest`,
`python -B -m pytest "tools"`, `python -m pytest tools/ tools/test_x.py`,
`pytest tools .claude/hooks/test_gates.py`, `python -m pytest tools/ > out.txt`,
`… 2>&1 | tee log.txt`, `… ; echo done`, `bash -c '…'`, `sh -c "…"`, `echo tools | xargs python -m pytest`,
`nohup python -m pytest tools &`, `python -m pytest --pyargs tools`, `-p no:randomly`, `-q -x tools`,
`-n auto`, `--maxfail=1`, `python3 -m pytest tools`, `python -m pytest tools\`, `.\tools`, `./tools/`,
`pytest`, `pytest -q`, `pytest .`, `pytest /`, PowerShell `python -B -m pytest tools/ -q` und
`& python -m pytest tools`.

**Auswahl passiert (rc 0), wie verlangt:** `pytest tools/ -k test`, `-m slow`, Unterpfad, Knoten-Id,
`--collect-only`, `grep -rn pytest tools/`, `ls tools`, `echo pytest tools`.

**Lieferpräfix:** gegen den **Kernel** geprüft, nicht per Muster —
`_harness.resolve_references` + `_harness.automata`, und `_full_run_evidence` liest
`_harness.project_state(root).iter_active_items("EVD")` mit `run_scope: full`. Gemessen:
`DELIVERY_RUN=TSK-9999 …` rc 2 („leads no open work"), `$env:DELIVERY_RUN="…"; …` rc 2 mit
derselben Begründung, `DELIVERY_RUN=<offenes Item> …` rc 0 am Piloten, danach mit einem über
`kernel.cli evidence --run-scope full --result pass` erfassten Datensatz rc 2, mit `--result fail`
rc 0. Ein `DELIVERY_RUN=` in einem `echo`-Stadium hebt nichts an (rc 2 gemessen).

**AC-3 (eigene Messung, echtes Chromium, echt bedienter Build `frontend/dist`):** die sechs
gepflanzten Verletzungen und der saubere Build, jede Regel einzeln ausgewertet (`rig/ac3_cross.py`):

```
CLEAN                                             expected=None fired=-       other=[]
C1 contrast under the WCAG floor                  expected=C1   fired=C1      other=[]
C2 mouse-clickable, keyboard-unreachable          expected=C2   fired=C2      other=[]
C2 a positive tabindex                            expected=C2   fired=C2      other=[]
C2 a focus nobody can see                         expected=C2   fired=C2,C3   other=[]
C3 an animation that ignores reduced motion       expected=C3   fired=C3      other=[]
C3 no :focus-visible rule at all                  expected=C3   fired=C3      other=[]
```

Fünf von sechs treffen ausschließlich ihre eigene Regel; der eine Doppeltreffer ist sachlich
richtig (die Fassung entfernt die `:focus-visible`-Regel und ist damit wirklich C2 **und** C3).
Office liefert die Datei nicht aus — das braucht keinen `KIT_SPECIFIC_SCRIPTS`-Eintrag, weil die
Spiegelregel (`tools/test_hooks.py:2822 ff.`) Anwesenheit ausdrücklich nicht fragt.

**AC-4 (Median aus fünf echten Prozessen, `rig/repo_deadline.py`):**

```
a line naming no runner       rc=0 median 0.111s
an ordinary line naming it    rc=0 median 0.144s
a refused full run            rc=2 median 0.134s
a delivery line               rc=2 median 0.232s
```

gegen ein registriertes Fenster von **120 s** (`.claude/settings.json`, `Bash|PowerShell`,
`timeout: 120`) — 0,1 bis 0,2 %. Kit-Hälfte mit einem Invariantenspeicher **an der
ausgelieferten Obergrenze** (6 Items, 12,0 MB, `rig/ac4_cost.py`):

```
ordinary shell line      rc=0  0.330s  0.167s  0.189s
line naming the runner   rc=0  0.174s  0.157s  0.156s
full run (refusal)       rc=2  0.193s  0.168s  0.169s
delivery run             rc=0  0.475s  0.258s  0.226s
```

Der Kopf-Scan trägt also. Sein fail-closed-Rückfall ist echt: eine Erklärung, deren `scope:`-Zeile
hinter den ersten 4096 Byte steht, wird trotzdem gefunden (rc 2 gemessen). Projekt ohne UI /
Projekt mit Sekunden-Suite: beide zahlen nichts (`judged_above_seconds` unter der erklärten Dauer →
rc 0 gemessen; ohne `frontend/dist` startet kein Browser).

---

## Paket-Hygiene (Pflicht d/e/f)

* **Patch** `_round-scratch/TSK-0121/stream-testgate.patch`: `git apply --check` **rc 0** gegen
  einen aus 75a00d1 materialisierten Baum; auch `--3way` rc 0. 23 Dateien, 3622 +, 12 −.
  **Keine** `team-kits/*/VERSION`-Hunks (die Stempel dev `2026.09.04-4`, office `-6`,
  research `-4` liegen im Arbeitsbaum, nicht im Patch). **0 CR-Bytes** im Patch und in allen 23
  berührten Dateien.
* **Spiegel:** `gate_test_scope.py` sha256 `f3ace285474f8194…` ×3, `_kernel.py` md5 gleich ×3,
  `kit_browser_checks.py` sha256 `1a7077452cf49a46…` dev = research. Beide vom Bericht genannten
  sha256-Präfixe stimmen.
* **`test_gates.py`:** ein eigener Block ab `:6606` (+373 Zeilen) **plus drei kleine Bestandsstellen**
  (`build_project`, der Registrierungs-Kommentar, `EXPECTED_TOOLS`, `_refusable`). Das sind
  Tabellen, die jedes registrierte Gate nennen müssen; sie sind in der Nahttabelle des Protokolls
  benannt. Für den Merge mit G4-2/G4-4 sind genau diese vier Stellen das Konfliktrisiko, nicht der
  Block.
* **`_kernel.py` ist keine Naht** — TSK-0122 führt `team-kits/*/hooks/_*.py` in seinem
  **forbidden_scope**, TSK-0123 und TSK-0125 führen `team-kits/*/hooks/**` dort. Befund N-1 des
  Umsetzers ist damit gegenstandslos; ich korrigiere ihn hier.
* **`session_status.py` / `_routine.py` unverändert** (nicht im `git status` des Arbeitsbaums).
* **H151–H153:** im reservierten Bereich, im aktuellen Format (Tabellenzeile + Langabschnitt mit
  Mechanismus / gemessener Kette / Urteil), jede genannte Prüfung existiert (alle 9 im Paket
  genannten Testnamen lösen auf; `grep -rn test_run_scope` ist leer). Die Löcher-Richter laufen
  grün (`-k "hole_list or claims_in_its_own_prose or reference_to_a_measurement"`: 8 passed).
  **Aber:** H152s Urteil trägt die Behauptung aus B1 und ist damit inhaltlich falsch.
* **Naht an G4-3:** Abschnitt 8 des Protokolls nennt die drei Verfassungszeilen wörtlich mit
  Zeilennummer; die beiden angekündigten roten Tests sind wirklich rot:
  `tools/test_shortening_net.py::test_every_registered_hook_is_anchored_in_its_kits_constitution`
  und `::test_the_inventory_the_constitution_presents_is_the_registrations_it_ships` (2 failed,
  34 deselected).
* **Scope:** alle 26 berührten Dateien liegen im `allowed_scope`. Kein `project_memory/`-Schreiben
  ausser `staging/TSK-0121/`.

---

## Ausdrückliche Negativbefunde

**Gemessen und in Ordnung:** Registrierung von Gate 5 auf `Bash|PowerShell` mit `timeout: 120` und
in `EXPECTED_TOOLS` (beide Richtungen grün); `_harness.Deadline` greift auch für Gate 5 (Eintrag
ohne `timeout` → Verweigerung mit Satz, gemessen); Volllauf-Erkennung über alle 33 oben genannten
Schreibweisen; Auswahl passiert; Lieferpräfix gegen den Kernel; zweiter Volllauf gegen die
Evidence des Kernels, `fail` öffnet wieder; Erklärung fehlt → nicht beurteilt; Schwelle als
Datenwert wirksam; Kit-Gate ×3 byte-gleich und am gebauten Piloten als Prozess bestätigt;
Kopf-Scan-Kosten am Speicherlimit; C1/C2/C3 gegen den bedienten Build mit echtem Chromium; Spiegel
dev/research byte-gleich; Patch sauber; `session_status.py`/`_routine.py` unberührt;
`_kernel.py` kollidiert mit keinem anderen Strom; die vier Rot-zuerst-Reproduktionen oben.

**Nicht gemessen (offen benannt):**
* die volle Suite — gehört nach DEC-0050 in den Merge, nicht in die Prüfung.
* office- und research-Piloten für die Kit-Hälfte (nur ein dev-team-Pilot gebaut; die drei
  `gate_test_scope.py` sind byte-gleich, `_kernel.py` ebenfalls, das Verhalten sollte identisch
  sein — belegt ist es nur für dev-team).
* Codex-Gegenstück `.codex/hooks.json` (Fristensemantik dort ist auch in
  `provider_observations.json` als „not measured" geführt).
* ob ein **archiviertes** `EVD` mit `run_scope: full` den zweiten Volllauf wieder freigibt
  (`_full_run_evidence` liest nur `iter_active_items`), und ob ein zweites offenes Item als Präfix
  einen zweiten Volllauf derselben Runde kauft — beides gelesen, nicht gefahren.
* der PowerShell-Zweig der QS-Rollenzeile (`$env:DELIVERY_RUN=…`) wird vom „gehobenen" Test nicht
  ausgeführt, nur der POSIX-Zweig.
* die restlichen 21 der 25 vom Umsetzer gemeldeten Rot-zuerst-Läufe (vier selbst reproduziert).
* Laufzeit der Gates unter echter Parallel-Last (BUG-0033) — nicht Sache dieses Stroms.

---

## Verdikt

**FAIL, und B1 wie B2 blockieren die Runde.** Das Paket ist handwerklich stark: die
Volllauf-Eigenschaft ist als Eigenschaft und nicht als Schreibweisenliste gebaut, sie hält gegen 33
Schreibweisen, das Lieferpräfix hängt am Kernel und nicht an einer selbst geschriebenen Datei, die
Kit-Hälfte ist ×3 byte-gleich und am gebauten Piloten belegt, C1/C2/C3 erreichen wirklich die
gebaute App, die Kosten sind gemessen und winzig, der Patch ist sauber, und das Protokoll korrigiert
sogar einen eigenen Fehlbefund. Gescheitert ist es an der einen Stelle, die das Item selbst als
gefährlich markiert: der **unvermeidbaren Aufzählung**. `options_that_narrow` enthält sieben
Einträge, die nichts verengen, der Stolperdraht, der genau das fangen soll, kann nicht scheitern,
und die Löcherliste behauptet trotzdem „lässt nie einen Volllauf durch" — `pytest tools/ --ff` ist
rc 0 und kostet 3465 s. Dazu vergleicht `_covers` Zeichenketten statt Pfade, so dass `..`, `tools/.`
und ausgerechnet der **absolute** Pfad — die Schreibweise, zu der Gate 1 den Aufrufer zwingt — am
Gate vorbeigehen, in beiden Hälften. Beide Löcher sind zwei kleine Änderungen weit vom Fix entfernt;
mit ihnen, mit der Korrektur der drei falschen Prosa-Stellen (B1, F3, F5), dem `min`-Fix in
`registered_window`, dem zerschnittenen QS-Satz und den zwei von dieser Runde überholten
Messungssätzen ist AC-1 und AC-2 abnehmbar. AC-3 und AC-4 sind es jetzt schon. Die AC-2-Abweichung
selbst („jeder Eintrag nennt ein timeout") ist keine Nachlässigkeit, sondern eine belegte
Widerlegung des Items — sie gehört auf den Tisch des Leads, nicht in die Nacharbeit des Umsetzers,
und der Umsetzer hat sie eher unter- als überverkauft.
