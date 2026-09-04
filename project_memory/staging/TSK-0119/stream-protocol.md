# TSK-0119 — Strom E „Design-Gates" (FR-0077 primär, FR-0078 gebündelt)

Umsetzer-Protokoll. Arbeitsbaum: `C:/Offline Repos/v2-testbed/_worktrees/g3-design` (Branch
`g3/design`, von `feat/harness-v2` bei `e45c0ca`). Scratch ausschließlich unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0119/`. Kein Commit, kein Push, keine Installation
in den globalen Speicher.

---

## 1. Vorgefunden (gelesen, bevor eine Zeile geschrieben wurde)

| Frage | Was der laufende Stand sagt |
|---|---|
| Wo entsteht ein Design-Entwurf? | `product-designer` stagt eine selbstständige HTML unter `project_memory/staging/<task-id>/`; der Kernel friert sie als `design/revisions/DSN-nnnn.rNN.html` ein. Das eingefrorene File IST der Vertrag, den der Frontend umsetzt und QA vergleicht. |
| Was prüft heute jemand daran? | Nichts Mechanisches. `gate_design_sighted` (PreToolUse `AskUserQuestion` + `SubagentStop`) fragt genau eine Frage: hat jemand gerendert. `kit_design_render.py` rendert und schreibt `review/render.json`. `kit_design_system_check.py` prüft ein eingelegtes Design-System-Bündel, ist ausdrücklich kein Gate. |
| Was sagt die Wunschliste §1c? | Wörtlich „NICHT gebaut" für C1/C2/C3 (axe, Tastaturpfad, `prefers-reduced-motion`/`:focus-visible`) und B2/B3 (Farbliterale). Bedingung für den Bau: der Text darf nie „barrierefrei" melden. |
| Was sagt §1a? | Rangfolge selbst ist Urteil → SKILL. Nachweisbar machen sie: genau EIN primäres Ziel je View, ausgezeichnet im eingefrorenen Vertrag. |
| Wie steht es um `timeout` in `settings/settings.json`? | Die gebaute Regel ist NICHT „jede Registrierung trägt eine Frist". `tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default` verlangt das Gegenteil: eine Frist ist nur erlaubt, wenn der Haken eine eigene Kind-Grenze UNTER dem Fenster hat; ein Haken ohne eigene Grenze, der eine Frist nennt, ist ein Befund. Gemessen: einziger Eintrag mit Fenster ist `gate_pipeline` (1800 s über einer eigenen Kind-Grenze von 1500 s). |
| Wer liefert welche Skript-Datei? | `kit_design_render.py` und `kit_design_system_check.py`: nur `dev-team`. `kit_browser_checks.py`, `kit_checks.py`, `quality.py`: `dev-team` UND `research-team`, **byte-gleich** (sha256 gemessen, Tabelle unter 6). |

**Der Widerspruch im Auftrag, benannt statt befolgt:** der Auftragstext verlangt „jede neue
Haken-Registrierung trägt einen `timeout`". Die im Baum laufende, gemessene Regel verlangt das
Gegenteil (Zeile 5 oben). Aufgelöst wurde er dadurch, dass **keine neue Registrierung entsteht** —
siehe 2.

---

## 2. Plan, und der verworfene Weg in einer Zeile

**Gebaut:** die mechanisch entscheidbaren Hälften laufen als **ausgeliefertes Skript** im
Nutzerprojekt, im schon vorhandenen `kit_design_render.py`, am **gerenderten DSN-Entwurf** — nicht
als neuer PreToolUse-Haken und nicht am gebauten App.

Drei Gründe, jeder gemessen oder aus einer aktiven Entscheidung:

1. **`DEC-0056` (b) verbietet den Haken.** Ein Gate wird nur für eine Fehlklasse gebaut, für die ein
   Fall gemessen vorliegt. Der einzige gemessene Fall dieser Gegend ist `BUG-0076` (ungesehener
   Entwurf) — den trägt `gate_design_sighted` bereits. Für „ein Entwurf mit Kontrastfehler erreicht
   den Nutzer" gibt es keinen Vorfall in diesem Repo.
2. **Ein Haken, der einen Browser startet, ist eine Frist-Wette.** Nach der gebauten Fenster-Regel
   dürfte er nur dann eine Frist nennen, wenn er eine eigene Kind-Grenze darunter hat; Playwright
   gibt keine, die der AST-Leser dieser Regel sehen könnte. Ohne Frist läuft er gegen das
   Standardfenster (frühester gemessener Kill: 560 s), und ein getöteter Haken ist ein Durchlass.
3. **Der Entwurf ist die frühere und billigere Stelle.** Er ist der Vertrag, den der Build umsetzt;
   ein Kontrastfehler dort erreicht jede View des Builds. Und der Renderer bootet Chromium ohnehin —
   genau das Kosten-Argument der Synthese, nur eine Phase früher.

**Verworfener Weg, eine Zeile:** C1/C2/C3 in das schon gebootete `browser_smoke()` von
`kit_browser_checks.py` legen, wie §1c es vorschlägt — verworfen, weil diese Datei `dev-team` und
`research-team` byte-gleich ausliefern und `research-team/**` im `forbidden_scope` dieses Items
steht, die Prüfung dort erst NACH dem Einfrieren zuschlägt und ihr Subjekt ohne `npm` + `vite build`
gar nicht existiert, also auch nicht rot messbar wäre (steht als `H139`).

---

## 3. Nahttabelle

| Naht | Wem gehört sie | Was dieser Strom getan hat |
|---|---|---|
| `docs/POST_V2_WISHLIST.md` (§1a, §1c, Löcherliste + Übersichtstabelle) | geteilt, alle Ströme hängen an | §1c-Zeilen C1/C2/C3 und B2/B3 auf den gebauten Stand gebracht, Item-Zeilen von FR-0077/FR-0078 ergänzt, `H138`/`H139`/`H140` samt Übersichtszeilen angehängt; in Nacharbeit 1 dazu `H145`/`H146`, die der Koordinator für Strom E reserviert hat. **Belegt sind genau H138–H140 und H145/H146**, keine anderen Nummern. Konfliktrisiko im Merge: Anhang am Dateiende + fünf Tabellenzeilen nach `H125`. |
| `tools/test_hooks.py` | geteilt (Generation 2: Ströme I und K) | **NICHT angefasst.** Die neuen Tests liegen in einer neuen Datei `tools/test_design_conformance.py`, gerade um diese Naht zu meiden. |
| `tools/constitution_section_pins.json` + `docs/reviews/phase0-disposition.md` | geteilt (jeder, der eine gepinnte Datei ändert) | Der `hooks/ENFORCEMENT.md`-Abschnitt „1. What each mechanism refuses" wurde neu gepinnt (`python tools/pin_constitution_sections.py --write --note "…"`); das erzeugt eine Journalzeile in der Disposition. Ein zweiter Strom, der eine gepinnte Datei ändert, erzeugt eine zweite Zeile — Merge-Konflikt möglich, Auflösung ist beide Zeilen zu behalten. |
| `team-kits/*/VERSION` | geteilt | `dev-team` provisorisch auf `2026.09.03-4` gestempelt (Nacharbeit 1). Der Merge stempelt neu. |
| `team-kits/dev-team/agents/product-designer.md` | Strom D / verboten hier | **Nahtsatz, siehe 9.** |
| `team-kits/dev-team/skills/project-manager/SKILL.md` | Strom D / verboten hier | **Nahtsatz, siehe 9.** |
| `team-kits/dev-team/skills/frontend-developer/SKILL.md` | nicht in `allowed_scope` | Die Konvention `data-view`/`data-primary-action` erreicht den Frontend heute nur über den eingefrorenen Vertrag. Wer sie im Build erzwingen will, braucht diese Datei — benannt, nicht geschrieben. |
| `team-kits/dev-team/templates/repo/scripts/kit_browser_checks.py`, `kit_checks.py`, `quality.py` | `dev-team` + `research-team`, byte-gleich | **NICHT angefasst** (`H139`). |
| Spiegelregel / `KIT_SPECIFIC_HOOKS` | `tools/test_hooks.py` | **Kein Eintrag nötig, gemessen:** `kit_design_render.py` liefert nur `dev-team`, und `_assert_mirrored` vergleicht ausschließlich die Kopien der Kits, die einen Namen liefern. Die dev-Exklusivität der Design-Schleife trägt bereits `DESIGN_LOOP_EXEMPT` in `tools/test_hooks.py` samt Grund für `research-team`; `test_the_design_loop_ships_where_a_draft_is_judged_by_its_LOOK` läuft grün. |

**Befund gegen den Schnitt (DEC-0062 (5)):** der `allowed_scope` dieses Items nennt
`kit_browser_checks.py`, der `forbidden_scope` nennt `team-kits/research-team/**` — und die beiden
schließen einander aus, weil dev und research diese Datei byte-gleich ausliefern. Der Schnitt hat
diese Kollision nicht als Naht benannt. Folge: die BUILD-Hälfte von FR-0077 ist nicht gebaut
(`H139`).

---

## 4. FR-0077 — Abnahmezeile

**Gebaut.** `kit_design_render.py` lädt jeden gestagten Entwurf nach den Screenshots ein zweites Mal
(breitestes konfiguriertes Viewport) und misst am **gerenderten DOM**:

| Hälfte | Was gemessen wird, und woran |
|---|---|
| **C1** (statt axe) | Kontrast jedes Elements mit eigenem sichtbarem Text: `getComputedStyle().color`, komponiert über den ersten deckenden Hintergrund der Ahnenkette; WCAG-2.2-Schwellen 4.5:1 / 3:1 (groß = ≥24 px, oder ≥18,66 px bei Gewicht ≥700). Text über Bild/Verlauf/halbdurchsichtiger Schicht → `NOT DECIDABLE`, weder Befund noch bestanden. |
| **C2** | Echte `Tab`-Drücke auf der echten Seite. Drei Bilder: (a) ein fokussierbares Element, das `Tab` nie erreicht; (b) ein erreichtes Element, das fokussiert **pixelgleich** aussieht wie unfokussiert (zwei geklippte Screenshots mit 8 px Rand, byte-verglichen); (c) ein Element mit `cursor: pointer`, das in keiner Tab-Ordnung liegt. Dazu `tabindex > 0`. |
| **C3** | Wirkung statt Präsenz: animiert die Seite überhaupt etwas (computed `transition-duration`/`animation-duration` > 0), wird dieselbe Datei in einem Kontext mit `reduced_motion: "reduce"` geladen und muss dort **nichts** mehr animieren. Zusätzlich Präsenz mindestens einer `:focus-visible`-Regel im CSSOM, sobald es überhaupt Fokussierbares gibt. |
| **B2** | Farbliterale außerhalb des Token-Blatts: über CSSOM (inkl. `@keyframes`-Schritten), `style`-Attribute und — seit Nacharbeit 1 — Präsentationsattribute (`<rect fill="#f00">`). |

**Definitionen statt Aufzählungen** (Hausregel, und hier der Kern der Arbeit):

- *Farbliteral*: kein Regex-Zoo und keine Notationsliste. Ein Wert ist ein Literal, wenn (1)
  `CSS.supports('color', v)` gilt, (2) er kein `var(` enthält, (3) er **kein CSS-weites
  Schlüsselwort** ist — gefragt als `CSS.supports('border-collapse', v)`, denn genau ein CSS-weites
  Schlüsselwort nimmt jede Eigenschaft an —, (4) er unter zwei verschieden geerbten Farben **gleich
  auflöst** (das trennt ihn von `currentColor`/`inherit`) und (5) seine Alpha nicht 0 ist. Damit
  sind `#rgb`, `#rrggbb`, `rgb()`, `hsl()`, `oklch()`, benannte Farben und alles Künftige eine
  Regel, nicht sechs.
- *Token-Blatt*: keine Selektorliste (`:root`, `[data-theme=dark]`). Erlaubt ist ein Literal an
  genau einer Stelle: als Wert einer **Custom Property**. Damit sind Theme-Blöcke, Media-Queries
  und projekteigene Schreibweisen ohne Aufzählung abgedeckt.
- *In der Tab-Ordnung*: `el.tabIndex`, die eigene Zahl des DOM — nie eine Tag-Liste. Genau daran
  wurde die erste Fassung gemessen falsch: mit der Tag-Liste
  (`a[href], button, input, …`) galt `<a href tabindex="-1">` als „Bedienelement, alles gut", und
  der Fall blieb still. Mit `tabIndex` ist er ein Befund.
- *Fokus sichtbar*: in **Pixeln**, nicht an byte-gleichen computed styles, wie C2 der Synthese es
  vorschlägt. Gemessen: mit `a:focus { outline: none }` verschiebt Chromium `outline-offset` von
  `0px` auf `1px` — die computed styles sind verschieden, auf dem Schirm ist nichts, und die von
  der Recherche vorgeschlagene Regel schweigt. Eigener Testfall.

**Rot zuerst** (`tools/test_design_conformance.py`, jede Verletzung EINZELN in eine sonst saubere
DSN gepflanzt, das Skript als **Prozess** in einem Projekt außerhalb des Repos):

| Gepflanzte Verletzung | rc | Satz, auf den der Test besteht |
|---|---|---|
| Kontrast unter der Schwelle | 3 | `where 4.5:1 is required` |
| Farbliteral in einer Komponentenregel | 3 | `colour literal outside the token sheet` |
| Farbliteral in einem `@keyframes`-Schritt | 3 | `@keyframes step` |
| Animation ohne `prefers-reduced-motion`-Rückfall | 3 | `keep animating when the system asks for reduced motion` |
| `outline: none` auf Link und Button | 3 | `look EXACTLY the same as unfocused, pixel for pixel` |
| `outline: none` nur auf dem Link (der Fall, den die computed-style-Regel verfehlt) | 3 | dito |
| `cursor: pointer` ohne Tab-Ordnung | 3 | `is in no tab order` |
| Link mit `tabindex="-1"` | 3 | `is in no tab order` |
| `tabindex="3"` | 3 | `overrides the document order` |
| **derselbe Entwurf unversehrt** | **0** | — (ohne diesen Fall wäre eine Prüfung, die alles verweigert, in allen Zeilen darüber grün) |

**Mutationslauf** (Defekt in einer Kopie außerhalb des Repos wiederhergestellt, Suite gefahren,
Defekt zurückgenommen — `_round-scratch/TSK-0119/mutate.py`):

| Wiederhergestellter Defekt | Ergebnis |
|---|---|
| Kontrastprüfung entfernt | `-k contrast`: **1 failed** |
| Farbliteralprüfung entfernt | `-k colour`: **1 failed** |
| Tastaturlauf entfernt | `-k "focus or tab or mouse or link"`: **2 failed**, 3 passed |
| `prefers-reduced-motion`-Prüfung entfernt | `-k reduced`: **1 failed** |
| Fokus wieder an computed styles statt an Pixeln | `-k computed`: **1 failed** |
| Regel-Walk wieder nur auf `selectorText` (ohne `keyText`) | `-k keyframe`: **1 failed** |
| Sichtbarkeit wieder an der eigenen `opacity` statt an `checkVisibility` | **1 failed**, 19 passed |
| Prüfungen dürfen den Render abbrechen (statt Befund zu werden) | `-k breaks`: **1 failed**, 1 passed |
| Konformitätsschritt ganz entfernt | **12 failed**, 5 passed |

Nacharbeit 1 hat sieben weitere gepflanzte Verletzungen und sieben weitere Mutationen dazugelegt
(unlesbares Stylesheet, verblasstes Element, Pseudo-Element-Text, Präsentationsattribut, Entwurf
ohne View, plus die beiden Kopplungen der SKILL-Vorlage) — die Tabellen dazu stehen in §13.

**Was NICHT gebaut ist und wo es steht:** kein axe-Lauf (`H139`-Nachbarabsatz in §1c: axe ist ein
npm-Paket, das Kit liefert keine npm-Datei aus, und die eine ausgelieferte Abhängigkeitsdatei lag
außerhalb der Dateihoheit); B3 (Farbliterale im Anwendungscode) und die Build-Hälfte von C1/C2/C3
(`H139`).

---

## 5. FR-0078 — Abnahmezeile

**Gebaut, als Prüfung im ausgelieferten Skript, nicht als Haken** (Begründung in 2).

- Der Renderer liest am gerenderten DOM jeden Container mit `data-view` und zählt darin die
  Elemente mit `data-primary-action`, deren nächster `[data-view]`-Vorfahr genau dieser View ist.
  Ungleich 1 → Befund mit Satz: *„view 'uebersicht' declares 2 primary action(s)
  [data-primary-action]; a view names exactly ONE thing the user should do here and one thing they
  see it by first. Say that sentence, then mark that one element."*
- **Die SKILL-Zeile nennt das VERFAHREN, nicht ein Adjektiv.** Neuer Abschnitt „Ranking: the ONE
  thing this view is for — the procedure, not the adjective" in
  `team-kits/dev-team/skills/product-designer/SKILL.md`, drei Schritte: (1) den Satz schreiben,
  bevor gezeichnet wird — *„Here the user <does one thing>, and they see it first by <the one
  signal>."*, ein Verb, ein Signal, ein Satz mit „und" ist zwei Views; (2) Container mit `data-view`
  und das eine Element mit `data-primary-action` auszeichnen; (3) den Satz in die Spezifikation
  neben das Mockup, damit der Frontend das WARUM erbt und die Fidelity-Runde etwas zum Vergleichen
  hat. Dazu ein Punkt in der Phase-2-Liste.
- **Gegen den Kit-Text gemessen, nicht gegen ein Literal im Test:**
  `tools/test_design_conformance.py::test_the_ranking_attributes_the_skill_teaches_are_the_ones_the_check_reads`
  liest `VIEW_ATTR` und `PRIMARY_ACTION_ATTR` aus dem **Modul**, sucht beide im ausgelieferten
  SKILL-Text und verlangt im selben Abschnitt die Verfahrenswörter. Driftet eine Schreibweise,
  zeichnet die Designerin einen Entwurf aus, den niemand liest, und die Prüfung meldet „0 primary
  actions" auf einem Mockup, das eines hat — ein Rename, das wie ein Designfehler aussieht.

**Rot zuerst:** zwei gepflanzte Views (zwei primäre Aktionen bzw. keine) → je rc 3 mit dem
jeweiligen Satz; Mutation „Rangfolge-Prüfung entfernt" → `-k primary`: **2 failed**.

**Kein Schutz behauptet:** die SKILL-Zeile sagt ausdrücklich „It BLOCKS nothing — no hook refuses a
presentation over it — so the exit code is the whole mechanism"; die ENFORCEMENT-Zeile sagt
dasselbe aus der Gate-Richtung.

---

## 6. Kostenseite je Prüfung (DEC-0056), gemessen

Alle Prüfungen hängen an **einer** Stelle: dem zweiten Seitenaufruf in `kit_design_render.py`. Es
gibt keine zweite Kostenstelle und keinen neuen Haken.

Zahlen des **Endstands nach Nacharbeit 1** (die Erstmessung stand bei +0,27 s / +1,52 s; das
Verhältnis ist gleich geblieben, die Basis schwankt mit der Last des Hosts):

| Lage | Ohne die Prüfungen | Mit den Prüfungen | Differenz |
|---|---|---|---|
| Projekt **ohne UI** (nichts gestagt, nur ein Wireframe) | 0,178 s (rc 2) | 0,139 s (rc 2) | **keine messbare** (die Streuung ist größer als die Differenz). Das Skript antwortet „stages no .html draft" und kehrt **vor** dem Playwright-Import zurück; gehalten von `tools/test_design_conformance.py::test_a_project_that_stages_no_draft_never_reaches_the_browser`, das genau darauf besteht, dass die Install-Zeile NICHT mitkommt. |
| ein sauberer Entwurf (12 Elemente) | 1,10 s | 1,42 s | +0,32 s |
| fünf saubere Entwürfe | 2,18 s | 3,80 s | +1,62 s (~0,32 s je Entwurf) |
| **ein Entwurf von der Größe eines echten Per-View-Mockups** (603 Elemente, 242 fokussierbar) | 2,27 s | 12,15 s | **+9,88 s** — fast alles davon ist der Pixelvergleich des Fokus (2 Screenshots je Element, ~33 ms je Aufnahme). Er ist bei `FOCUS_PIXEL_BUDGET` = 120 Elementen gedeckelt, und der Deckel meldet sich: derselbe Lauf druckt „122 focusable element(s) were NOT compared … past the 120-element budget". Der Deckel ist die Obergrenze der Kosten und zugleich die benannte Grenze der Messung. |

(Die Basis ist dieselbe Datei mit herausgeschnittenem Konformitätsschritt, also derselbe
Chromium-Start — `_round-scratch/TSK-0119/probe_cost.py`. Eine zweite Messreihe während eines
laufenden Suitenlaufs lag um Faktor ~3 höher bei gleichem Verhältnis; die Zahlen oben sind die
Leerlaufmessung.)

**Über-Verweigerung je Prüfung, benannt:**

| Prüfung | Wo sie zu viel verweigert |
|---|---|
| Kontrast | Ein Entwurf, der Text bewusst dezent hält (Platzhalter, deaktivierte Zustände), bekommt einen Befund. Gegenrichtung ist gebaut: Text in einem `opacity: 0`-Wrapper wird NICHT beurteilt (`checkVisibility`), sonst hätte jeder Tooltip einen Befund erzeugt. |
| Farbliterale | Ein `@keyframes`-Schritt oder ein `style`-Attribut mit einer Farbe ist ein Befund, auch wenn es Absicht ist. Der Ausweg ist eine Custom Property, kein Schalter. |
| Tastatur (pointer-only) | `cursor: pointer` ist die Definition; ein rein dekoratives Element mit diesem Cursor wird gemeldet. |
| Fokus-Pixel | Ein Fokusring, der außerhalb des Rands von 8 px liegt, würde als unsichtbar gemeldet. Über `FOCUS_PIXEL_BUDGET` (120 Elemente) hinaus wird nichts verglichen — und als `NOT MEASURED` gedruckt, nie als bestanden. |
| Reduced motion | Ein Entwurf, der Bewegung absichtlich behält, ist ein Befund; die Designer-SKILL nennt den globalen Rückfall selbst „mandatory". |
| Rangfolge | Nur deklarierte Views (`H140`). |

---

## 7. Fristen (die Frage aus `expected_outputs` (3))

**Keine neue Haken-Registrierung, also keine neue Frist.** `team-kits/dev-team/settings/settings.json`
ist unverändert (0 Zeilen Diff). Damit ist auch
`tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default`
unberührt — die im Baum laufende Regel, die eine Frist nur dort erlaubt, wo der Haken eine eigene
Kind-Grenze darunter hat.

Was sich am **bestehenden** Haken ändern konnte, ist der Datensatz, den er liest: `render.json`
trägt jetzt je Quelle einen `conformance`-Block. Gemessen als Prozess, 7 Läufe je Zeile, bester Wert:

| `render.json` | Größe | Laufzeit `gate_design_sighted` | rc |
|---|---|---|---|
| wie bisher | 243 B | 0,076 s | 0 |
| mit leerem `conformance` | 293 B | 0,075 s | 0 |
| mit 100 Befunden | 14 429 B | 0,075 s | 0 |

Registrierte Frist dieses Eintrags: **keine**, also das Standardfenster; der früheste gemessene
Kill des Standardfensters liegt bei 560 s (`tools/provider_observations.json` →
`hook_deadlines`). 0,076 s gegen 560 s.

Die neuen Prüfungen selbst laufen in **keinem** Haken-Fenster: sie laufen im Skript, das die
Designer-Rolle aus ihrer Shell startet.

---

## 8. Bewusst nicht geschlossen, aber benannt

| Nr. | Was offen bleibt | Warum, und was stattdessen begrenzt |
|---|---|---|
| `H138` | Die Befunde verweigern nichts: rc 3, Datensatz trotzdem geschrieben, `gate_design_sighted` lässt durch. Gemessen: Renderer rc 3 → Haken rc 0. | `DEC-0056` (b) — kein Gate ohne gemessene Fehlklasse. Ein Zurückhalten des Datensatzes wäre die schlechtere Verweigerung („nobody has rendered this draft" schickt den Designer an die falsche Stelle). Begrenzt: Rückgabewert, gedruckter Befund, SKILL-Zeile, ENFORCEMENT-Zeile. |
| `H139` | BUILD-Hälfte von FR-0077 (C1/C2/C3 im `browser_smoke()`) und B3 nicht gebaut. | Beide Wirtsdateien byte-gespiegelt nach `research-team`, das im `forbidden_scope` steht (sha256 in der Tabelle des Eintrags). Begrenzt: der eingefrorene Vertrag trägt die Werte; der Fidelity-Review vergleicht — Urteil, keine Messung. |
| `H140` | Die Rangfolge-Prüfung sieht nur deklarierte Views; der Kontrast schweigt über Bild-/Verlaufshintergründe. Gemessen: dasselbe Markup mit zwei primären Aktionen ist rc 3 **mit** `data-view` und rc 0 **ohne**. | (1) ist die Grenze jeder Prüfung über eine Deklaration; (2) ist ein Rechenproblem, und eine geschätzte Farbe wäre eine Zahl, die niemand nachrechnen kann. Begrenzt: SKILL-Verfahrensschritt bzw. die gedruckte `NOT DECIDABLE`-Zeile mit eigenem Test. |

Zusätzlich benannt, ohne Löchernummer, weil ohne Kette:

- **Der Frontend erbt die Rangfolge-Konvention nur über den Vertrag.** `data-view`/`data-primary-action`
  im Build zu verlangen bräuchte `skills/frontend-developer/SKILL.md` — nicht im `allowed_scope`.
- **`kit_design_system_check.py` blieb unangetastet.** Es ist der semantisch passende Ort für eine
  Token-Prüfung über Projektquellen (B3), aber ohne `kit_checks._frontend_sources()` (fremde Datei)
  hätte es eine zweite Definition von „Frontend-Quelle" gebraucht — genau der Drift, den die
  Hausregel meint.
- **`frontend-design/SKILL.md` und `webapp-testing/SKILL.md` wurden NICHT geändert**, obwohl im
  `allowed_scope`: es sind Apache-2.0-Fremdtexte mit Marken/Liste-Vertrag, ihre Sätze bleiben wahr,
  und `[MOD-4]` legt ausdrücklich fest, dass die Zahlen und der Boden an genau einer Stelle stehen —
  in `product-designer/SKILL.md`. Eine zweite Fassung dort wäre der Defekt, den `SR-0008` meint.
- ~~**SVG-Präsentationsattribute** (`<rect fill="#f00">`) zählen nicht als Farbliteral~~ — **in
  Nacharbeit 1 geschlossen**, als Eigenschaft statt als Attributliste (`CSS.supports(name, value)`);
  siehe §13 und `H140` (5).

---

## 9. Nahtsätze für Strom D — wörtlich, hier NICHT geschrieben

Beide Dateien stehen im `forbidden_scope` dieses Items.

**(a) `team-kits/dev-team/agents/product-designer.md`**, im Absatz „You LOOK at your own draft
before anyone else does" (heute Zeile 35–37), anzuhängen:

> Since the same command also checks the rendered draft, its exit code has three meanings: `0`
> nothing to report, `2` nothing was rendered at all (hand it back), `3` it rendered and the
> automatically checkable share of the design standards found something — contrast, the keyboard
> path, reduced motion, focus visibility, a colour spelled instead of tokenised, a view with none
> or two primary actions. Nothing refuses a presentation over a `3`; reading it is your step.

**(b) `team-kits/dev-team/skills/project-manager/SKILL.md`**, Schritt (b) der Design-Phase (heute
Zeile 154–155, „designer renders it and looks at the pixels … you never forward a staged draft that
has no render behind it"), anzuhängen:

> The render step now also answers `3` when the draft breaks the mechanically checkable half of the
> design standards. That is not a gate and it does not stop you — but a designer that hands you a
> draft after a `3` has handed you contract defects the build will inherit, so ask for the exit
> code in the envelope and send it back rather than forwarding it.

**(c) `team-kits/dev-team/constitution/AGENTS.md`:** **kein** Satz. Dieser Strom hat kein Gate
gebaut; ein Verfassungssatz über eine Prüfung, die nichts verweigert, wäre genau die Schutzbehauptung,
die die Hausregel verbietet. Wenn Strom D dort etwas schreiben will, dann höchstens den Zeiger auf
`hooks/ENFORCEMENT.md`, wo die Grenze mit `H138` steht.

---

## 10. Suiten-Läufe (DEC-0050: nur betroffene Suiten; die volle Suite gehört in die Merge-Runde)

Geänderte Dateien: `team-kits/dev-team/templates/repo/scripts/kit_design_render.py`,
`team-kits/dev-team/skills/product-designer/SKILL.md`, `team-kits/dev-team/hooks/ENFORCEMENT.md`,
`team-kits/dev-team/VERSION`, `tools/constitution_section_pins.json`,
`docs/reviews/phase0-disposition.md`, `docs/POST_V2_WISHLIST.md`, neu
`tools/test_design_conformance.py`.

Nicht gefahren, mit Grund: `test_kernel`, `test_state`, `test_migrate`, `test_report`,
`test_backlog_types`, `test_board`, `test_finance_dashboard`, `test_office_duties`,
`test_research_chain`, `test_staging_cli`, `test_gaplog`, `test_schemas`, `test_approvals_dispatch`,
`test_routine_feed`, `test_handover_marker`, `test_model_pins`, `test_parity_sources`,
`test_ci_lint_pinned`, `test_user_defaults`, `test_design_system_contract` — keine davon liest eine
der geänderten Dateien (Kernel, Office/Research-Kit, Zustandsmaschinen). `test_design_system_contract`
steht ausdrücklich dabei, weil sein Name das Gegenteil nahelegt: er misst
`kit_design_system_check.py`, und diese Datei ist unverändert (gemessen: kein Treffer für
`kit_design_render` oder `product-designer` in seinem Quelltext).

**Gefahren auf dem ausgelieferten Endstand des Arbeitsbaums** (`suite-final.log`, `suite-gates.log`
im Scratch):

| Lauf | Ergebnis |
|---|---|
| `pytest tools/test_hooks.py test_hooks_v2.py test_repo_hygiene.py test_shortening_net.py test_role_contracts.py test_reference_skills.py test_kitupdate.py test_context_budget.py test_kit_neutrality.py test_presets.py test_shared_skill_contract.py test_disposition.py test_e2e.py test_design_conformance.py -q` | **3366 passed, 14 skipped** in 49:57, Exit 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` (Zwischenstand, vor den letzten Prosa-Korrekturen) | **489 passed** in 7:37 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` (Endstand) | **488 passed, 1 failed** in 21:18 |

**Der eine rote Test ist nicht dieser Strom, und das ist gemessen, nicht behauptet.** Rot ist
`.claude/hooks/test_gates.py::test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`,
ein **Zeitmesstest** von Gate 3: die Verweigerung kam nach 4,61 s, die Registrierung gibt 4,50 s.
Sein eigener Docstring benennt genau diese Lage („Under heavy PARALLEL load that vantage cost can
spike and eat the margin; that is BUG-0033's timing class … If this line reddens, re-run it as the
only load"). Auf diesem Host liefen währenddessen drei fremde Suiten anderer Ströme.

Gegenprobe, dieselbe Maschine, dasselbe Zeitfenster, **unveränderter Baum**: derselbe Test im
Hauptrepo `C:/Offline Repos/AgentAndSkills` auf `e45c0ca` — **ebenfalls rot, 4,5023 s gegen
4,50 s**. Dieser Strom ändert keine einzige Datei unter `.claude/` (Patch: 8 Dateien, keine davon
dort), also kann er den Test nicht bewegt haben. Ein echter Alleinlauf war nicht zu bekommen: drei
fremde `pytest`-Prozesse hielten den Host über die ganze Wartezeit
(`_round-scratch/TSK-0119/solo_gate3.py` wartete vergeblich). **Der Prüfer sollte ihn im Alleinlauf
nachfahren, bevor er ihn als Befund führt.**

`python -m ruff check .` → All checks passed. `python tools/validate.py` → all structural checks
passed. Provisorischer Stempel nach Nacharbeit 1: `team-kits/dev-team/VERSION` = **2026.09.03-4**
(`content: d588b689e2d984f27bb1b371e1e3d7cd1876c2fd313c2772a058d77b8a668e04`); `office-team` und
`research-team` unverändert.

---

## 11. Übergabe

- Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0119/stream-design.patch`
  (`git diff HEAD -- docs team-kits tools`, neue Testdatei per `git add -N` enthalten; 8 Dateien,
  +1076/−22).
- **Eine Datei im Arbeitsbaum ist geändert und NICHT im Patch, absichtlich benannt:**
  `project_memory/.audit/hook_events.jsonl` trägt zwei neue Zeilen (`gate_needs`,
  `gate_shell_hygiene`, 2026-09-03 08:42 und 08:58). Sie stammen nicht von einer Bearbeitung,
  sondern von den Haken-PROZESSEN, die die Suiten im Arbeitsbaum fahren — dieselbe Datei trägt aus
  der Vorrunde Zeilen vom 2026-09-02 mit identischem Text. `project_memory/**` steht im
  `forbidden_scope` dieses Items, und `git checkout/restore` ist untersagt, also bleibt die Datei
  wie sie ist und dieser Absatz ist die Meldung. Der Merge sollte diese zwei Zeilen verwerfen.
- Prüfer-Kopien ohne die `.git`-Datei des Worktrees (`shutil.ignore_patterns(".git", …)` in
  `_round-scratch/TSK-0119/mutate.py`).
- Messwerkzeuge im Scratch: `probe_dom.py` (Browser-Tatsachen), `probe_render.py` (gepflanzte
  Verletzungen), `probe_pixels.py` (Stabilität der Pixelmessung), `probe_link_focus.py` (der
  `outline-offset`-Fall), `probe_holes.py` (H139/H140-Ketten), `probe_cost.py` (DEC-0056),
  `probe_gate_deadline.py` (Frist), `mutate.py` (Rot-zuerst), `add_rows.py`,
  `fix_wishlist_claim.py`.

## 12. (g)-Tabelle

| Größe | Wert |
|---|---|
| Wanddauer Spawn → Übergabe | ~3 h 30 min (Scratch angelegt 07:26, Protokoll abgeschlossen 10:57) |
| davon Suitenläufe | ~1 h 20 min reine Laufzeit (49:57 + 21:18 + 7:37), zusätzlich Wartezeit, weil bis zu drei fremde Suiten denselben Host hielten |
| Tokens (Kontextbudget-Delta dieses Umsetzers) | ~352 000 |
| Geänderte Dateien | 7 geändert, 1 neu (1076 Zeilen +, 22 −) |
| Ströme, die denselben Host teilten | 3 (gemessen an gleichzeitigen fremden `pytest`-Prozessen) — der einzige gemessene Nebeneffekt ist der Zeitmesstest oben |

---

## 13. Nacharbeit 1 (Prüfurteil FAIL: B 1 / M 5 / N 4)

Beide gemeldeten Abweichungen des ersten Pakets hat der Prüfer angenommen (Skript statt Gate;
BUILD-Hälfte als Befund gegen den Schnitt, `H139`). Was hier steht, ist die Arbeit an den Befunden.

### B1 (blockierend) — die Messung „Verfahren statt Adjektiv" maß sich selbst

**Was falsch war.** `tools/test_design_conformance.py` suchte die Wörter „sentence" und „first" in
einem 4000-Zeichen-Fenster um `data-view`. Der Prüfer hat Schritt 1 des Verfahrens durch ein
Adjektiv ersetzt und die Attribut-Schritte stehen lassen → **1 passed**. Beide Wörter überlebten
anderswo, „first" sogar im Adjektivsatz selbst. Dazu: läge der Abschnitt in den ersten 2000 Zeichen
der Datei, wäre `index - 2000` negativ und der Ausschnitt leer — irreführend rot. Der Docstring
behauptete eine Eigenschaft, die der Code nicht baute.

**Was jetzt läuft.** Drei Stücke, und keines ist eine Wortsuche:

1. **Ein struktureller Schnitt.** `_skill_section` schneidet von der `## `-Überschrift bis zur
   nächsten `## `-Überschrift. Eigener Bodentest in beide Richtungen:
   `tools/test_design_conformance.py::test_the_section_reader_cuts_at_headings_and_not_at_a_character_count`
   — er misst, dass der Schnitt an der nächsten Überschrift endet UND dass ein Abschnitt am
   Dateianfang nicht leer zurückkommt.
2. **Eine Quelle für den Satz.** Neu im Modul:
   `RANKING_SENTENCE_TEMPLATE = "Here the user <does one thing>, and they see it first by <the one signal>."`
   Die Verweigerung des Renderers **zitiert** sie, und die SKILL trägt sie als Schritt 1 wörtlich.
   Ein Satz mit zwei benannten Leerstellen kann seine eigene Löschung nicht überleben — genau das,
   was ein Adjektiv nicht leistet.
3. **Zwei Kopplungen statt einer.**
   `tools/test_design_conformance.py::test_the_skill_teaches_the_ranking_PROCEDURE_the_check_demands`
   liest die Vorlage aus dem MODUL und verlangt sie im strukturell geschnittenen Ranking-Abschnitt,
   dazu beide Attribute und den Namen des Skripts;
   `tools/test_design_conformance.py::test_the_refusal_quotes_the_same_template_the_skill_teaches`
   liest den Satz aus der **gedruckten Ausgabe** eines echten Laufs — eine Verweigerung, die die
   Vorlage nur umschreibt, schickt die Designerin zu einem anderen Satz als die SKILL.

**Rot zuerst, mit der Mutation des Prüfers** (Kopie außerhalb des Repos,
`_round-scratch/TSK-0119/mutate_rework.py`):

| Wiederhergestellter Defekt | Auswahl | Ergebnis |
|---|---|---|
| Schritt 1 durch das Adjektiv ersetzt, Attribut-Schritte belassen | `-k PROCEDURE` | **1 failed** |
| die Verweigerung umschreibt die Vorlage statt sie zu zitieren | `-k refusal_quotes` | **1 failed** |
| Ranking-Abschnitt an den Dateianfang verschoben (die Negativ-Slice-Falle) | `-k "PROCEDURE or section_reader"` | **2 passed** — die Über-Verweigerung ist mitgemessen |

### H145 — ein unlesbares Stylesheet war für die Sonde ein leeres

`document.styleSheets` + `cssRules` wirft unter `file://` bei einem verlinkten Blatt; der stumme
`catch` machte daraus zwei Fehler zugleich (Literal nur dort → rc 0 stumm; `:focus-visible` nur dort
→ rc 3 mit einer falschen Anschuldigung). Jetzt: `undecided`-Eintrag mit `sheet.href`, und die
Aussage „declares no :focus-visible rule at all" wird unterdrückt, sobald ein Blatt unlesbar war —
eine Aussage über das ganze Dokument darf nicht stehen, wenn ein Teil ungelesen blieb. Rot ohne den
Fix: `-k stylesheet` → **1 failed**. Was offen bleibt (die Regeln des Blattes sind nicht
beurteilbar), trägt der Eintrag `H145`.

### H146 — zwei Sorten Text, die der Kontrast nicht sah

`0 < opacity < 1` galt als deckend (`.card { opacity: .05 }` → rc 0, falsch grün) und erzeugter Text
(`::before { content }`) hing an keinem Kindknoten. Jetzt wird die Deckkraft der ganzen
Vorfahrenkette als Produkt in die Alpha des Textes gefaltet (und im Befund genannt: „at opacity
0.05"), und `::before`/`::after` werden über `getComputedStyle(el, part)` mitgemessen, mit eigener
Deckkraft und eigenem Hintergrund. Rot ohne den Fix: `-k faded` → **1 failed**, `-k pseudo` →
**1 failed**. Offen und benannt: ein verblasstes Element MIT eigenem Hintergrund ist `UNDECIDED`,
weil die Gruppe als Einheit komponiert wird — jede Zahl dort wäre geschätzt.

### H140 ergänzt — drei Mechanismen, keine Schreibweisen

- **M3, offen:** „Fokus sichtbar" heißt hier „die beiden PNGs sind byte-verschieden". Die Messtechnik
  ist stabil, die DEFINITION ist die Lücke: ein Ring in der Hintergrundfarbe und eine Änderung um
  eine Kanaleinheit sind beide byte-verschieden und beide unsichtbar. Der Fix wäre eine Schwelle
  über der Kanaldifferenz und braucht einen PNG-Dekoder, den dieses Kit nicht ausliefert.
- **M5, geschlossen:** Farbliterale in Präsentationsattributen, als Eigenschaft statt als
  Attributliste — ein Attribut zählt, wenn dieser Browser seinen NAMEN als CSS-Eigenschaft mit
  diesem Wert annimmt. `<rect fill="#ff0000">` war rc 0, ist rc 3; `fill="var(--brand)"` bleibt
  rc 0 (beide Richtungen im selben Test). Rot ohne den Fix: `-k presentation_attribute` →
  **1 failed**.
- **M6, eine Aussage:** die Sonde liest den **deklarativen Zustand des Light DOM**, einmal, beim
  Laden — kein Shadow Root, kein Zustand aus einem Skript, kein per `addEventListener` angehängter
  Handler. Das `onclick` der Auszeichnung selbst wird jetzt gelesen und macht ein Element ohne
  Tab-Ordnung zum Befund, auch ohne `cursor: pointer`. Der Satz steht im Kopf der Sonde und in
  `H140` (4).

### N8 — ein Entwurf ohne einen einzigen View sagte kein Wort

Schweigen und Bestehen sahen gleich aus. Jetzt: `undecided`-Zeile („no [data-view] container, so the
one-primary-goal rule judged nothing here"), rc bleibt 0, weil ein Phase-1-Kachelblatt zu Recht
keinen View deklariert. Rot ohne den Fix: `-k declares_no_view` → **1 failed**.

### H138 — benannte Ausnahme, vom Nutzer abgenommen

Der Nutzer hat am **2026-09-03** abgenommen („melden reicht vorerst"), auf Basis des Beispiels
Entwurf mit Kontrast 2,1:1 und zwei Hauptknöpfen → rc 3 im Umschlag → PM schickt zurück, und nichts
hindert das Einfrieren. **Die Bedingung, unter der die Ausnahme fällt**, steht mit im Eintrag: der
erste echte Fall, in dem ein Entwurf MIT Befunden trotzdem gebaut oder eingefroren wurde, macht
daraus ein Gate. Damit ist `H138` nach `DEC-0056` „consequences" kein offener Rest mehr, sondern der
vorgesehene Endzustand dieser Klasse.

### Bereinigt

- **N7:** die sha256-Zeile für `kit_design_render.py` in der `H139`-Tabelle war ein Zwischenstand.
  Sie ist **entfernt** statt neu gemessen: die Datei hat keinen Spiegel, also sagt ihr Hash zur
  Spiegelfrage nichts, und eine Zahl, die jede Runde wandert, ist genau die Zahl, die rottet. Die
  Zeile lautet jetzt „— (kein Spiegel, nur dev-team)".
- **N9:** `tools/test_design_system_contract.py` steht jetzt in §10 in der Nicht-gefahren-Liste, mit
  dem Grund (sein Name legt das Gegenteil nahe; er misst `kit_design_system_check.py`, unverändert).
- **N10** (Widerspruch im Item: `forbidden_scope project_memory/**` gegen die Ausnahme in
  `expected_outputs`) ist ein Befund gegen den Schnitt und nicht meiner.

### Suitenläufe von Nacharbeit 1 (Endstand des Arbeitsbaums)

| Lauf | Ergebnis |
|---|---|
| dieselben 14 `tools/`-Suiten wie oben | **3373 passed, 14 skipped** in 46:30, Exit 0 (7 Tests mehr als vor der Nacharbeit) |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **488 passed, 1 failed** in 22:45 |
| die eine rote Stelle, nach dem Fix einzeln nachgefahren | **2 passed** |

**Der rote Test war diesmal meiner, und er ist behoben.**
`.claude/hooks/test_gates.py::test_the_hole_list_judges_every_entry_it_carries` verlangt, dass die
Übersichtszeile eines Eintrags dasselbe Urteil spricht wie der Eintrag selbst. Ich hatte den
`H138`-EINTRAG auf die Nutzerabnahme umgeschrieben und die ZEILE auf „OFFEN“ stehen lassen — genau
die Drift, gegen die dieser Test gebaut ist. Die Zeile lautet jetzt „**AUSNAHME, vom Nutzer
abgenommen 2026-09-03**“ und trägt die Bedingung, unter der die Ausnahme fällt, mit. Nachgefahren:
`test_the_hole_list_judges_every_entry_it_carries` und
`test_every_test_the_hole_list_names_is_one_that_exists` — **2 passed, 487 deselected**. Die
Korrektur berührt ausschließlich `docs/POST_V2_WISHLIST.md`, und diese beiden sind die einzigen
Tests der Gate-Suite, die diese Datei lesen.

**Der Zeitmesstest von Gate 3, der im ersten Paket rot war, ist in diesem Lauf GRÜN** — was die
Erstdiagnose bestätigt: es war die Lastklasse `BUG-0033` und nicht der Strom. `ruff` grün,
`validate.py` grün.

### Was Nacharbeit 1 NICHT geschlossen hat

`H139` (BUILD-Hälfte, fremde Dateihoheit), `H140` (1) (nur deklarierte Views), `H140` (3) (die
Byte-Definition der Fokus-Sichtbarkeit), `H145`-Rest (Regeln eines unlesbaren Blattes),
`H146`-Rest (Gruppen-Komposition bei verblasstem Element mit eigenem Hintergrund).

---

## 14. (g)-Tabelle, Endstand nach Nacharbeit 1

| Größe | Wert |
|---|---|
| Wanddauer Spawn → Übergabe (beide Runden) | ~5 h 55 min (Scratch angelegt 07:26, Nacharbeit abgeschlossen 13:22) |
| davon Nacharbeit 1 | ~2 h 25 min |
| reine Suitenlaufzeit beider Runden | ~2 h 40 min (49:57 + 21:18 + 7:37 + 46:30 + 22:45), dazu Wartezeit durch bis zu drei fremde Suiten auf demselben Host |
| Tokens (Kontextbudget-Delta dieses Umsetzers, beide Runden) | ~430 000 |
| Geänderte Dateien | 7 geändert, 1 neu (+1431 / −22) |
| Tests in `tools/test_design_conformance.py` | 27 (vorher 20) |
| Rot-zuerst-Mutationen insgesamt | 16 (9 im ersten Paket, 7 in der Nacharbeit), dazu eine Grün-Mutation als Über-Verweigerungsprobe |

---

## 15. Nacharbeit 2 (Wiederholungsprüfung FAIL, ohne rundenblockierenden Befund)

Der Prüfer hat B1 als geschlossen gemessen (fünf eigene Mutationen rot), M5 als Eigenschaft
bestätigt (zehn Fälle) und H145/H146/N8/N7/N9 abgenommen. Das FAIL trug **zwei Gegenlücken der
Fixes selbst** — beide sind hier geschlossen, keine ist eingetragen worden.

### B-1 — die Unterdrückung von H145 war global statt qualifiziert

**Was falsch war.** `if facts["focusable"] and not facts["focus_visible_rules"] and not
facts["unreadable_sheets"]` ließ den Befund ganz fallen, sobald IRGENDEIN Blatt unlesbar war. Ein
Entwurf **ohne jede** `:focus-visible`-Regel plus ein verlinktes, völlig unbeteiligtes `print.css`
kam damit rc 0 zurück — der Fix gegen die falsche Anschuldigung hatte eine Tür danebengestellt.

**Was jetzt läuft.** Der Befund bleibt und wird qualifiziert: „no :focus-visible rule in the sheets
this run could read (N sheet(s) unreadable, named below — the rule may be in one of them)". Was ein
unlesbares Blatt wegnimmt, ist das Wort „at all", nicht der Befund. Rot zuerst mit der globalen
Unterdrückung: `-k unreadable_sheet_does_not_buy` → **1 failed**. Der bestehende H145-Test hat eine
dritte Zusicherung dazubekommen (`"sheet(s) unreadable" in text`), damit eine Rückkehr zur
unqualifizierten Fassung nicht still bleibt. `H145` nennt jetzt nur noch den Rest: die Regeln des
unlesbaren Blattes sind nicht beurteilbar.

### B-2 — `rendered()` wurde über das Element gefragt, nie über das Pseudo-Element

**Was falsch war.** Der Sichtbarkeitstest lief über das ELEMENT; ein `::before` mit `display:none`,
`visibility:hidden`, `opacity:0` oder leerem `content` bekam Kontrastbefunde („contrast 1.00:1 … at
opacity 0", Textprobe leer) — die exakte Umkehrung von
`tools/test_design_conformance.py::test_text_nobody_can_see_is_not_judged_for_contrast` eine
Verzweigung darüber.

**Was jetzt läuft.** `checkVisibility` reicht nicht an ein Pseudo-Element, also werden dessen eigene
`display`, `visibility` und `opacity` gefragt, und ein entquoteter leerer `content` erzeugt eine Box
und keinen Text. Rot zuerst: `-k nobody_can_see_is_not_judged_either` → **4 failed** (vier
parametrisierte Fälle). Gegenrichtung gebaut und grün:
`tools/test_design_conformance.py::test_a_pseudo_element_inside_a_hidden_element_stays_unjudged` —
ein unsichtbares ELEMENT bleibt rc 0, das war nie die Lücke.

### Die vier kleinen Punkte

- **N-1:** der Satz nannte „cursor: pointer", auch wenn das `onclick` gefeuert hatte. Jetzt reist das
  Signal mit dem Befund („an onclick attribute"), beide sind möglich und beide werden genannt. Rot
  zuerst: `-k names_the_signal` → **1 failed**.
- **N-2:** `H140` (1) sagte noch „die Prüfung schweigt". Seit `N8` schweigt sie nicht mehr; der
  Begrenzungssatz nennt jetzt die `NOT DECIDABLE`-Zeile und den Test, der sie hält.
- **N-3:** der Docstring von
  `tools/test_design_conformance.py::test_the_skill_teaches_the_ranking_PROCEDURE_the_check_demands`
  benennt jetzt seine eigene Grenze: die Löschung der Vorlage ist messbar, ihre Widerrufung in Prosa
  („zitiere sie, dann ignoriere sie") nicht. Präsenz ist mechanisch, Bedeutung nicht — R2 des
  Prüfers bleibt grün und ist benannt statt behauptet.
- **N-5:** die Übersichtszeilen stehen in Nummernfolge H138, H139, H140, H145, H146.
- **`DEC-0069`:** die Nutzerabnahme zu `H138` hat jetzt einen Datensatz; Eintrag und Übersichtszeile
  verweisen darauf, statt Datum und Wortlaut ein zweites Mal zu führen.

### Läufe von Nacharbeit 2 (nach Vorgabe: keine 14 Suiten, keine volle Gate-Suite)

| Lauf | Ergebnis |
|---|---|
| `tools/test_design_conformance.py` voll | **34 passed** in 41 s (vorher 27) |
| die zwei Löcherlisten-Knoten aus `.claude/hooks/test_gates.py` | **2 passed, 487 deselected** in 2,2 s |
| `ruff check .` / `validate.py` | grün / grün |

Provisorischer Stempel: `team-kits/dev-team/VERSION` = **2026.09.03-5**
(`content: ec703298dbfff3cea87abd192d7cb745b6a87198fc777bc9bc6c636e260993e0`).

### Was auch nach Nacharbeit 2 offen und benannt ist

`H139` (BUILD-Hälfte, fremde Dateihoheit) · `H140` (1) nur deklarierte Views, jetzt aber sichtbar
nicht-beurteilt, und (3) die Byte-Definition der Fokus-Sichtbarkeit · `H145`-Rest (die Regeln eines
unlesbaren Blattes) · `H146`-Rest (Gruppen-Komposition bei verblasstem Element mit eigenem
Hintergrund) · die Grenze der SKILL-Kopplung aus N-3 (eine Vorlage, die neben sich widerrufen wird).

| Größe | Wert |
|---|---|
| Wanddauer Nacharbeit 2 | ~40 min |
| Wanddauer gesamt (drei Runden) | ~6 h 35 min |
| Tokens gesamt | ~455 000 |
| Tests in `tools/test_design_conformance.py` | 34 |
| Rot-zuerst-Mutationen gesamt | 19 (9 + 7 + 3), dazu eine Grün-Mutation als Über-Verweigerungsprobe |

---

## 16. Nacharbeit 3 (dritte Prüfung PASS, mit einer Auflage für den Merge)

Zwei Abschlusszeilen, beide billiger gebaut als eingetragen. Keine erneute Prüfung angefordert; der
Merge-Prüfer liest diesen Abschnitt.

### R-A — ein `@import` ist ein Blatt für sich, und der Walk ging daran vorbei

**Was falsch war.** `walkRules` stieg über `rule.cssRules` ab. Eine `CSSImportRule` hält ihre Regeln
aber unter `rule.styleSheet.cssRules` und wurde nie betreten. Der zweite, schlimmere Teil: weil das
IMPORTIERENDE Blatt lesbar ist, entstand kein `unreadable_sheets`-Eintrag — die Absage-Aussage kam
also **unqualifiziert** heraus, während die einzige `:focus-visible`-Regel des Entwurfs eine Ebene
tiefer stand und wirkte, und ein Farbliteral dort stumm durchging.

**Was jetzt läuft.** `styleSheet.cssRules` wird im selben `try/catch` betreten; im `catch` landet
derselbe Eintrag, mit dem `href` des Imports. Damit gilt für einen Import wortgleich, was für ein
verlinktes Blatt gilt.

**Gemessen, beide Richtungen** (`file://`, ausgeliefertes Skript als Prozess):

| Import | vor dem Fix | jetzt |
|---|---|---|
| `@import url("theme.css")` (Nachbardatei, wirft `SecurityError`) | rc 3, unqualifizierter Satz, keine `NOT DECIDABLE`-Zeile | rc 3, qualifizierter Satz + `theme.css` benannt |
| `@import url("data:text/css,…")` (lesbar) | Regel nicht gefunden → Anschuldigung; Literal übersehen | keine Anschuldigung, Literal gemeldet |

Rot zuerst: `-k imported_sheet` → **2 failed** (beide Richtungen mit einer Mutation).

### R-B — `["::before", "::after"]` war eine Aufzählung ohne Stolperdraht

**Was falsch war.** `.inp::placeholder { color: var(--faint) }` auf einem
`<input placeholder="Suchbegriff">` war **rc 0** — der klassische Kontrastfehler eines Mockups —,
`li::marker` ebenso.

**Was jetzt läuft.** Vier Einträge, und jeder sagt, WIE der Text ihn erreicht: `::before`/`::after`
über `content`, `::placeholder` über das **Attribut**, `::marker` über den **Listenstil**. Für die
letzten beiden rechnet `content` zu `normal` (gemessen) — eine einzige Regel wäre für drei von vier
falsch gewesen.

**Warum die Liste eine Liste bleibt, geschrieben statt behauptet.** CSS schließt die Menge der
Pseudo-Elemente; erfinden kann sie niemand. Aber das DOM bietet keinen Weg zu fragen, welche ein
Element HAT: `getComputedStyle(el, part)` antwortet für jede Schreibweise, gültige wie ungültige.
Es gibt also nichts, wogegen die Liste zu messen wäre, und **kein Stolperdraht, der ein totes oder
ein fehlendes Glied fände**. Deshalb steht der Grund im Code und die Kosten in `H146`: ein
textführendes Pseudo-Element, das dort nicht steht, wird nicht beurteilt.

Rot zuerst: `-k placeholder_is_text` → **1 failed**, `-k bullet_of_a_list` → **1 failed**. Beide
Tests messen die Gegenrichtung mit (`<input>` ohne Attribut bzw. `list-style-type: none` → rc 0), so
dass eine Prüfung, die einfach immer meldet, nicht grün werden kann.

### Läufe von Nacharbeit 3

| Lauf | Ergebnis |
|---|---|
| `tools/test_design_conformance.py` voll | **38 passed** in 49 s (vorher 34) |
| die zwei Löcherlisten-Knoten aus `.claude/hooks/test_gates.py` | **2 passed, 487 deselected** |
| `ruff check .` / `validate.py` | grün / grün |

Provisorischer Stempel: `team-kits/dev-team/VERSION` = **2026.09.03-6**
(`content: 5f9751c3360442d54620f8212a235d9bd69a8039f6e1cf62696d3c013252a013`).

### Was nach Nacharbeit 3 offen und benannt ist

- `H139` — die BUILD-Hälfte, fremde Dateihoheit.
- `H140` (1) nur deklarierte Views (sichtbar nicht-beurteilt), (3) die Byte-Definition der
  Fokus-Sichtbarkeit.
- `H145`-Rest — die Regeln **jedes** Blattes, das dieses Dokument nicht lesen darf, verlinkt oder
  importiert, sind nicht beurteilbar. Ob eines lesbar ist, entscheidet der Browser und nicht dieses
  Kit: ein `data:`-Import ist es, eine Nachbardatei unter `file://` nicht.
- `H146`-Rest — die Gruppen-Komposition bei einem verblassten Element mit eigenem Hintergrund, ein
  `content`, das nur ein Bild ist, **und neu: die Pseudo-Element-Liste ohne Stolperdraht**.
- Die N-3-Grenze der SKILL-Kopplung (eine Vorlage, die neben sich widerrufen wird).

| Größe | Wert |
|---|---|
| Wanddauer Nacharbeit 3 | ~20 min |
| Wanddauer gesamt (vier Runden) | ~6 h 55 min |
| Tokens gesamt | ~475 000 |
| Tests in `tools/test_design_conformance.py` | 38 |
| Rot-zuerst-Mutationen gesamt | 22 (9 + 7 + 3 + 3), dazu eine Grün-Mutation als Über-Verweigerungsprobe |
| Patch | 8 Dateien, +1750 / −22 |
