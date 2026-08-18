## 1. Was die SKILL.md heute gut macht

Datei: `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\frontend-developer\SKILL.md` (59 Zeilen)

Vier Dinge sind überdurchschnittlich — sie stammen erkennbar aus echten Fehlläufen und sind deshalb konkret statt generisch:

- **Mockup-as-Base statt Nachkoloration.** „take the mockup's **markup + CSS as the BASE** and wire the app logic INTO it, so the build is faithful by construction. **NEVER recolor/retrofit an existing layout**" — das ist die richtige Kausalrichtung. Genau diese Regel verhindert das „AI-generated"-Ergebnis auf der Implementierungsseite, weil sie dem Modell verbietet, das Layout selbst zu erfinden.
- **jsdom-green is NOT browser-green.** Die Regel benennt `crypto.randomUUID` / `navigator.clipboard`, verlangt EINEN Helper mit Fallback — und ist tatsächlich mechanisch hinterlegt (`check_frontend_pitfalls` in `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\kit_checks.py`). SKILL-Text und Gate sagen dasselbe; das ist die Ausnahme, nicht die Regel.
- **Delivery freshness.** „a 'verified in the real browser' claim MUST name the origin (URL) AND the served bundle/asset hash" — und `kit_browser_checks.py` vergleicht `sha256(dist/index.html)` gegen den ausgelieferten Body. Ein Anspruch mit gebautem Beweis.
- **Staged testing als Kostendisziplin** („run `scripts/quality.py` at most ONCE right before handing off"). Selten explizit, hier richtig.

Schwach ist die Testzeile: „Write **component/unit tests** … `*.test.*` / `*.spec.*`". Das ist eine Aussage über *Dateinamen*, nicht über Testqualität — und `gate_test_coverage.py` prüft exakt das: die **Existenz** einer Datei, die auf `.test.`/`.spec.` matcht. Eine einzige triviale Datei erfüllt das Gate.

---

## 2. Lücken gegen publizierte Standards

| # | Standard / Quelle | Was in der SKILL fehlt |
|---|---|---|
| A | Testing-Library Query-Priorität: `getByRole` > `getByLabelText` > … > `getByTestId` („The user cannot see (or hear) these, so this is only recommended for cases where you can't match by role or text") — https://testing-library.com/docs/queries/about/ | Kein Wort zur Query-Wahl. Ein Test, der nur `data-testid` kennt, kann eine unbedienbare UI grün melden. |
| B | WCAG 2.2 AA (W3C Recommendation) — https://www.w3.org/TR/WCAG22/ ; Playwright + `@axe-core/playwright` — https://playwright.dev/docs/accessibility-testing | Kein Kontrast-, Label-, Namens- oder Fokus-Kriterium. Der bestehende Browser-Smoke prüft nur „mount nicht leer + Konsole leer". |
| C | ARIA APG, „A role is a promise" / „No ARIA is better than bad ARIA" — https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/ | Nichts zu Tastaturverhalten hinter übernommenen Rollen (Tabs/Menu/Combobox). |
| D | Design Tokens Format Module 2025.10 (erste stabile Fassung, **kein** W3C-Standard) — https://www.designtokens.org/tr/drafts/format/ ; Durchsetzungs-Präzedenz: `stylelint-declaration-strict-value` — https://github.com/AndyOGo/stylelint-declaration-strict-value | Die Designerin liefert semantische Tokens (light+dark, WCAG AA) — nichts verlangt oder prüft, dass die Implementierung sie *benutzt*. |
| E | Performance-Budgets — https://web.dev/articles/incorporate-performance-budgets-into-your-build-tools ; `size-limit` — https://github.com/ai/size-limit ; Lighthouse-CI `resource-summary:script:size` — https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md | **Es gibt kein Budget.** `check_frontend_build_config` verbietet nur, `chunkSizeWarningLimit` zu *erhöhen* — eine Zahl setzt niemand, und Vites Warnung lässt `npm run build` mit rc=0 durch. Das Gate verbietet die Vertuschung, nicht den Zustand. |
| F | Core Web Vitals: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1, **75. Perzentil echter Ladevorgänge** — https://web.dev/articles/vitals | Keine Performance-Akzeptanz. Aber: siehe Punkt 5 — der naive Einbau wäre falsch. |
| G | `prefers-reduced-motion` (WCAG 2.3.3) und `:focus-visible` (WCAG 2.4.7, 2.4.11 neu in 2.2) | Die Designer-SKILL schreibt beides als „Base reset (mandatory)" vor; auf der Frontend-Seite prüft nichts, ob es im Build ankommt. |
| H | UI-Inventar-Regression. Die Verfassung behauptet sie bereits: „Removing/replacing/renaming a VISIBLE UI element is ALWAYS a CR (**the UI inventory snapshot test fails without one**)" (`AGENTS.md` §7) | **Diesen Test gibt es nicht.** Weder Kit-Template noch Gate erzeugen ihn. Das ist genau das Muster „Kommentar behauptet nicht gebauten Schutz". Der passende Mechanismus existiert seit Kurzem: Playwright `expect(...).toMatchAriaSnapshot()` mit committeter `.aria.yml` — https://playwright.dev/docs/aria-snapshots |
| I | Frontend-Coverage-Schwelle | `quality.py` erzwingt `coverage_threshold()` nur für Python; der Node-Zweig prüft nur `rc == 0` von `npm test`. |

---

## 3. GATE oder SKILL — je Lücke

**GATE (mechanisch prüfbar, mit beschreibbarem Fehlschlag):**

- **B — axe im bestehenden `browser_smoke`.** Prüft: nach `page.goto` `axe.run()` gegen die Tags `wcag2a, wcag2aa, wcag22aa`; **fail** bei `violations` mit `impact ∈ {serious, critical}`, `incomplete` nur als warn. Fehlschlag lautet z. B.: *„axe: `color-contrast` — .btn-secondary hat 2,9:1 gegen #1b1b20, gefordert 4,5:1 (3 Knoten, http://localhost:52133/)"*. Ehrliche Decke: Deque misst rund **57 %** der real gefundenen Barrierefreiheitsprobleme als automatisch erfassbar (https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/) — das Gate ist ein Boden, nie ein Beweis.
- **D — Farbliterale außerhalb der Token-Datei.** Prüft: alle Dateien aus dem vorhandenen Walker `_frontend_sources()` (er erfasst bereits `.css`, `.tsx`, …) auf `#rgb`/`#rrggbb`/`rgb(`/`hsl(`/`oklch(`, ausgenommen genau eine Token-Datei und die Schlüsselwörter `transparent|currentColor|inherit`. Fehlschlag: *„frontend/src/components/Card.module.css:14 kodiert `#2b2b31` fest — Farbwerte leben nur in frontend/src/styles/tokens.css; benutze `var(--surface-2)`"*. Das ist die mechanisch prüfbare Scheibe von „hält sich an den visuellen Vertrag".
- **E — Bundle-Budget.** Prüft nach dem bereits laufenden Build die gzip-Summe von `frontend/dist/assets/*.js` und den größten Einzel-Chunk. Fehlschlag: *„initial JS 412 kB gzip > Budget 250 kB (größter Chunk vendor-a1b2.js, 301 kB) — code-splitten; das Anheben von `chunkSizeWarningLimit` ist bereits verboten"*.
- **G — Motion/Fokus-Präsenz.** Prüft: enthält irgendeine Frontend-CSS `transition:`/`animation:`, muss mindestens ein `@media (prefers-reduced-motion` existieren; enthält der Build interaktive Elemente, mindestens ein `:focus-visible`. Fehlschlag: *„12 `transition:`-Deklarationen, kein einziger `prefers-reduced-motion`-Block — WCAG 2.3.3 und der verpflichtende Base-Reset der Design-Revision"*. Nahezu keine Falsch-Positiven.
- **H — ARIA-Snapshot des UI-Inventars.** Prüft: `toMatchAriaSnapshot` gegen committete `.aria.yml`. Fehlschlag: *„Rolle `button` mit Namen ‚Account' fehlt im Accessibility-Tree von `/` — sichtbare Elemente entfernt man nur per CR (§7)"*. Diff ist lesbarer YAML-Text, nicht ein Bild.
- **I — Coverage-Schwelle Frontend** (schwach, aber prüfbar): fail, wenn `frontend/` Tests hat, aber weder `coverage.thresholds` in der Vite-Config noch ein Äquivalent deklariert ist.

**SKILL (Urteil, darf nicht als erzwungen auftreten):**

- **A — Query-Priorität.** Welche Query korrekt ist, ist Urteil (Canvas, dynamischer Text, Zahlenformate sind legitime `testid`-Fälle). Als harter Gate produziert das Falsch-Positive. Als **warn** vertretbar: eine Testdatei mit ≥1 `getByTestId` und **null** `getByRole|getByLabelText` — das ist eine schwächere, verteidigbare Behauptung.
- **C — ARIA-Rollen als Versprechen.** axe prüft *Anwesenheit* von Attributen, nicht ob `role="tab"` die Pfeiltastennavigation implementiert. Reiner SKILL-Text mit APG-Verweis.
- **F — Core Web Vitals als Produktkriterium** (siehe Punkt 5).
- Kritische Flows: SKILL-Text — aber er soll auf den **schon vorhandenen** Mechanismus zeigen: ein `INV`-Item trägt `check: {kind: test, ref: <pytest-nodeid|pfad::test>}`, und der State-Validator prüft **fail-closed** Existenz und Sammelbarkeit dieses Tests (Spec II.2). Damit wird jede vom Frontend vorgeschlagene Invariante automatisch gate-fähig, ohne ein neues Gate zu bauen. Das ist der stärkste ungenutzte Hebel im Harness.

**Harness-spezifische Randbedingung für jeden Vorschlag oben:** Neue Stellschrauben dürfen *keine* Konfigurationsdatei brauchen. `coding_guidelines.yaml` ist in V2 aufgelöst, `_knob_hint()` in `kit_checks.py` sagt wörtlich, die Knöpfe hätten „no home", und `gate_write_scope` verweigert ohnehin jeden Schreibzugriff unter `project_memory/`. Jedes hier vorgeschlagene Gate ist deshalb mit eingebautem Default formuliert (Token-Datei per Konvention, Budget als Kit-Default) — kein `testing_guidelines.yaml`-Eintrag.

---

## 4. Die drei größten Hebel, in Reihenfolge

**1. axe-core in `kit_browser_checks.browser_smoke()` hängen.**
Kosten: ~35 Zeilen in `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\kit_browser_checks.py`; keine neue Python-Abhängigkeit nötig (`axe.min.js` per `page.add_script_tag` injizieren, `page.evaluate("axe.run()")`), Laufzeit 1–3 s. Die gesamte Infrastruktur — Produktionsbuild, `vite preview`, Chromium, ehrliche warn-Degradation ohne Playwright — steht bereits. Bestes Verhältnis im ganzen Bericht.

**2. Token-Konformität (Farbliterale) + Bundle-Budget im selben Commit.**
Kosten: ~60 bzw. ~50 Zeilen in `kit_checks.py`, beide wiederverwenden vorhandene Bausteine (`_frontend_sources()`, `_more()`, das bereits erzeugte `frontend/dist`). Keine Laufzeitkosten. Das Bundle-Budget ist der billigste Einzelcheck des Berichts und schließt eine Lücke, die das bestehende `chunkSizeWarningLimit`-Verbot bisher nur *verdeckt* — es verbietet die Vertuschung, ohne je eine Zahl zu setzen.

**3. ARIA-Snapshot als das UI-Inventar-Gate.**
Kosten: höher — braucht den Playwright **Test-Runner** im Projekt (Node) neben dem heutigen Python-Smoke, ein Scaffold-Template `frontend/tests/inventory.spec.ts`, eine committete `.aria.yml`-Baseline und eine Entscheidung, wer sie beim legitimen CR aktualisiert. Grob ein halber Tag Kit-Arbeit. Trotzdem oben in der Liste, weil `AGENTS.md` §7 diesen Test **bereits als existent behauptet** — bis dahin ist die CR-Pflicht für sichtbare Elemente reine Policy mit einem Gate-Versprechen davor.

---

## 5. Was gegen populäre Empfehlungen für diese Rolle spricht

**Core Web Vitals als Gate-Schwelle wären ein Kategorienfehler.** CWV sind **Feldmetriken am 75. Perzentil echter Ladevorgänge** aus CrUX (https://web.dev/articles/vitals). Ein frisch gescaffoldetes Projekt hat keine Nutzer und keinen CrUX-Eintrag. **INP ist im Labor grundsätzlich nicht messbar** — es braucht echte Interaktionen; Lighthouse führt INP deshalb gar nicht und benutzt TBT als Proxy, der über große Populationen korreliert, aber pro Seite ein schlechter Prädiktor ist (https://web.dev/articles/tbt, https://web.dev/articles/lab-and-field-data-differences). Ein Gate „INP ≤ 200 ms" im Kit wäre exakt das Muster „Behauptung ohne gebauten Schutz". Ehrliche Aufteilung: **CLS** ist die eine CWV-Größe, die im Labor stabil ist (Layout, nicht Netzwerk) → GATE gegen 0,1, ausdrücklich als *lab* beschriftet. **LCP** lokal nur als warn. **INP gar nicht** — es gehört als Feldmessung in die `acceptance_criteria` des PR, also zum PM.

**Pixel-basierte Visual Regression gehört nicht ins Kit.** Vitests eigene Dokumentation nennt visuelle Tests „inherently unstable across different environments" und benennt Font-Rendering als Hauptursache, dazu GPU-Treiber, headless/headed und Browserversionen (https://vitest.dev/guide/browser/visual-regression-testing). Das dokumentierte Endstadium ist Falsch-Positiv-Ermüdung: Baselines werden blind bestätigt, dann abgeschaltet. In einem Harness, das Windows-Entwicklung und Linux-CI mischt, wäre das ein Gate, das Vertrauen zerstört statt schafft. Der Zweck — „ist etwas Sichtbares verschwunden?" — wird vom ARIA-Snapshot (Rollen und Namen, kein Rendering) vollständig und stabil abgedeckt; die *ästhetische* Abweichung deckt bereits die Fidelity-Review der Designerin in Phase 3 ab, und die ist Urteil, kein Diff.

**Storybook / Component-Driven Development ist hier die falsche Empfehlung.** CDD ist keine Norm eines Standardgremiums, sondern ein Manifest aus dem Storybook/Chromatic-Umfeld (https://www.chromatic.com/blog/component-driven-development/). Wichtiger: Das Harness hat den Komponentenkatalog schon — die eingefrorene, self-contained `design/revisions/DSN-nnnn.rNN.html` ist per Spec II.6 der *verbindliche* visuelle Vertrag. Storybook danebenzustellen erzeugt eine **zweite visuelle Wahrheit**, was `design_ref` als bindenden Vertrag aushöhlt und gegen §2.1 („NO ad-hoc … files") arbeitet, plus eine erhebliche Abhängigkeits- und Dateibudget-Last. Storybook 9 hat mit dem a11y-Test-Runner (`parameters.a11y.test: 'error'`) durchaus eine echte Fähigkeit (https://storybook.js.org/docs/writing-tests/accessibility-testing) — aber `@axe-core/playwright` auf dem bereits laufenden Preview-Server liefert davon den größten Teil zu einem Bruchteil der Kosten.

**Und eine Einschränkung gegen meine eigene Empfehlung A:** `eslint-plugin-jsx-a11y` wird oft als Accessibility-Gate verkauft. Die Maintainer selbst schränken ein, dass statische Analyse Prop-Werte vor der Laufzeit nicht kennt und das Plugin mit `@axe-core/react` kombiniert gehört (https://github.com/jsx-eslint/eslint-plugin-jsx-a11y). Als *Scaffold-Default in der ESLint-Config* sinnvoll und billig — als eigenständiges Gate nicht ausreichend.