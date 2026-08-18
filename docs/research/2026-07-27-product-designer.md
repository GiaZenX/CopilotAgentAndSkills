# Rolle `product-designer` — Recherche gegen anerkannte Standards

Datei: `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\product-designer\SKILL.md` (127 Zeilen).
Kontext gelesen: `docs/HARNESS_V2_SPEC.md` II.2/II.6/II.6a/II.11, `team-kits/dev-team/constitution/AGENTS.md` §2/§6, `skills/frontend-developer/SKILL.md`, `skills/quality-engineer/SKILL.md`, `templates/repo/scripts/kit_checks.py`. In `research-team` und `office-team` existiert **keine** Designrolle — die Befunde unten betreffen ausschliesslich `dev-team` (Randnotiz am Ende).

---

## 1. Was die SKILL heute gut macht

Vier Dinge sind überdurchschnittlich und dürfen beim Härten **nicht** verloren gehen:

**a) Der Divergenz-Zwang mit sichtbarem Beleg.** „Invent **2–3 genuinely different, named directions** — distinct moods, all at top-tier quality, NOT three shades of one idea" plus die Pflicht, das als eine self-contained HTML-Datei zu stagen, „that renders ALL directions side by side as real tiles — actual background/surface/accent colors, the real font pairing … **a real button and card** with a live hover/press transition at the stated timing". Genau das ist in der Literatur der empfohlene Gegenmechanismus gegen Homogenisierung (unten 2a) — „productive friction" statt Ein-Klick-Akzeptanz. Das ist nicht selbstverständlich und ist richtig.

**b) Ein Kontrakt statt einer Tokenliste — und die Begründung dafür steht drin.** „**Mandatory: extend the staged preview into PER-VIEW SCREEN MOCKUPS** … Frozen, this file IS the **visual contract** … A design that exists only as a token list cannot be built faithfully (a real run ‚recolored' four slices because no per-view contract existed)." Zusammen mit `frontend-developer` („take the mockup's **markup + CSS as the BASE**") und `design_ref` als TSK-Pflichtfeld ist das eine **einzige Quelle der Wahrheit** — der Punkt, an dem die halbe Branche scheitert (siehe 5a). Der Harness ist hier besser als der Industriestandard, nicht schlechter.

**c) Konkretheit statt Adjektiven.** „Specific — never ‚smooth animations'", „real hex, real fonts, real ms timings", 150–250 ms als Zahl. Und der Base-Reset-Absatz mit `button, input, select, textarea { font: inherit }` ist echtes Handwerkswissen aus einem realen Fehlschlag.

**d) Die Regel, die den Harness überhaupt trägt.** „a rule that must hold beyond this revision … is proposed as an `INV` item WITH the test that proves it — a hard requirement nothing can check is how a wrong value survives a redesign." Das ist exakt die GATE/SKILL-Trennlinie, und sie steht bereits in der Rolle. Die Recherche unten baut nur darauf auf.

**e) Phase 3 ist ein systematischer Walkthrough**, keine Stichprobe: „every screen/tab × light+dark × desktop+mobile width". Selten so sauber formuliert.

---

## 2. Was gemessen an publizierten Standards fehlt

### 2a) Die publizierte Ursachenanalyse für „lieblos" fehlt komplett — und mit ihr der wirksamste Hebel

Die SKILL verbietet das Ergebnis („Generic ‚0815' … is a **FAIL**"), benennt aber die Ursache nicht. Die ist erforscht:

- **Homogenisierung ist älter als KI.** Goree/Doosti/Crandall/Su, *Investigating the Homogenization of Web Design*, CHI 2021: Computer-Vision-Analyse repräsentativer Websites 2003–2019; die mittlere Layout-Distanz zwischen Seiten sinkt seit 2007 um über 30 %, 2010–2019 um 44 % (p < 0.001). https://dl.acm.org/doi/abs/10.1145/3411764.3445156 · Volltext-PDF: https://aux.engineering.ucsc.edu/publications/Goree_Doosti_Crandall_Su-HomogenizationWebDesign-CHI21.pdf
- **KI-Prototypen sind brauchbar, aber unoriginell — blind gemessen.** Romero et al., *Usable but Conventional: An Empirical Study on the UX of AI-Generated Interface Prototypes*, SEMISH 2026 (n = 92, UEQ-S, Blindbewertung): pragmatische Qualität gut, **hedonische Qualität — Originalität, Innovation — schlecht**. https://arxiv.org/abs/2605.15124
- **Warum, mechanistisch, und was dagegen hilft.** Shin/Lee/Gao/Reinecke/Pang/Tseng (UW + Microsoft Research), *Interrogating Design Homogenization in Web Vibe Coding*, arXiv 2603.13036, März 2026. Drei Treiber: (1) **Modell-Priors** — englischsprachige Trainingsdaten, westliche Ästhetik als Default; (2) **frictionless generation** — „success is measured by how quickly vague user intent is converted into outcome"; (3) **Pfad des geringsten Widerstands** beim Nutzer. Gegenmittel „productive friction" auf drei Ebenen; die für diesen Harness relevante ist die **meso**-Ebene: *contextual anchoring* (das Werkzeug muss Designsystem-Tokens, Markenleitlinien oder die bestehende digitale Präsenz **einlesen müssen**) und *comparative analysis* (das System meldet, wenn der Entwurf auf Standardkonventionen zurückfällt — wörtlich: „generic web styles—such as standard drop shadows or rounded corners"). https://arxiv.org/abs/2603.13036

**Der Befund für diesen Harness:** Die SKILL hat die Mikro-Ebene (Richtungen, Reibung, Auswahl durch den User) — und **keine Meso-Ebene**. Es gibt kein projektweites Marken-/Ton-/Anti-Referenz-Artefakt. Jeder neue PR startet die Designerin wieder beim Modell-Prior. Das ist nach der Literatur die stärkste einzelne Ursache für „sieht überall gleich aus", und sie ist im Zustandsmodell heute nicht abgebildet.

### 2b) WCAG 2.2 ist im Harness eine QA-Nachprüfung, kein Design-Input

Die SKILL sagt genau zweimal etwas zu Barrierefreiheit: „WCAG AA contrast" (Zeile 96) und „**Accessibility**: focus-visible style, keyboard order, contrast, reduced-motion, semantic structure" (Zeile 107). Die vollständige Prüfung steht in `quality-engineer/SKILL.md` — also in Phase 6–8, nach der Implementierung. Das ist genau die Reihenfolge, die der Auftrag als falsch benennt.

Was fehlt, ist nicht „mehr a11y", sondern die **Untermenge von WCAG 2.2, die eine Layout-/Flow-Entscheidung ist und nachträglich nicht mehr reparierbar**:

| SC | Level | Warum Design, nicht QA |
|---|---|---|
| **2.5.8 Target Size (Minimum)** — 24×24 CSS px | AA (neu in 2.2) | Steht in **direktem Konflikt** mit der Ästhetik, die die SKILL fordert (dicht, „Linear/Raycast-like", ruhig). Wer das erst in QA merkt, muss das Spacing-System neu bauen. https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html |
| **2.4.11 Focus Not Obscured (Min.)** | AA (neu) | Trifft sticky Header/Footer/Toolbars — eine Layoutentscheidung des Wireframes. |
| **2.5.7 Dragging Movements** | AA (neu) | Jede Drag-Interaktion braucht eine Single-Pointer-Alternative. Das ist eine Flow-Entscheidung, kein CSS. |
| **3.2.6 Consistent Help** | A (neu) | Hilfe muss auf jeder Seite an derselben relativen Position stehen — reine Informationsarchitektur, gehört in Phase 0 (WFR). |
| **3.3.7 Redundant Entry** / **3.3.8 Accessible Authentication (Min.)** | A / AA (neu) | Verbietet u. a. kognitive Funktionstests (Rätsel-CAPTCHA, „Code abtippen"). Eine Flow-Entscheidung im Wireframe. |

WCAG 2.2 ist seit 05.10.2023 W3C Recommendation: https://www.w3.org/TR/WCAG22/
Rechtlicher Treiber, den die SKILL nirgends erwähnt: der **European Accessibility Act** ist seit 28.06.2025 durchsetzbar und bindet erstmals die Privatwirtschaft; harmonisierte Norm EN 301 549 v3.2.1 (enthält WCAG 2.1 AA; die für 2026 erwartete v4.1.1 zieht WCAG 2.2 nach). https://accessible-eu-centre.ec.europa.eu/content-corner/news/wcag-22-officially-w3c-recommendation-2023-10-06_en

Ausserdem fehlt die **WAI-ARIA Authoring Practices Guide** als Entwurfseingabe. Die APG ist unversioniert und laufend gepflegt: https://www.w3.org/WAI/ARIA/apg/patterns/ — mit dem dort wiederholten Grundsatz „**no ARIA is better than bad ARIA**". Relevanz für die Designerin: wenn sie eine Komponente entwirft, für die die APG ein Muster hat (Combobox, Disclosure, Dialog, Tabs, Treegrid), dann ist das **erwartete Tastaturverhalten bereits normiert** — Pfeiltasten, Home/End, Esc, Fokusfalle im Dialog. Die SKILL fordert heute „Keyboard: shortcuts + command palette + a full keyboard path" und lässt die Designerin das Verhalten frei erfinden, obwohl es publiziert ist.

### 2c) Kontrast ist unpräzise formuliert — und damit nicht prüfbar

„WCAG AA contrast" nennt keine Zahl. Die Zahlen sind: **4.5:1** für Text (1.4.3), **3:1** für Grosstext, **3:1** für UI-Komponenten und grafische Objekte (1.4.11). Ein Modell kann „WCAG AA" behaupten, ohne es gerechnet zu haben. Das ist genau der Fehlertyp, den die SKILL an anderer Stelle selbst benennt.

### 2d) Token-Disziplin: die Semantik-Ebene ist genannt, die Architektur nicht

Die SKILL fordert „semantic tokens with hex for **light AND dark**" mit einer festen Liste (bg, surface, surface-2, border, text, text-muted, primary, primary-hover, accent, success, warning, danger). Das ist eine Liste, keine Disziplin. Publizierte Referenzen:

- **DTCG Design Tokens Format Module 2025.10** — erste stabile Fassung, 28.10.2025. **Wichtige Einschränkung:** Community-Group-Report, **kein W3C-Standard und nicht auf dem Standards Track**. https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/ · Spezifikation: https://www.designtokens.org/tr/drafts/format/
- **Material Design 3, Drei-Ebenen-Architektur** (`ref` → `sys` → `comp`): Referenzwerte, semantische Rollen, Komponentenbindung. Das ist die eigentliche Disziplin — nicht „nimm semantische Namen", sondern „eine Komponente greift **nie** auf die Referenzebene durch". https://m3.material.io/foundations/design-tokens

Was daraus für den Harness folgt, steht in 3d — und **nicht**, DTCG-JSON einzuführen (siehe 5b).

### 2e) Die Zustandsmatrix existiert pro Komponente, nicht pro View

Die SKILL fordert Zustände **pro Komponente** („default/hover/active/focus/disabled/loading/empty/error"). Sie fordert nirgends, dass **jeder View** in Leer-, Lade-, Teil- und Fehlerzustand entworfen wird. Genau das ist die Lücke, aus der „lieblos" im Betrieb entsteht: der Ideal-State ist hübsch, und die drei anderen erfindet der Frontend-Entwickler.

- Der geläufige Rahmen ist Scott Hurffs **„UI Stack"** (blank / loading / partial / error / ideal): https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/ — **ehrlich ausgewiesen: das ist ein Blogpost, kein Standard.** Die Fünferteilung ist de-facto weit übernommen (Carbon, GitLab, Treehouse-Curriculum), aber es gibt keine normative Quelle dafür. Als Struktur brauchbar, als „anerkannter Standard" nicht zitierfähig.
- Was normativ/forschungsgestützt ist, ist der **Inhalt** dieser Zustände: NN/g, *Designing Empty States in Complex Applications: 3 Guidelines* — der Leerzustand soll Systemstatus kommunizieren, die Erlernbarkeit erhöhen und einen direkten Pfad zur Kernaufgabe anbieten: https://www.nngroup.com/articles/empty-state-interface-design/ · NN/g, *Error-Message Guidelines*: https://www.nngroup.com/articles/error-message-guidelines/ und *10 Design Guidelines for Reporting Errors in Forms*: https://www.nngroup.com/articles/errors-forms-design-guidelines/
- Für Formularfehler ist das **GOV.UK-Validierungsmuster** die belastbarste öffentlich getestete Referenz (Error-Summary oben, Fokus dorthin verschieben, identischer Text am Feld): https://design-system.service.gov.uk/patterns/validation/ und https://design-system.service.gov.uk/components/error-message/

### 2f) Microcopy / Content Design kommt in der SKILL nicht vor

Kein Wort zu Beschriftungen, Button-Texten, Leerzustandstexten, Fehlermeldungstexten, Ton. Das ist — neben 2a — die zweite grosse Ursache für „KI-generiert": *„Submit"*, *„Welcome to your dashboard"*, *„No data available"*, *„Item 1"*. Standard dafür existiert seit 2023: **ISO 24495-1:2023 Plain language — Part 1: Governing principles and guidelines** (Konsensnorm, Experten aus 25 Ländern / 19 Sprachen; vier Grundsätze: Leser finden, verstehen und nutzen, was sie brauchen). https://www.iso.org/standard/78907.html · Zusammenfassung frei: https://www.iplfederation.org/iso-standard/

Praktisch bedeutsam: die SKILL definiert den DSN als **den** Vertrag für den Frontend — aber Text ist kein Bestandteil dieses Vertrags. Also erfindet ihn der Frontend. Das ist eine Lücke im Vertrag, keine Geschmacksfrage.

### 2g) Es gibt keinen Schritt, der das Design selbst kritisiert

Phase 3 vergleicht **Build gegen Mockup**. Niemand prüft je, ob das **Mockup** gut ist. Der publizierte Standardmechanismus dafür sind Nielsens **10 Usability-Heuristiken** (1994, laufend gepflegt): https://www.nngroup.com/articles/ten-usability-heuristics/ — mit der zugehörigen **Severity-Skala 0–4** von NN/g: https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/

Ebenfalls abwesend: die Kompositionsdisziplin aus **Atomic Design** (Brad Frost, Kapitel 2, frei online): https://atomicdesign.bradfrost.com/chapter-2/. Der für diesen Harness relevante Teil ist nicht das Vokabular, sondern die **Trennung Template ↔ Page** (Struktur vs. echter Inhalt) und die Existenz einer **Inventarschicht**, aus der Views zusammengesetzt werden. Ohne sie erfindet jeder View seine eigene Karte — was exakt der Fehler ist, den die SKILL unter dem Namen „recolored four slices" bereits kennt, aber nur am Frontend verortet.

### 2h) Performance-Budget: die SKILL nennt die richtige Zahl aus dem falschen Jahrzehnt

„perceived response < 100 ms" ist Nielsens 0,1-Sekunden-Grenze (Wahrnehmung direkter Manipulation), korrekt und weiterhin gültig: https://www.nngroup.com/articles/response-times-3-important-limits/. Sie ist aber **nicht messbar** im Sinne des Harness. Die messbare Feldmetrik ist **INP ≤ 200 ms am 75. Perzentil**, seit 12.03.2024 offiziell Core Web Vital anstelle von FID: https://web.dev/blog/inp-cwv-launch. Die SKILL vermischt beides zu einer Prosa-Zahl, aus der nie ein `INV` mit `check`-Referenz wird.

---

## 3. Für jede Lücke: GATE oder SKILL

Vorbemerkung zur Verortung, weil sie über die Machbarkeit entscheidet: **Der richtige Ort für Design-Gates ist die DSN-Promotion, nicht der Merge.** II.6a legt für ARC bereits fest, dass der Kernel bei der Promotion fail-closed validiert („prüft … die eingebettete mxGraph-XML auf Wohlgeformtheit und Renderbarkeit; Fehlschlag blockiert die Promotion"). Für DSN existiert dieser Haken, aber keine Prüfung darin. Alles unten Vorgeschlagene setzt dort an — und ist **nur deshalb bezahlbar, weil das Artefaktformat dem Harness gehört**: die self-contained HTML-Datei darf eine Markup-Konvention vorgeschrieben bekommen, Anwendungscode dürfte das nicht.

| # | Lücke | GATE / SKILL | Was geprüft wird und wie es scheitert |
|---|---|---|---|
| **a** | **Design-Anker fehlt** (2a) | **beides** | **SKILL:** In Phase 1 zwingend eine Anti-Referenz-Liste („was das ausdrücklich NICHT sein darf") und ein Marken-/Ton-Statement; bei einem Projekt mit bestehendem Anker leiten sich die Richtungen daraus ab statt bei null zu beginnen. **GATE bei DSN-Promotion:** Die gestagte HTML muss `<meta name="harness-design-anchor" content="DEC-nnnn">` tragen; der Kernel löst die ID im aktiven Zustand auf. **Fehlschlag:** Meta fehlt → Block („DSN names no design anchor"); ID zeigt auf nichts → Block (Referenzgraph, dasselbe Muster wie `design_ref`); Decision-Item steht auf `SUPERSEDED` → Block („anchor superseded; re-derive or update the DSN"). Nötige Nebenänderung: §6-Zeile, wer den Anker-Decision inhaltlich besitzt (heute gehören Decision-Items dem Architect; hier wäre es die Designerin auf Vorschlag, freigegeben vom User). **Kein neuer Item-Typ** — Decision hat bewusst keinen Statusautomaten (§9), genau richtig für eine Richtungsentscheidung. |
| **b** | **„drei Schattierungen einer Idee"** ist heute reine Prosa (2a) | **GATE** | Die gestagte Preview deklariert je Richtung einen maschinenlesbaren Block (`data-direction` mit `accent`, `heading-font`, `radius-base`, `motion-base`). **Fehlschlag:** zwei Richtungen liegen auf **allen** deklarierten Achsen zusammen — Accent-Hue-Distanz < 25° **und** identische Heading-Font **und** identische Radius-Basis **und** Motion-Dauer-Differenz < 40 ms → Promotion/Weitergabe blockiert mit „directions D1 and D2 differ on no declared axis". Mehrachsig mit Absicht: eine reine Hue-Distanz wäre ein zu grober Proxy und würde legitime Varianten fälschlich blocken. Dies erzwingt mechanisch eine Regel, die die SKILL **bereits aufstellt** — der billigste Gate-Typ, den es gibt. |
| **c** | **WCAG 2.2 als Design-Input** (2b) | **gespalten** | **GATE (mechanisch, auf der eingefrorenen DSN, headless):** ① axe-core-Lauf über die Datei — Kontrast, Name/Rolle/Wert, Landmarks, Formularbeschriftungen; Fehlschlag: jede `violation` mit impact ≥ serious → Block mit Regel-ID + Selektor. ② Zielgrösse: `getBoundingClientRect()` über alle interaktiven Elemente je deklarierter Breakpoint-Breite; < 24×24 CSS px ohne erfüllte Abstands-Ausnahme → Block mit Selektor und gemessener Grösse. ③ `prefers-reduced-motion`-Block existiert, sobald irgendein `transition`/`animation` deklariert ist → sonst Block. ④ mindestens eine `:focus-visible`-Regel existiert und keine `outline: none` ohne ersetzende Sichtbarkeit im selben Selektor → sonst Block. **SKILL (Urteil, nicht prüfbar):** 2.5.7 Drag-Alternative, 3.2.6 Hilfe-Position, 3.3.7/3.3.8 Auth-Flow, 2.4.11 Fokus nicht verdeckt — **und zwar in Phase 0 (Wireframe)**, weil es Flow- und Layoutentscheidungen sind. Plus: die APG-Muster als Pflichtlektüre, wenn eine entworfene Komponente dort ein Muster hat. **Ehrlichkeitspflicht im Gate-Text:** ein grüner axe-Lauf deckt laut Deque-Auswertung (13.000+ Seitenzustände, ~300.000 Befunde) **57 % des Befundvolumens** — der Gate darf niemals „WCAG-konform" melden, sondern „automatisch prüfbarer Anteil bestanden". https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/ |
| **d** | **Token-Disziplin** (2d) | **GATE** | Auf der gestagten DSN: ① **Kein Farbliteral ausserhalb des Tokenblocks** — jedes `#hex`, `rgb()`, `hsl()`, `oklch()` und jeder benannte CSS-Farbwert ausserhalb von `:root` / `[data-theme="dark"]`; Fehlschlag → Block mit Datei/Zeile/Selektor. Allowlist nötig: `transparent`, `currentColor`, `inherit`. ② **Theme-Parität** — die Token-Namensmenge unter `:root` und unter `[data-theme="dark"]` muss identisch sein; Fehlschlag → Block mit der Differenzmenge („dark theme is missing --color-surface-2"). Fängt den häufigsten Halbfertig-Zustand. ③ **Semantische Namen** — ein Token in der semantischen Ebene darf seinen eigenen Wert nicht benennen: Namen, die auf `/^--(color-)?(red|blue|green|yellow|orange|purple|pink|gray|grey|black|white)(-\d{2,3})?$/` matchen, sind nur in einem explizit als Referenzebene markierten Block zulässig; sonst Block. Damit ist die Material-3-Trennung ref/sys mechanisch erzwungen, ohne dass irgendein Werkzeug dazukommt. Implementierungshinweis: II.5 verlangt stdlib-first für **Hooks**; dieser Check läuft im Kernel bei Promotion, nicht im heissen Hookpfad — trotzdem würde ich ihn regexbasiert und ohne neue Abhängigkeit bauen, weil der CSS-Umfang einer DSN-Datei überschaubar und harness-eigen ist. |
| **e** | **Zustandsmatrix pro View** (2e) | **GATE für die Existenz, SKILL für den Inhalt** | **GATE:** Jeder View trägt `data-view="<name>"`; für jeden View müssen Varianten mit `data-state="loading"`, `"empty"` und `"error"` existieren (`"partial"` optional — die Fünferteilung ist nicht normiert, siehe 2e; drei sind verteidigbar, fünf wären erfundene Strenge). **Fehlschlag:** „view ‚inventory' has no data-state=empty variant" → Promotion blockiert. Das ist **Präsenz**, nicht Qualität — und es ist genau die richtige Aufteilung: dass es einen Leerzustand gibt, ist mechanisch; ob er gut ist, nicht. **SKILL:** was drinstehen muss — NN/g-Leerzustand (Systemstatus + Pfad zur Kernaufgabe, nicht „Keine Daten"), NN/g-Fehlermeldung (sichtbar, in Nutzersprache, konstruktiv, nahe der Ursache), GOV.UK-Validierungsmuster für Formulare (Error-Summary oben, Fokus dorthin, identischer Text am Feld). |
| **f** | **Microcopy** (2f) | **überwiegend SKILL, mit einem gateable Splitter** | **SKILL:** eine **UI-Text-Tabelle als Teil der DSN** — jede Beschriftung, jeder Button, jeder Leerzustand, jede Fehlermeldung, jede Bestätigung, mit dem ISO-24495-1-Grundsatz „Leser zuerst" und einem festgelegten Ton aus dem Design-Anker (3a). Ausdrücklich **in** der DSN, nicht als Zweitdatei — sonst entsteht die zweite Wahrheit, die der Harness bisher vermieden hat. **GATE:** eine Sperrliste von Platzhaltern in sichtbaren Textknoten der eingefrorenen DSN — `Lorem ipsum`, `Click here`, `No data available`, `Item 1`, `Welcome!`, `TODO`, `Placeholder`, `Your text here`. **Fehlschlag:** wörtlicher Treffer → Block mit Fundstelle. Das ist eine Trivialprüfung, aber sie fängt das sichtbarste KI-Merkmal, und sie kann nicht falsch-positiv sein, wenn die Liste konservativ bleibt. |
| **g** | **Heuristische Evaluation** (2g) | **SKILL — bewusst kein Gate** | Vor dem Einfrieren der Phase-2-Revision: die 10 Heuristiken × die Kern-Views, Befunde mit NN/g-Severity 0–4; alles ≥ 3 wird vor dem Freeze behoben oder als Decision-Item mit Begründung offen dokumentiert. **Warum kein Gate:** NN/g selbst weist aus, dass Einzelbewerter stark streuen (deshalb die Empfehlung von 3–5 Evaluatoren) — ein Gate auf „Heuristik-Abschnitt vorhanden" prüft Anwesenheit, nicht Urteil, und lädt zum Abhaken ein. Das wäre ein Gate, das vorgibt erzwungen zu sein, ohne es zu sein — genau das, was die Verfassung verbietet. |
| **h** | **Inventarschicht / Atomic Design** (2g) | **GATE, mit ehrlichem Kostenhinweis** | Die DSN führt einen Inventarabschnitt (`data-component="<name>"`); alle in `[data-view]`-Teilbäumen verwendeten Klassennamen müssen entweder dort deklariert oder in einer deklarierten Utility-Allowlist enthalten sein. **Fehlschlag:** „class `.stat-card-alt` used in view ‚dashboard' is declared by no component" → Block. Wirkung: die fünf Views können nicht fünf eigene Karten erfinden — das ist der strukturelle Kern der Beschwerde „wirkt zusammengewürfelt". **Kosten ehrlich:** ohne grosszügige Utility-Allowlist wird dieser Gate laut. Ich würde ihn zuletzt bauen und zunächst als Warnung, nicht als Block, laufen lassen — was heisst: **nicht als Integritätsgate**, sondern als `kit_checks`-Warnung, bis Erfahrungswerte da sind. |
| **i** | **Performance-Budget** (2h) | **SKILL — mit Wiederverwendung eines vorhandenen Gates** | Die SKILL verlangt, dass die Designerin **ein `INV` vorschlägt**: `INV-INP-P75` mit `check: {kind: test, ref: <playwright/lighthouse-nodeid>}`. Dann greift die Mechanik, die II.2 bereits hat: „Der State-Validator (fail-closed) prüft EXISTENZ und Sammelbarkeit des referenzierten Tests; fehlt er, gilt die Invariante als `unverified` und blockiert Merge/Abnahme." **Null neuer Gate-Code.** Ausserdem: die SKILL soll die beiden Zahlen trennen — 100 ms = Wahrnehmung (Nielsen, Entwurfsziel), 200 ms INP p75 = Feldmetrik (Google, Akzeptanzkriterium). |
| **j** | **Kontrastzahlen** (2c) | **SKILL-Präzisierung, danach vom Gate in 3c abgedeckt** | „WCAG AA contrast" → „4.5:1 Text (1.4.3), 3:1 Grosstext, 3:1 UI-Komponenten und grafische Objekte (1.4.11), in **beiden** Themes". Ohne Zahlen ist der Satz eine Behauptung; mit Zahlen prüft ihn der axe-Lauf. |

---

## 4. Die drei wirksamsten Ergänzungen, in Reihenfolge

### 1. Design-Anker als Decision-Item + Anker-Referenz-Gate bei der DSN-Promotion (3a)

Greift die publizierte Hauptursache direkt an: *contextual anchoring* aus Shin et al. ist die einzige der drei Interventionsebenen, die ein Werkzeug erzwingen kann, und sie fehlt hier vollständig. Sie verändert, **was überhaupt erzeugt wird** — alle anderen Punkte prüfen nur, was schon da ist. Ausserdem ist es der einzige Vorschlag, der über einen einzelnen PR hinaus wirkt: ohne Anker ist jeder neue PR ein neuer Modell-Prior.

**Kosten:** kein neuer Item-Typ (Decision hat bewusst keinen Statusautomaten, §9) — aber eine §6-Ownership-Zeile, ein Freigabeweg für den Anker (er gehört inhaltlich in die **scope**-Freigabe des ersten UI-PRs), ~60–80 Zeilen Promotionsprüfung, und eine zusätzliche Frage-Runde am Projektanfang, die der PM stellen muss. Risiko: bei kleinen Projekten Overhead — deshalb an `class ≥ normal` binden, wie es II.2 für die Designerin ohnehin tut.

### 2. Token-Disziplin-Gate bei der DSN-Promotion (3d)

Weil es die Voraussetzung für alles ist, was der User am Frontend sehen will: solange der visuelle Vertrag Farbliterale enthält, ist „der Frontend hat sich nicht ans Design gehalten" nicht entscheidbar. Die drei Teilprüfungen sind billig, deterministisch, und die Theme-Paritätsprüfung fängt einen Fehler, der real und peinlich ist (halb fertiger Dark Mode). Und es erzwingt die Material-3-Trennung ohne ein einziges neues Werkzeug.

**Kosten:** ~150 Zeilen plus Tests. Die reale Arbeit steckt in der Allowlist (Gradienten, Schatten, `currentColor`, SVG-Fills) — dafür ein bis zwei Iterationen an echten DSN-Dateien einplanen. Zusätzlich: die SKILL muss die Blockstruktur der DSN vorschreiben (ein `:root`, ein `[data-theme="dark"]`), sonst ist nichts extrahierbar.

### 3. Zustandsmatrix pro View + UI-Text-Tabelle, mit Präsenz-Gate (3e + 3f)

Füllt die grösste inhaltliche Lücke des Vertrags. Heute übergibt die Designerin einen Ideal-State ohne Text-Kontrakt; der Frontend erfindet beides — Leer-/Fehlerzustand und die Wörter. Genau dort landet die Lieblosigkeit, die der User sieht. Das Präsenz-Gate ist mechanisch sauber begrenzt (dass etwas existiert ≠ dass es gut ist), und die Platzhalter-Sperrliste ist der billigste hochwirksame Check im ganzen Paket.

**Kosten:** die höchsten von den dreien, weil sie **rollenübergreifend** ist: `data-view`/`data-state` muss auch in `frontend-developer/SKILL.md` (Mockup-as-Base) und in `quality-engineer/SKILL.md` (Screenshot-Matrix) landen, sonst driften die drei Rollen auseinander. Und die DSN wird spürbar grösser — bei fünf Views mal vier Zuständen mal zwei Themes. Gegenmassnahme: Zustände als CSS-Klassen-Varianten derselben Markup-Basis, nicht als kopierte Views; das muss die SKILL explizit vorschreiben, sonst produziert das Modell 40 duplizierte Blöcke.

---

## 5. Was gegen populäre Empfehlungen für diese Rolle spricht

### a) Storybook als Komponentenvertrag — hier falsch

Die Wunschliste (`docs/POST_V2_WISHLIST.md`, Zeile 22) nennt „Storybook als Komponentenvertrag". Für diesen Harness wäre das ein **Rückschritt**. Der Harness hat bereits genau das, was die Branche als Lösung des Drift-Problems fordert: **eine** eingefrorene, gehashte, per `design_ref` gebundene Datei, aus der der Frontend das Markup übernimmt. Storybook würde eine zweite Komponentendefinition mit eigenem Build, eigenem Backlog und eigenem Release-Zyklus danebenstellen — und die dokumentierte Standardfolge ist Drift: „When the canonical component definition lives in multiple tools that don't reference each other, you have three sources of truth, which means you have zero." https://www.magicpatterns.com/blog/design-system-maintenance · https://help.zeroheight.com/hc/en-us/articles/36473744204955-Should-you-document-your-design-system-in-Storybook
Das einzig Übernehmenswerte aus dieser Ecke ist **visuelle Regression in CI** — und die kann QA mit Playwright direkt gegen die eingefrorene DSN fahren, ohne Storybook. Achtung, `quality-engineer/SKILL.md` verbietet dort bereits explizit Pixel-Diffing und Paletten-Matrizen nach einem realen Fehlschlag („burned 3 gate rounds on a 160-combo sweep") — jede Empfehlung in diese Richtung muss eng gefasst sein: Default-Palette, ein Theme, ein Lauf.

### b) DTCG-`tokens.json` exportieren — hier nicht

Naheliegend, weil die Spezifikation gerade stabil wurde. Aber: (i) sie ist **kein W3C-Standard**, sondern ein Community-Group-Report; (ii) ihr Zweck ist **Werkzeug-Austausch** (Figma ↔ Style Dictionary ↔ iOS/Android) — ein Problem, das dieser Harness nicht hat, weil er kein Figma und keine native Plattform bedient; (iii) eine `tokens.json` neben der DSN wäre die zweite Wahrheit, die der Harness sonst konsequent vermeidet. Empfehlung: die **Namenskonvention** von DTCG/Material 3 übernehmen (das ist der Wert), das **Dateiformat** nicht. Erst wenn ein Projekt tatsächlich nach iOS/Android exportiert, wird die Frage neu gestellt. https://www.designtokens.org/tr/drafts/format/

### c) „Skeletons statt Spinner" als Regel — die Evidenz ist umstritten

Die SKILL stellt das heute als Regel auf („skeletons/placeholders over spinners"). Vigets Test mit 136 Teilnehmern fand Skeleton Screens **auf allen Metriken am schlechtesten** in der wahrgenommenen Wartedauer — mit der wichtigen Nuance, dass langsame, gleichmässige Bewegung besser abschnitt als schnelle, und mit ausdrücklich eingeräumter kleiner Stichprobe. https://www.viget.com/articles/a-bone-to-pick-with-skeleton-screens · Die ECCE-2018-Studie fand das Gegenteil für wahrgenommene Geschwindigkeit, aber **langsameres Auffinden von Inhalten beim Erstbesuch**: https://dl.acm.org/doi/10.1145/3232078.3232086
**Empfehlung:** von Regel auf Bedingung herabstufen — Skeletons nur, wenn das Layout vorab bekannt ist, die Platzhalter inhaltsförmig sind und die Bewegung langsam und gleichmässig läuft; sonst ein bestimmter Fortschrittsindikator. Und, weil die SKILL sonst genau darin gut ist: die Evidenzlage als umstritten benennen, statt eine Zahl zu erfinden.

### d) APCA statt WCAG-2-Kontrast — noch nicht

Die Kritik an der WCAG-2-Formel ist fachlich ernstzunehmen (ignoriert räumliche Frequenz, symmetrisch obwohl menschliches Sehen es nicht ist, überschätzt Kontrast im dunklen Bereich — deshalb unzuverlässig für Dark Mode). Aber: die Kontrastarbeit wurde im Juli 2023 **aus dem WCAG-3-Working-Draft entfernt**, der Algorithmus ist dort „yet to be determined", APCA ist Kandidat, nicht Norm — und WCAG 2.x AA ist der rechtlich massgebliche Massstab (EAA/EN 301 549). https://github.com/w3c/wcag3/issues/29 · https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html
**Empfehlung:** Gate auf WCAG 2.x rechnen; APCA höchstens als beratende Zweitzahl in der SKILL, nie als Blockkriterium. Und WCAG 3 nicht als „kommt bald" in Prosa aufnehmen — es ist seit Jahren nicht bereit: https://yatil.net/blog/wcag-3-is-not-ready-yet

### e) Ein grüner axe-Lauf ist keine Barrierefreiheit

Wird der Gate aus 3c gebaut, ist die grösste Gefahr, dass QA und PM ihn als Konformitätsnachweis lesen. Deque misst 57 % des Befundvolumens als automatisch vollständig abgedeckt — bei einer Regelbibliothek, die bewusst falsch-positive Befunde vermeidet und damit konservativ zählt. Der Gate-Text muss das aussprechen, und die Urteilsprüfung in `quality-engineer` muss bleiben. https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/

### f) Atomic Design als Vokabular — nur die Disziplin übernehmen

Atoms/Molecules/Organisms ist als Denkmodell wertvoll, als Benennungsschema in Teams notorisch streitanfällig (ist ein Suchfeld ein Molekül oder ein Organismus?). Für den Harness zählt nur: **eine Inventarschicht existiert, und Views werden daraus komponiert** (3h), plus die Trennung Template/Page. Das biologische Vokabular würde ich nicht in die SKILL schreiben.

### g) Ein Präsenz-Gate auf „heuristische Evaluation durchgeführt" — nicht bauen

Verlockend, weil billig. Aber es prüft, dass ein Abschnitt existiert, nicht dass jemand nachgedacht hat — und ein Modell füllt zehn Zeilen mühelos. Es wäre ein Gate, dessen Fehlschlag ich zwar beschreiben kann, dessen **Bestehen** aber nichts aussagt. Das verletzt die Regel aus dem Auftrag in der zweiten Richtung: Anleitung darf nicht so tun, als wäre sie erzwungen — und ein Gate darf nicht so tun, als prüfe es Qualität.

---

## Randnotizen

- **Ein Widerspruch in der SKILL selbst**, unabhängig von der Recherche: die Qualitätslatte fordert „Restraint … calm whitespace" und Referenzen wie Raycast/Linear (dichte, kleine Ziele) — und gleichzeitig gilt SC 2.5.8 mit 24×24 CSS px auf AA. Die SKILL sollte diese Spannung benennen und auflösen (Ausnahme über Abstand statt über Grösse), sonst produziert sie zuverlässig Designs, die der Gate aus 3c blockt.
- **`design/revisions/DSN-nnnn.rNN.html` hat kein Companion-YAML**, anders als ARC und WFR (II.2). Alle oben vorgeschlagenen Metadaten (Anker-Referenz, Direction-Achsen, Breakpoint-Liste für die Zielgrössenmessung) müssen deshalb **in der HTML** stehen — `<meta>` und `data-*`. Ein Companion-YAML für DSN einzuführen wäre die Alternative, zieht aber Schemaarbeit nach sich; ich empfehle die HTML-interne Variante, weil sie die Self-Contained-Eigenschaft erhält, auf der II.6 besteht.
- **Reichweite:** `research-team` und `office-team` haben keine Designrolle; die dortigen nutzerseitigen Textrollen (`office-team/skills/product-editor`, `shop-curator`) erwähnen weder Barrierefreiheit noch Textstandards. ISO 24495-1 wäre dort einschlägig — ausserhalb dieses Auftrags, aber vermerkenswert, falls die Kits gemeinsam gehärtet werden.

---

**Quellen:**
[CHI 2021 Homogenization of Web Design (ACM)](https://dl.acm.org/doi/abs/10.1145/3411764.3445156) ·
[dass. Volltext-PDF](https://aux.engineering.ucsc.edu/publications/Goree_Doosti_Crandall_Su-HomogenizationWebDesign-CHI21.pdf) ·
[Usable but Conventional (arXiv 2605.15124)](https://arxiv.org/abs/2605.15124) ·
[Interrogating Design Homogenization in Web Vibe Coding (arXiv 2603.13036)](https://arxiv.org/abs/2603.13036) ·
[WCAG 2.2 (W3C Recommendation)](https://www.w3.org/TR/WCAG22/) ·
[Understanding SC 2.5.8 Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) ·
[WCAG 2.2 als W3C-Empfehlung (EU Accessible Centre)](https://accessible-eu-centre.ec.europa.eu/content-corner/news/wcag-22-officially-w3c-recommendation-2023-10-06_en) ·
[WAI-ARIA Authoring Practices Guide — Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/) ·
[DTCG: erste stabile Fassung 2025.10](https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/) ·
[Design Tokens Format Module](https://www.designtokens.org/tr/drafts/format/) ·
[Material Design 3 — Design tokens](https://m3.material.io/foundations/design-tokens) ·
[Nielsen — 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) ·
[NN/g — Severity Ratings](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/) ·
[NN/g — Response Time Limits](https://www.nngroup.com/articles/response-times-3-important-limits/) ·
[NN/g — Empty States](https://www.nngroup.com/articles/empty-state-interface-design/) ·
[NN/g — Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/) ·
[NN/g — Errors in Forms](https://www.nngroup.com/articles/errors-forms-design-guidelines/) ·
[GOV.UK — Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) ·
[GOV.UK — Error message](https://design-system.service.gov.uk/components/error-message/) ·
[ISO 24495-1:2023](https://www.iso.org/standard/78907.html) ·
[IPLF zur ISO-Norm](https://www.iplfederation.org/iso-standard/) ·
[Atomic Design, Kap. 2 (Brad Frost)](https://atomicdesign.bradfrost.com/chapter-2/) ·
[Scott Hurff — The UI Stack](https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/) ·
[web.dev — INP ist Core Web Vital](https://web.dev/blog/inp-cwv-launch) ·
[Deque — 57 % automatisch abgedeckt](https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/) ·
[Viget — A Bone to Pick with Skeleton Screens](https://www.viget.com/articles/a-bone-to-pick-with-skeleton-screens) ·
[ECCE 2018 — The effect of skeleton screens](https://dl.acm.org/doi/10.1145/3232078.3232086) ·
[w3c/wcag3 Issue #29 — Contrast](https://github.com/w3c/wcag3/issues/29) ·
[Roselli — WCAG3 Contrast as of April 2026](https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html) ·
[Eggert — WCAG 3 is not ready yet](https://yatil.net/blog/wcag-3-is-not-ready-yet) ·
[Magic Patterns — Design System Drift](https://www.magicpatterns.com/blog/design-system-maintenance) ·
[zeroheight — Should you document your design system in Storybook?](https://help.zeroheight.com/hc/en-us/articles/36473744204955-Should-you-document-your-design-system-in-Storybook)