## Rolle `quality-engineer` — Recherchebericht (read-only, nichts im Repo geändert)

Gelesen: `docs/HARNESS_V2_SPEC.md` II.2 + II.11, `team-kits/dev-team/skills/quality-engineer/SKILL.md`, die Schwesterrollen `research-team/skills/reviewer/SKILL.md` und `dev-team/skills/project-auditor/SKILL.md`, `team-kits/*/constitution/AGENTS.md` §2/§6, sowie die real ausführenden Teile: `team-kits/dev-team/templates/repo/scripts/quality.py`, `.../kit_browser_checks.py`, `.../kit_checks.py`, `team-kits/dev-team/hooks/gate_test_coverage.py`.

---

## 1. Was das SKILL heute wirklich gut macht

Das ist kein generisches QA-Dokument. Fast jede Regel trägt eine Narbe, und das ist seine Stärke.

**a) Es kennt den Unterschied zwischen „gelaufen" und „bewiesen".** Der Evidence-Vertrag ist die beste Stelle der Datei:

> „**`--result` is the verdict the merge gate reads.** It is `pass` or `fail` and nothing else; a run that could not decide is a `fail` whose summary says why (a partial run is not merge evidence)."

Und weiter: „your `--result` is the claim and your `--summary` is prose about the claim, so the reference is the only part of the record someone else can re-read." Das ist genau die Trennung, an der die meisten QA-Prozesse scheitern.

**b) Es hat den „Green Skip" schon erkannt** — die zentrale Frage dieser Recherche steht bereits als Satz da:

> „A real_run/e2e **SKIPPED for environment reasons** (docker daemon off) is **NOT a pass** — report it as BLOCKED, never as green."

**c) Delivery-Freshness (R6).** „every 'verified in the real browser' claim MUST name the origin (URL) AND the served bundle/asset hash" — und das ist die *eine* Stelle, wo eine SKILL-Regel tatsächlich mechanisiert wurde (`kit_browser_checks.py`, `_served_index_hash` vs. `_file_hash`). Das ist das Vorbild für alles Weitere in diesem Bericht.

**d) Flake-Protokoll mit Statistik statt Wiederholungsgefühl.** „isolate the suspect test and run IT 10–30× in a loop + `--lf` for the rest, and record the repetition statistics" — deckt sich mit Googles Praxis (Rerun nur der verdächtigen Tests, nicht der Suite).

**e) Kostendisziplin als QA-Regel.** „run the FULL suite + e2e exactly ONCE right before your PASS verdict … NEVER edit code or tests during the run (that would invalidate the verdict)". Der zweite Halbsatz ist methodisch sauber und in kaum einem Lehrbuch so explizit.

**f) Der Satz, der QA von „Testrunner" trennt:** „**Plan the tests (you are the sole owner of test completeness).**" plus die Abgrenzung in `AGENTS.md` §6: „The Architect contributes test STRATEGY … QA owns test COMPLETENESS".

**g) Bugfix-Regel ist bereits mutationsähnlich gedacht:** „require a **regression test** that FAILS on the pre-fix code and PASSES after". Das ist — für genau einen Mutanten, nämlich den echten Bug — exakt das Prinzip des Mutation Testing.

---

## 2. Lücken gegen publizierte Standards

### L1 — Die zentrale Überbehauptung: „coverage per source area" existiert nicht

SKILL Schritt 4 fordert: „**coverage ≥ threshold globally AND per source area** (src/, frontend/src/ …)".

Real:
- `quality.py::check_python` führt aus `pytest -q --cov=<tgt> --cov-fail-under=<thr>` mit `tgt = "src"` — **eine** globale Zahl über **ein** Verzeichnis.
- `gate_test_coverage.py` prüft ausschließlich die *Existenz* mindestens einer Testdatei pro Bereich („source area 'frontend/' has code but no UI/unit tests"). Eine einzige `foo.test.ts` erfüllt den ganzen Frontend-Bereich.
- `check_node` hat **überhaupt keinen** Coverage-Floor — und schlimmer:
  ```python
  rc, out = run_npm(["npm","run","-s","test","--","--run","--coverage"], cwd=fe)
  if rc != 0:
      rc, out = run_npm(["npm","run","-s","test"], cwd=fe)   # Fallback OHNE coverage
  ```
  Ein Frontend, dessen Coverage-Lauf rot ist, wird still ohne Coverage nachgeschossen und gilt dann als grün.

Damit behauptet das SKILL eine Durchsetzung, die es nicht gibt — genau die Klasse Defekt, die deine eigene Lessons-Notiz als Muster 3 führt („Comments promised protection the code did not implement").

### L2 — Statement- statt Branch-Coverage

`--cov=` ohne `--cov-branch`. coverage.py selbst: *„Statement coverage would show all lines of the function as executed. But the `if` was never evaluated as false"* — [coverage.readthedocs.io/branch.html](https://coverage.readthedocs.io/en/latest/branch.html). Eine 80-%-Statement-Zahl über KI-generierten Code mit vielen `if`-Zweigen ist strukturell zu optimistisch.

### L3 — Die Prozentzahl selbst ist der falsche Floor

Google Testing Blog, *Code Coverage Best Practices*: 60 % „acceptable", 75 % „commendable", 90 % „exemplary"; die Gewinne oberhalb eines Punktes sind **logarithmisch**, und „more important than the percentage … is human judgment over the actual lines of code (and behaviors) that aren't being covered". Empfohlen wird stattdessen **Coverage auf geändertem Code** — [testing.googleblog.com/2020/08/code-coverage-best-practices.html](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html). Werkzeuge dafür sind publiziert und trivial: [`diff-cover --fail-under=N`](https://github.com/Bachmann1234/diff_cover), bzw. Codecovs Trennung von *project*- und *patch*-Status — [docs.codecov.com/docs/commit-status](https://docs.codecov.com/docs/commit-status).

### L4 — Kein Verfahren gegen „ein Test, der nicht scheitern kann"

Das ist laut deiner eigenen Erfahrung der häufigste Defekt des Harness. Publizierte Technik dagegen, in aufsteigender Kosten-Reihenfolge:

1. **Assertionsfreie Tests, statisch** — `expect-expect` in [eslint-plugin-vitest](https://github.com/vitest-dev/eslint-plugin-vitest/blob/main/docs/rules/expect-expect.md) / [eslint-plugin-jest](https://github.com/jest-community/eslint-plugin-jest/blob/main/docs/rules/expect-expect.md): „ensures that there is at least one expect call made in a test". Dazu `valid-expect`, `no-conditional-expect`, `no-disabled-tests`, `no-focused-tests`.
2. **Test Smells als Forschungsgegenstand** — Ursprungskatalog van Deursen et al. / Meszaros („Assertionless Test", „Conditional Test Logic"); für Python maschinell umgesetzt in **PyNose** (ASE 2021), 18 Smells, 94 % Precision / 95,8 % Recall — [arxiv.org/abs/2108.04639](https://arxiv.org/abs/2108.04639), [github.com/JetBrains-Research/PyNose](https://github.com/JetBrains-Research/PyNose). Einschränkung: PyNose ist ein PyCharm-Plugin, keine CLI — als Gate nicht direkt brauchbar, als Regelkatalog sehr wohl.
3. **Mutation Testing** — der einzige Standard, der die Frage „kann dieser Test überhaupt rot werden?" *beweisend* beantwortet. Google, *Practical Mutation Testing at Scale* (IEEE TSE 2022), 24.000 Entwickler, 1.000+ Projekte: praktikabel nur mit drei Einschränkungen — **inkrementell nur auf geändertem Code im Review**, **Mutantenfilterung**, **Operatorauswahl nach Historie**; unproduktive Stellen („arid nodes") werden gar nicht erst mutiert — [arxiv.org/pdf/2102.11378](https://arxiv.org/pdf/2102.11378), [research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/). Werkzeug für TS/JS mit genau diesem Modus: [Stryker `--incremental`](https://stryker-mutator.io/docs/stryker-js/incremental/) plus `thresholds.break`.
4. **Skips und xfails.** pytest liefert bei *allen* Tests übersprungen **Exit-Code 0** — [docs.pytest.org/en/stable/reference/exit-codes.html](https://docs.pytest.org/en/stable/reference/exit-codes.html). Die SKILL-Regel „SKIPPED ist kein Pass" ist damit heute reine Prosa gegen eine Toolchain, die das Gegenteil signalisiert.
5. **Testreihenfolge.** Order-Dependency ist eine der Hauptursachen in der kanonischen Flaky-Taxonomie (Luo, Hariri, Eloussi, Marinov, FSE 2014, 201 Fix-Commits in 51 Projekten) — [dl.acm.org/doi/10.1145/2635868.2635920](https://dl.acm.org/doi/10.1145/2635868.2635920). Ein Test, der nur wegen des Zustands eines Vorgängertests grün ist, ist ebenfalls „ein Test, der nichts prüft".

### L5 — Risikobasierter Testentwurf ist nicht benannt

Das SKILL sagt „make sure EVERY stack in use is actually covered" — das ist Abdeckung nach *Ort*, nicht nach *Risiko*. Publizierte Bezugsrahmen:
- **ISO/IEC/IEEE 29119-2** ist explizit risikobasiert aufgebaut — [iso.org/standard/56736.html](https://www.iso.org/standard/56736.html); **29119-4:2021** liefert den benennbaren Technikkatalog (Äquivalenzklassen, Grenzwerte, Entscheidungstabellen, Zustandsübergänge, kombinatorisch) — [iso.org/standard/79430.html](https://www.iso.org/standard/79430.html).
- **NIST SP 800-142** liefert die *empirische* Begründung für kombinatorisches Testen: „66 % der Medizingeräte-Fehler wurden durch einen einzigen Variablenwert ausgelöst, 97 % durch ein oder zwei interagierende Variablen" — [nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-142.pdf](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-142.pdf). Das ist genau das Argument gegen die Palettenmatrix, die das SKILL bereits verbietet — und gleichzeitig das Argument *für* Paarweise-Abdeckung an den zwei, drei Stellen, wo sie zählt.
- **ISO/IEC 25010:2023** (Produktqualitätsmodell, 9 Charakteristiken; „Usability" → **Interaction Capability**, „Portability" → **Flexibility**, **Safety** neu) — [iso.org/standard/78176.html](https://www.iso.org/standard/78176.html). Das ist die publizierte Liste, gegen die man „mehr als: es läuft" überhaupt abhaken kann.

### L6 — Accessibility: der Anspruch ist da, die Messung fehlt vollständig

Das SKILL fordert semantisches HTML, `focus-visible`, vollständigen Keyboard-Pfad, WCAG AA, `prefers-reduced-motion`. **Im gesamten Repo kommt „axe" oder „lighthouse" nicht ein einziges Mal vor** (verifiziert per grep über `team-kits/`). Es gibt also null mechanische A11y-Prüfung — obwohl `kit_browser_checks.py` bereits einen echten Chromium gegen den echten Production-Build fährt. Der teure Teil ist gebaut, der billige fehlt.

Zur Größenordnung, ehrlich und **umstritten**: axe-core beansprucht im eigenen README „on average **57 %** of WCAG issues automatically" — [github.com/dequelabs/axe-core](https://github.com/dequelabs/axe-core), Studiengrundlage [deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/](https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/). Das ist eine **Herstellerangabe, gemessen an der Zahl gefundener Befunde**; die klassischen 20–30 % beziehen sich auf die Abdeckung von **WCAG-Erfolgskriterien**. Beide Zahlen können stimmen und meinen Verschiedenes. Für die Rolle heißt das: axe-grün ist ein *Floor*, nie ein Urteil.

Was den Rest strukturiert, ist publiziert:
- **W3C ACT Rules Format 1.1** (W3C Recommendation) — das Format unterscheidet ausdrücklich vollautomatische, halbautomatische und manuelle Regeln — [w3.org/TR/act-rules-format-1.0/](https://www.w3.org/TR/act-rules-format-1.0/), Status-Meldung [w3.org/news/2026/…act-rules-format-1-1…](https://w3.org/news/2026/accessibility-conformance-testing-act-rules-format-1-1-is-now-a-w3c-recommendation/). Das ist wörtlich die GATE/SKILL-Linie, die dieses Harness selbst zieht — von einem Standardisierungsgremium vorgezeichnet.
- **WCAG-EM 1.0** — Scope definieren, repräsentative Stichprobe wählen, prüfen, berichten — [w3.org/TR/WCAG-EM/](https://www.w3.org/TR/WCAG-EM/).
- Regulatorisch für dich relevant: **BFSG** seit 28.06.2025 in Kraft, verweist über EN 301 549 auf **WCAG 2.1 AA** — [twobirds.com/…/germany-ready-for-the-eaa…](https://www.twobirds.com/en/insights/2025/germany/germany-ready-for-the-eaa-european-accessibility-act-implementation-entering-into-force-on-28-june-2). Für ein Consumer-Frontend ist A11y damit keine Geschmacksfrage mehr.

### L7 — Die visuelle Fidelity-Prüfung hat keine benannte Methode

„render the built view … and judge VISUALLY" ist ein Auftrag ohne Verfahren, und darum genau die Stelle, an der ein Modell „sieht gut aus" produziert. Publizierte Form dafür: **Heuristische Evaluation** nach Nielsen/Molich mit Schweregrad-Skala 0–4 — [nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/). Das macht aus einem Eindruck eine Liste aus (verletzte Heuristik, Ort, Beleg, Schweregrad) — vergleichbar über Gates hinweg und geeignet als Evidence-Artefakt.

### L8 — Testpyramide fehlt als Begriff, und das ist teilweise okay

Das SKILL regelt Stack-Abdeckung und „no mock-only", aber nie das Verhältnis. Der klassische Bezug ist Fowlers *Practical Test Pyramid*; Googles Beitrag ist eher „Just Say No to More End-to-End Tests" (E2E-Tests sind flaky und verstecken kleine Bugs in großen). Aber: die Pyramide als feste Zahlenrelation ist **umstritten** — web.dev diskutiert sie offen als eine Form unter mehreren (*Pyramid or Crab?*) — [web.dev/articles/ta-strategies](https://web.dev/articles/ta-strategies). Siehe Abschnitt 5.

### L9 — `INV.check.ref` bleibt manuell

Das SKILL sagt es selbst: „The state validator does not do it yet (that duty is deferred to the pytest/CI integration), so a missing test is invisible to every gate until you name it." Spec II.2 fordert dagegen ausdrücklich: „Der State-Validator (fail-closed) prüft EXISTENZ und Sammelbarkeit des referenzierten Tests". Das ist keine Lücke gegen einen externen Standard, sondern gegen die eigene Spezifikation — und sie ist mechanisch, weil `pytest --collect-only -q <nodeid>` genau diese Frage beantwortet.

---

## 3. GATE oder SKILL — je Lücke, mit Fehlerbild

Regel des Harness: nur, wessen Scheitern ich beschreiben kann, darf ein Gate sein.

| # | Lücke | Einstufung | Was geprüft wird / warum Judgement |
|---|---|---|---|
| **G1** | A11y-Automat fehlt (L6) | **GATE** in `kit_browser_checks.py` | `@axe-core/playwright` auf der bereits gebooteten Preview-Seite. **Fehlerbild:** `FAIL frontend a11y (axe) — 3 violations, impact serious/critical: color-contrast (button.primary, 3.1:1 < 4.5:1), button-name (2 Elemente ohne zugänglichen Namen), landmark-one-main`. Degradiert wie die Browser-Smoke: axe fehlt → `warn`, nie stiller Pass. |
| **G2** | Keyboard-Pfad / Fokus-Sichtbarkeit (L6) | **GATE**, eigener Playwright-Schritt | N-mal `Tab`, `document.activeElement` protokollieren. **Fehlerbild A (Trap):** `nach 40 Tabs verlässt der Fokus <div id="modal"> nicht — kein Keyboard-Ausgang`. **Fehlerbild B (unsichtbar):** `focus-visible fehlt: bei button.primary sind outline/box-shadow/border im fokussierten und unfokussierten Zustand byte-gleich`. **Fehlerbild C (unerreichbar):** `Element mit onClick ist in keiner Tab-Position — mouse-only action`. Alle drei sind computed-style- bzw. DOM-Vergleiche, keine Geschmacksurteile. |
| **G3** | Assertionsfreie Tests (L4.1) | **GATE** in `kit_checks.py` | JS/TS: `expect-expect` + `no-disabled-tests` + `no-focused-tests` über die vorhandene ESLint-Stufe. Python: AST-Walk über `tests/**`, jede `test_*`-Funktion ohne `assert`, `pytest.raises`, `unittest`-`assert*` oder eine als assertion-tragend deklarierte Helper-Funktion. **Fehlerbild:** `FAIL assertion-free test — tests/test_gate.py::test_blocks_foreign_write hat keine Assertion (der Test kann nicht rot werden)`. Wichtig, Lesson 4 deiner Notiz: der Check muss den **geparsten AST** lesen, nicht den Dateitext — sonst erfüllt ein Kommentar „# assert …" die Regel. |
| **G4** | Skip-/xfail-Buchhaltung (L4.4) | **GATE** in `quality.py` | `--junitxml` einlesen: (a) jeder `skipped` ohne Reason-String → FAIL; (b) Skip-Quote über Budget (Default z. B. 2 %, Knopf in `testing_guidelines.yaml`) → FAIL; (c) namentlich deklarierte kritische Marker (`real_run`, `e2e`, `browser`) übersprungen → FAIL. **Fehlerbild:** `FAIL suite proved less than it claims — 14/220 Tests skipped (6,4 % > 2 %), darunter der einzige Test mit @pytest.mark.real_run; pytest hat trotzdem Exit 0 gemeldet`. Das mechanisiert wörtlich die Regel, die das SKILL heute nur behauptet. |
| **G5** | Branch- + Diff-Coverage statt Prozentglaube (L2/L3) | **GATE** in `quality.py` | `--cov-branch` einschalten und den globalen Floor **beibehalten** (nicht anheben), zusätzlich `diff-cover --fail-under=<diff_threshold>` gegen den Merge-Base. **Fehlerbild:** `FAIL diff coverage 41 % < 80 % — 37 von 63 geänderten Zeilen ungetestet: src/pricing.py 88-104 (der neue Rabattzweig), frontend/src/CartTotal.tsx 22-31`. Das ist die Zahl, die Reviewer glauben können, weil sie über 63 Zeilen redet und nicht über 40.000. |
| **G6** | Frontend-Coverage-Floor + Fallback-Loch (L1) | **GATE**, Korrektur in `check_node` | Den Fallback ohne `--coverage` entfernen und `--coverage.thresholds.lines=<thr>` erzwingen. **Fehlerbild:** `FAIL frontend tests — vitest coverage 12 % < 80 % (bisher: derselbe Lauf galt als grün, weil quality.py nach dem roten Coverage-Lauf still ohne Coverage nachgeschossen hat)`. |
| **G7** | `INV.check.ref` unaufgelöst (L9) | **GATE** im State-Validator | `pytest --collect-only -q <nodeid>` je INV. **Fehlerbild:** `FAIL INV-0007 unverified — check.ref "tests/test_ui_inventory.py::test_nav_snapshot" ist nicht sammelbar (Datei existiert, Testname nicht). Merge blockiert.` Das ist keine Erfindung, das ist Spec II.2 wörtlich. |
| **G8** | Testreihenfolge-Abhängigkeit (L4.5) | **GATE**, aber im *einen* Verdikt-Lauf | `pytest -p no:cacheprovider --random-order --random-order-seed=<commit-hash-prefix>`, Seed protokolliert. **Fehlerbild:** `FAIL order dependency — Suite grün in Dateireihenfolge, rot mit Seed 4711: tests/test_ledger.py::test_balance schlägt fehl, wenn test_import nicht vorher lief`. Deterministisch reproduzierbar, weil der Seed vom Commit abgeleitet ist — sonst wäre das Gate selbst flaky. |
| **G9** | Mutation Score auf dem Diff (L4.3) | **GATE nur für TS/JS, SKILL für Python** | TS/JS: Stryker `--incremental` + `thresholds.break`. **Fehlerbild:** `FAIL mutation score on changed files 38 % < 60 % — 11 überlebende Mutanten, u. a. src/cart.ts:44 (>= → >) und src/cart.ts:51 (Rückgabe durch null ersetzt) werden von keinem Test bemerkt`. Für Python bewusst **kein** Gate: mutmut/cosmic-ray sind deutlich unreifer als PIT/Stryker und die Laufzeit ist der Killer — dort bleibt es Prüftechnik im SKILL für die Kernmodule. |
| **S1** | Risikobasierter Entwurf (L5) | **SKILL** | Welche Technik zu welchem Risiko passt, ist Urteil. Verlangt werden soll die *Form*: je `SR`-Komponente mit `criticality: high` eine benannte Technik aus 29119-4 (Grenzwerte / Entscheidungstabelle / Zustandsübergang / paarweise) plus ein Satz, warum. Ein Gate darauf würde nur Vokabeln zählen. |
| **S2** | ISO-25010-Charakteristiken (L5) | **SKILL** | Im Review-Evidence benennen, welche der 9 Charakteristiken der PR berührt und welche davon *nicht* geprüft wurden. Ehrliche Lücke > erfundene Vollständigkeit. Nicht mechanisierbar. |
| **S3** | Die 43–70 %, die axe nicht sieht (L6) | **SKILL**, ausdrücklich als „nicht enforced" markiert | Manuelle Prüfliste nach WCAG-EM-Stichprobenlogik: Fokus**reihenfolge** sinnvoll (nicht nur vorhanden), Alt-Text-**Qualität**, Fehlermeldungen nennen die Abhilfe, Reflow bei 320 px ohne horizontales Scrollen, Screenreader-Ansage der Statusänderungen. Der SKILL-Text muss sagen: **axe-grün ist der Floor, nicht das Urteil** — sonst ersetzt G1 die Prüfung, statt sie zu tragen. |
| **S4** | Fidelity-Review ohne Methode (L7) | **SKILL** | Heuristische Evaluation nach NN/g als Form: pro Befund verletzte Heuristik + Ort + Beleg + Schweregrad 0–4; alles ≥ 3 ist ein `fail`. Die Guardrails („default palette + theme only, ONCE per gate — no pixel-diffing") bleiben unverändert stehen. |
| **S5** | Flakiness-Ursache statt Wiederholungszahl (L4.5) | **SKILL** | Das 10–30×-Protokoll ergänzen um: klassifiziere die Ursache nach der Luo-Taxonomie (async wait / concurrency / order dependency / resource leak) und schreib sie ins Test-Evidence. Ohne Ursache wiederholt sich der Flake nach dem Merge. |

**Zwei Dinge, die im SKILL-Text selbst korrigiert gehören, unabhängig von jedem Gate:**
1. Der Satz „coverage ≥ threshold globally AND per source area" muss weg oder als *Policy, nicht enforced* markiert werden — heute ist er schlicht falsch.
2. Wo das SKILL eine Prüfung fordert, die kein Gate trägt, gehört das dazugesagt. Das ist die Regel des Harness, und der `project-auditor`-SKILL macht es an anderer Stelle bereits vorbildlich („So the ROUTINE part … is policy nobody enforces. Report it").

---

## 4. Die drei wirkungsstärksten Ergänzungen, in Reihenfolge

### Platz 1 — G1 + G2: axe + Keyboard-Pfad in `kit_browser_checks.py`
**Warum zuerst:** Es ist die einzige Lücke, bei der das Teure schon existiert. Der Chromium läuft, der Production-Build wird geladen, der Freshness-Hash wird verglichen — es fehlen die zwanzig Zeilen, die axe injizieren und die Tab-Schleife fahren. Und es ist das Einzige in dieser Liste, das der User **selbst sehen** kann: „ich kann mit der Tastatur nicht zum Absenden-Button" ist für einen Nicht-Entwickler nachprüfbar, „Mutation Score 38 %" nicht. Zusätzlich regulatorisch gedeckt (BFSG seit 28.06.2025).
**Kosten:** eine Dev-Dependency (`axe-core` + `@axe-core/playwright`, oder python-seitig `axe-playwright-python`), ca. 40–60 Zeilen in einer kit-eigenen Datei, die das Scaffold ohnehin bei jedem Update überschreibt. Laufzeit +1–3 s auf einer bereits geöffneten Seite. Ein Knopf mehr in `testing_guidelines.yaml` (`a11y: { impact_threshold: serious, routes: [...] }`). Risiko: Legacy-Frontends werden beim Einschalten sofort rot — deshalb Impact-Schwelle konfigurierbar und initial auf `critical`.

### Platz 2 — G3 + G4: assertionsfreie Tests und Skip-Buchhaltung
**Warum zweiter:** Das ist die direkte Mechanisierung deines meistgesehenen Defekts, und beide Checks sind statisch bzw. lesen nur eine JUnit-XML — kein zusätzlicher Testlauf, keine Laufzeit. G4 hebt außerdem eine bereits geschriebene SKILL-Regel („SKIPPED is NOT a pass") aus der Prosa in die Ausführung; das ist die billigste Ehrlichkeitsverbesserung im ganzen Harness.
**Kosten:** `--junitxml` an den einen Verdikt-Lauf hängen, ~80 Zeilen in `kit_checks.py`, zwei Knöpfe (`skip_budget`, `critical_markers`). Die einzige echte Arbeit ist die AST-Variante für Python — und die *muss* per `ast`-Modul erfolgen, nicht per Regex, sonst baust du den Fehler aus Lesson 4 nach. Beim Einschalten Aufräumbedarf in Bestandsprojekten; deshalb mit Allowlist-Datei starten, die schrumpfen muss.

### Platz 3 — G5 + G6: Diff-Coverage + Branch-Coverage, Frontend-Floor geschlossen
**Warum dritter, nicht erster:** Es ist die konzeptionell richtigste Änderung — sie ersetzt eine Zahl, die niemand glaubt, durch eine, über die man reden kann — aber sie verändert das Verhalten jedes bestehenden Projekts und braucht einen Merge-Base-Begriff, den `quality.py` heute nicht hat (es kennt kein Git). G6 dagegen ist ein Zweizeiler und sollte sofort mitlaufen: den Fallback-Lauf ohne `--coverage` ersatzlos streichen.
**Kosten:** `diff-cover` als Dev-Dependency, `--cov-branch` + XML-Report in `check_python`, Merge-Base-Ermittlung (`kit_checks._run_git` existiert bereits und kann das). Wichtig: den globalen Floor dabei **nicht** anheben — Google zeigt, dass die Gewinne oberhalb ~70 % logarithmisch sind; der Zugewinn kommt aus dem Diff-Floor und aus Branch statt Statement, nicht aus einer größeren Zahl.

*Bewusst nicht in den Top 3:* G9 (Mutation Testing). Es ist die stärkste Antwort auf „kann dieser Test scheitern?", aber es kostet Laufzeit in genau dem Lauf, den das SKILL aus guten Gründen auf **einmal pro Verdikt** deckelt, und für Python fehlt die Werkzeugreife. Erst wenn G3/G4 die billigen Fälle abgeräumt haben, lohnt sich der teure.

---

## 5. Was gegen populäre Empfehlungen für diese Rolle spricht

**a) „Nehmt Visual Regression Testing / Screenshot-Diffs."** Nein — und das Harness hat schon recht. Das SKILL verbietet es ausdrücklich („no pixel-diffing, no palette matrix (a real run burned 3 gate rounds on a 160-combo sweep)"), und die Praxisliteratur bestätigt das Muster: Anti-Aliasing, Subpixel-Rendering und Font-Smoothing erzeugen Falschpositive, bis Teams die Initiative binnen Wochen aufgeben; Text-Rendering ist die häufigste Ursache flakiger Visual Tests — [shakacode.com/blog/flaky-visual-regression-tests-and-what-to-do-about-them/](https://www.shakacode.com/blog/flaky-visual-regression-tests-and-what-to-do-about-them/), [vitest.dev/guide/browser/visual-regression-testing](https://vitest.dev/guide/browser/visual-regression-testing). Das Harness hat den besseren Ersatz bereits erfunden: **berechnete** Uniformitätsassertionen („one computed heading size across all views, equal card heights per row, spacing from the token scale") plus **UI-Inventar-Snapshot** über die DOM-Struktur. Das prüft dieselbe Eigenschaft ohne Pixel. Ausbauen, nicht ersetzen.

**b) „Erhöht die Coverage-Schwelle auf 90 %."** Widerspricht Googles eigener publizierter Praxis: 90 % ist dort „exemplary", nicht Norm, und die Zuwächse sind logarithmisch; entscheidend ist menschliches Urteil über *welche* Zeilen fehlen. Eine hohe globale Zahl ist außerdem genau der Mechanismus, der bei euch schon einmal versagt hat — `gate_test_coverage.py` dokumentiert es selbst: „The real run shipped a frontend with 0 tests, hidden behind a high global backend coverage number." Eine höhere Schwelle hätte das nicht verhindert; ein Diff-Floor hätte es.

**c) „Führt Mutation Testing über die ganze Codebasis ein."** Google nennt das explizit lange als intraktabel: „the sheer number of mutants … has hindered adoption as an industry standard". Praktikabel wurde es erst inkrementell, gefiltert und operator-selektiv. Wer den vollen Lauf einführt, bekommt eine Gate-Laufzeit, die das Ein-Lauf-Budget des SKILLs sprengt, plus überwiegend unproduktive Mutanten. Wenn, dann nur diff-scoped.

**d) „axe-grün heißt barrierefrei."** Die 57 % sind eine Herstellerzahl über **Befundvolumen**; die konservativen 20–30 % messen **WCAG-Erfolgskriterien**. axe-core sagt zudem selbst, es liefere „incomplete"-Ergebnisse, wo Sicherheit nicht herstellbar ist. G1 ist ein Boden, kein Urteil — und das muss im SKILL-Text stehen, sonst ersetzt das neue Gate genau die manuelle Prüfung, die es tragen soll. Das ist die realistischste Art, wie dieses Gate schaden könnte.

**e) „Haltet euch an die Testpyramide 70/20/10."** Die Pyramide als Ratio ist umstritten; Google selbst redet über Test-*Größe* und Hermetizität, nicht über Anzahlverhältnisse, und web.dev diskutiert offen Alternativformen. Für dieses Harness ist die Pyramide ohnehin die falsche Achse: eure durchgesetzte Regel ist „**jeder Stack und jede Source-Area ist getestet**" plus „**no mock-only für user-/runtime-kritische Pfade**" — das ist eine Abdeckungs- und Realitätsregel, keine Verhältnisregel, und sie hat empirisch bei euch mehr gefangen (0 Frontend-Tests, jsdom-grüne Tests mit zwei echten Browser-Bugs).

**f) „ISO 29119 als Prozessrahmen übernehmen."** Ehrlich ausgewiesen: der Standard ist in der Testing-Community **umstritten** — die „Stop 29119"-Petition der ISST wirft ihm vor, die kontextgetriebene Schule zu ignorieren und Testen zu über-formalisieren ([ipetitions.com/petition/stop29119](https://www.ipetitions.com/petition/stop29119), Hintergrund [sdtimes.com/applause/software-testing-schism/](https://sdtimes.com/applause/software-testing-schism/)). Meine Empfehlung ist deshalb bewusst schmal: **nur den Technikkatalog aus 29119-4 als Vokabular** übernehmen (damit „ich habe getestet" zu „ich habe Grenzwertanalyse auf den Rabattstufen gefahren" wird), **nicht** das Prozess- und Dokumentationsmodell aus 29119-2. Letzteres würde eure eigene Regel „bloated rule files get ignored" (AGENTS.md Kopf) unmittelbar verletzen.

**g) „Ein weiterer Prozentwert löst das Problem."** Die Lehre aus deiner eigenen Lessons-Notiz Muster 1 („Enumerations keep producing findings; definitions stop") gilt auch hier: ein Coverage-Floor ist eine Aufzählung von Zeilen, die zufällig ausgeführt wurden. Die *Definition*, die aufhört Befunde zu produzieren, lautet: **ein Test zählt, wenn er bei einer Änderung am geprüften Verhalten rot wird.** G3 (keine Assertion), G4 (nicht ausgeführt), G8 (nur wegen Reihenfolge grün) und G9 (Mutant überlebt) sind vier mechanische Annäherungen an genau diese eine Definition — und sie sind der Grund, warum sie in dieser Reihenfolge stehen.