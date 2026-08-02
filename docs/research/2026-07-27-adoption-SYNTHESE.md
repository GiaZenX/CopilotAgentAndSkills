## Gemessene Randbedingungen (zuerst, weil sie zwei Prämissen der Frage korrigieren)

| Datei | Zeilen | Bytes |
|---|---|---|
| `skills/product-designer/SKILL.md` | **150** (= exakt am Limit) | 12 334 |
| `skills/quality-engineer/SKILL.md` | **146** | 13 069 |
| `skills/software-architect/SKILL.md` | 99 | 8 468 |
| `skills/frontend-developer/SKILL.md` | 59 | 4 381 |
| `skills/backend-developer/SKILL.md` | 41 | 2 418 |
| `skills/project-manager/SKILL.md` | **220** (70 über) | 21 627 |

**Korrektur 1 — das Lead-Paket ist deutlich schlimmer als „3 bis 21 KB über".** Gemessen (`agents/<lead>.md` + Lead-SKILL + `constitution/AGENTS.md`, das per Import immer mitlädt): dev-team **52 779 B**, research-team **47 027 B**, office-team **36 327 B** gegen 25 KB → Überschreitung **11,3 bis 27,8 KB**, dev-team bei 2,1× Budget. Der Treiber ist nicht die Summe vieler Rollen, sondern zwei Dateien: Verfassung 23,7 KB (220 Z.) und PM-SKILL 21,6 KB (220 Z.).

**Korrektur 2 — fünf der sechs Rollen konkurrieren gar nicht um die 25 KB.** II.5 definiert das Lead-Instruktionspaket als „agent.md + Lead-SKILL + Verfassung". Designer, Frontend, Backend, Architekt und QA sind Spezialisten-Preloads; für sie bindet **nur** die ≤150-Zeilen-Regel aus II.11/3. Das verschiebt die Timing-Frage vollständig: das KB-Budget ist ein **PM-und-Verfassungs-Problem**, das Zeilenbudget ein Designer-und-QA-Problem, und die übrigen vier Rollen haben zusammen **200 freie Zeilen**.

**Korrektur 3 — heute erzwingt nichts das Zeilenbudget.** `guard_memory_budget.py` deckt `agent-memory/**`, `MEMORY.md`, Envelope und Item ab, **nicht** SKILL-Dateien; sein eigener Docstring verweist für den Rest auf „die II.11/3 shrink step". Die 150 Zeilen sind heute eine Prosaregel — genau die Kategorie, die dieses Harness sonst verbietet. Wer jetzt Text hinzufügt, wird von keinem Gate gestoppt; das ist ein Argument für Disziplin, nicht für Sorglosigkeit.

**Korrektur 4 — `references/` reist mit und kostet in beiden Budgets nichts.** `scaffold_team.ps1` kopiert Skill-Ordner mit `Copy-Item $_.FullName $d -Recurse -Force`; ein Unterordner ist installiert, ohne dass eine Zeile Infrastruktur entsteht. Er wird aber auch nicht in den Kontext injiziert — also gilt die Zweiteilung: **gate-gedeckte Erklärung darf dorthin, unerzwungene Regel nicht.**

---

## 1. Adoption je Rolle

| Rolle | WÖRTLICH übernehmen | ADAPTIEREN | SELBST schreiben (nichts Publiziertes reicht) | Lizenzpflicht |
|---|---|---|---|---|
| **product-designer** | 3–4 Z. Klischee-Kalibrierung aus `anthropics/skills` `frontend-design` (die drei KI-Looks inkl. `#F4F1EA`) + 1 Z. Vorrangregel „the brief's own words always win, including when it asks for one of these looks" | UX-Writing-Absatz derselben Datei (Verbkonsistenz Button↔Toast, „errors don't apologize", „an empty screen is an invitation to act") → Inhalt für B5/B4, Großteil nach `references/ui-copy.md` | Design-Anker (B1) als DEC mit Promotions-Auflösung · Divergenz-Achsen (B6) · Per-View-Vertrag · WCAG-2.2-Zahlen (B7) · Nielsen-Severity (B9) · B10-Korrektur. **Kein publizierter Text kennt eine Designerin, die nicht mit dem User spricht und einen eingefrorenen Vertrag nach unten übergibt.** | **Apache-2.0** (pro Skill-Ordner, kein Repo-Root-LICENSE). §4: Lizenzkopie beilegen, Änderung kennzeichnen → eine Zeile in `NOTICES.md` (`anthropics/skills`, Apache-2.0, modified). Kein Copyleft. |
| **frontend-developer** | 2 Z.: CSS-Spezifitätsfalle („`.section` vs. `.cta` heben Paddings/Margins auf") + Anti-Slop-Literale aus `web-artifacts-builder` (kein Inter, keine uniformen Radien, kein Purple-Gradient) | Black-Box-Skriptregel aus `webapp-testing` („`--help` zuerst, Quelle nicht lesen") auf `scripts/quality.py` gemünzt — **eine** Zeile, kein Skript | Mockup-as-base · `design_ref`-Bindung · jsdom≠browser-Helper · Delivery-Freshness (Bundle-Hash). Alles publizierte Frontend-Material setzt einen Agenten voraus, der Design **und** Code besitzt. | **Apache-2.0**, gleiche Attributionszeile |
| **software-architect** | **nichts** | **Form**, kein Text: die Zwei-Schwellen-Sprache aus `openai/codex` `AGENTS.md` („unter X ok, über Y neues Modul") statt Prozentregeln — kostet null Zeilen | **Alles.** A4 (`SR.contract.kind`), F1 (`options_considered`), F3 (Threat-Model als Gate statt Selbsteinschätzung), F8 (ATAM-Satzform), F5-Satz zur Abhängigkeitsrichtung. Es gibt im ganzen Feld keine Architekten-Rollendatei, die eine Entscheidungsregel statt eines Werkzeuginventars enthält (`wshobson/backend-architect.md`: 18 356 B, die aufzählen, was es gibt, und nie sagen, wann etwas falsch ist). | keine (Methodennamen wie ATAM/C4/STRIDE nennen ist keine Übernahme) |
| **backend-developer** | **nichts** | **nichts.** Normen als Referenz-ID statt Text: RFC 9457, RFC 9110 §13, OAS 3.1 — Nummer nennen, Schema **nie** in die SKILL kopieren (sonst existiert das Fehlerformat zweimal und driftet) | **Alles.** A1-Urteilsteil, F10-Muster, F11-Default, F12-Parallel-Change. Das ist die Stelle, an der das Ökosystem schweigt: `wshobson/skills/api-design-principles` nennt „Inconsistent Error Formats" als Pitfall und **kennt RFC 9457 nicht**. | keine (RFC-Nummern, kein Text) |
| **quality-engineer** | ~3 Z. Verdikt-Kalibrierung aus `google/eng-practices` („no such thing as perfect code" / `Nit:` / „don't block based only on personal style preferences") + ~5 Z. Anti-Pattern-Liste und 1 Z. „a bug without reproduction steps is just a rumor" aus `awesome-copilot/agents/qa-subagent.agent.md` | „non-discriminating assertion" aus `skill-creator` als **ein** Satz (= D2 für Prompts) · Test-Desiderata-**Vokabular** (`isolated`, `deterministic`) für D6/D11 — Begriffe, nie Text | X1-Ehrlichkeitskorrektur (Coverage „per source area" existiert nicht) · Flake-Protokoll mit Wiederholungsstatistik · Staged Testing · Delivery-Freshness · die gesamte Evidence-Mechanik | **CC BY 3.0** (eng-practices): Urheber + Titel + Lizenz-URI nennen **und Änderungen kennzeichnen**; Quelle seit 21.11.2025 archiviert (eingefrorener Text — für einen Kalibrierungssatz Vorteil). **MIT** (awesome-copilot): Copyright- + Permission-Notice in `NOTICES.md`. |
| **project-manager** | **nichts** | **Struktur, kein Text:** das Router-Muster aus `internal-comms` (Körper = Router, Detail in `references/*.md`) — der einzige Weg von 220 auf 150 Zeilen, ohne Regeln zu löschen, die die Paritätsmatrix danach verbuchen muss | **Alles Inhaltliche.** `doc-coauthoring` ist der einzige inhaltlich passende Kandidat und hat **weder LICENSE.txt noch `license:`-Frontmatter** → bei fehlendem Root-LICENSE „all rights reserved" → nicht adoptierbar. BMAD ist der einzige ernstgemeinte fremde SDLC-Rollensatz und strukturell unvereinbar (Story-Monolith mit eingebettetem „Change Log" gegen II.2 „Historie liegt in Git"). | keine — weil nichts übernommen wird. Struktur/Idee ist nicht schutzfähig. |

Zwei Sätze, die zur Ehrlichkeit gehören: **die Anthropic-Designer-SKILL schlägt unsere nicht.** Sie ist ein Briefing für einen einzelnen kreativen Agenten; unsere ist ein Prozess mit Artefakten, einem Entscheider und einem nachgelagerten Konsumenten. Und: der einzige fachlich starke Text im ganzen Feld mit permissiver Lizenz ist `google/eng-practices`. Die fachlich besten Quellen (SWE at Google: **CC BY-NC-ND** — NoDerivatives verbietet die gekürzte Fassung, die wir bräuchten; GitLab Handbook und OWASP ASVS: **BY-SA**) sind lizenziell gesperrt oder Copyleft. Das ist kein Zufall, sondern die Antwort auf die Frage.

---

## 2. Landeplatz je Adoption — SKILL, INV oder GATE

Notation der heutigen SYNTHESE-Spalte („GATE / SKILL"), plus zwei Kategorien, die sie implizit schon benutzt: **GATE-CODE** (landet in einem Gate, ohne je eine Regelzeile zu erzeugen) und **references/** (gate-gedeckte Erklärung).

| # | Adoption | Landet als | Fehlschlag (nur bei GATE) |
|---|---|---|---|
| 1 | Klischee-Kalibrierung (3 Looks) | **SKILL**, Designer Phase 1 | — bewusst kein Gate: „warmes Creme mit Serif" ist ein Look, kein Literal; ein Gate darauf wäre eines, dessen Fehlschlag niemand beschreiben kann |
| 1a | Der gate-fähige Rest: die Literale `#F4F1EA`, `font-family: Inter`, uniformer Radius | **GATE** (Inhalt der `anti_references` im B1-Anker-DEC, geprüft bei der DSN-Promotion) | *„Die gestagte `DSN-nnnn` nennt in Zeile N das Literal `#F4F1EA`; der referenzierte Design-Anker `DEC-nnnn` führt es unter `anti_references`. Promotion blockiert."* Der Umweg über den Anker ist notwendig, sonst kollidiert das Gate mit Adoption 2. |
| 2 | „the brief's own words always win" | **SKILL**, 1 Z. neben den MINIMAL-Absatz | — |
| 3 | UX-Writing-Handwerk (Verbkonsistenz, Fehler-/Leerzustandston) | **references/ui-copy.md** + 1 Zeiger-Zeile in der SKILL; projektspezifische Fälle werden **INV** mit `check` (sobald D1 steht) | — (Zeiger), Gate-Deckung durch #4 |
| 4 | Platzhalter-Sperrliste (B5) | **GATE** | *„Sichtbarer Textknoten in der gestagten DSN matcht die Sperrliste (`Lorem ipsum` / `No data available` / `Item 1` / `Click here` / `TODO`) — Datei, Zeile, Treffer genannt. Promotion blockiert."* Beschreibbar, weil es ein Literalvergleich ist. |
| 5 | CSS-Spezifitätsfalle | **SKILL**, Frontend, 1 Z. | — kein Gate: „Regeln, die sich gegenseitig aufheben" verlangt eine Kaskadenauswertung, die wir nicht haben. Ausdrücklich als Urteilsheuristik markieren. |
| 6 | Black-Box-Skriptregel (`--help`, Quelle nicht lesen) | **SKILL**, Frontend + QA, 1 Z. je | — |
| 7 | `wait_for_load_state('networkidle')` vor DOM-Inspektion | **GATE-CODE** in `kit_browser_checks.py` (C1/C2) | Keine neue Regel — eine Codezeile im Gate. Beste Kompressionsrate der ganzen Recherche: null SKILL-Zeilen für einen benannten Flake-Grund. |
| 8 | Verdikt-Kalibrierung: ein `fail` benennt AC/INV/Guideline, sonst `Nit:` in `followups` | **SKILL** (2 Z.) **+ GATE** beim Evidence-Capture, Verwandter von G1 | *„`harness evidence --result fail` ohne auflösbare AC-/INV-/Guideline-ID in den Feldern → Capture verweigert; Meldung: ‚ein `fail` benennt den verletzten Vertrag; Geschmacksbefunde gehören als `Nit:` in `followups`.'"* **Grenze, die mitgesagt werden muss:** das Gate prüft Auflösbarkeit, nicht Berechtigung. Sein *Bestehen* sagt nur „eine existierende ID ist genannt" — dieselbe Klasse wie G1, und der Gate-Text darf nicht mehr behaupten. |
| 9 | QA-Anti-Pattern-Liste (5 Z.) | **SKILL**, ausdrücklich „nicht erzwungen", bis D2/D3 stehen; zwei der fünf werden danach zu **GATE** (D2 assertionsfrei, D3 Skip ohne Reason) | D2: *„`tests/x.py::test_y` enthält keinen `assert`/`pytest.raises`-Knoten (AST-Walk, kein Regex)."* D3: *„`--junitxml` meldet `skipped` ohne `message`-Attribut"* bzw. *„kritischer Marker (`real_run`/`e2e`/`browser`) übersprungen."* |
| 10 | „a bug without reproduction steps is just a rumor" | **SKILL**, QA Schritt 6 — und es ist die Begründung für das Pflichtfeld `BUG.repro` aus II.2, also bereits gate-gedeckt | — |
| 11 | „non-discriminating assertion" | **SKILL** (1 Satz) **+ Prüfkriterium in der Paritätsmatrix-Checkliste** von II.11/3 | — |
| 12 | Test-Desiderata-Vokabular | **SKILL**-Vokabular für D6/D11 | — |
| 13 | Zwei-Schwellen-Form (codex) | **Schreibregel für Phase 3**, kein SKILL-Text | — |
| 14 | Router-Muster (PM) | **Struktur** von `project-manager/SKILL.md` | — |

Bilanz in Zeilen: **≈ 5 Designer · 2 Frontend · 0 Architekt · 0 Backend · ≈ 9 QA · 0 PM** in den SKILL-Körpern. Plus zwei Gates (1a, 4), eine Gate-Erweiterung (8), eine Codezeile (7), eine `references/`-Datei.

---

## 3. Die Timing-Frage — Empfehlung

**Empfehlung: nach Landeplatz staffeln, nicht nach Rolle. Gates und Gate-Code SOFORT, SKILL-Text WÄHREND der Kürzung — mit einer namentlichen Ausnahmeliste von vier Zeilen.**

Die Argumente, in der Reihenfolge ihres Gewichts:

**a) Ein Drittel des Ertrags konkurriert um gar kein Budget.** Adoptionen 1a, 4, 7 und die Gate-Hälfte von 8 sind Gates bzw. Gate-Code. II.11/3 verlangt Gates ohnehin **vor** der Kürzung („Kürzung erst NACH den ersetzenden Gates"). Sie jetzt zu bauen ist nicht „vorher adoptieren", sondern die vorgeschriebene Reihenfolge. Sie später zu bauen, verschiebt die Kürzung.

**b) „Erst schreiben, dann kürzen" ist im Volumen keine Doppelarbeit, in der Begründung schon.** 16 Zeilen tippen und später wieder entfernen kostet Minuten. Was es kostet, ist eine **Paritätsmatrixzeile pro Zeile** — jede in Phase 3 entfernte Regel muss belegt werden. Wer heute Text hinzufügt und in Phase 3 kürzt, hat die Beweislast zweimal, und beim zweiten Mal für Text, den er selbst gerade erst eingeführt hat. Das ist das eigentliche Doppelarbeitsargument, und es zielt auf **Text**, nicht auf Gates.

**c) Die beiden Rollen mit dem meisten adoptierbaren Material haben null Reserve.** `product-designer` steht bei **exakt 150** Zeilen, `quality-engineer` bei **146**. Dort ist „hinzufügen" ohne „streichen" mechanisch unmöglich. Genau dieser Tausch ist aber das, wofür die Paritätsmatrix da ist: „schwache Prosazeile raus, belegte Fremdzeile rein" ist **eine** Matrixzeile mit einer Begründung, wenn es in einem Vorgang passiert — und zwei unverbundene Änderungen, wenn nicht. Beispiel, das den Punkt trägt: der Designer-Satz „Fence-sitting ‚safe' defaults ARE the AI-slop to avoid" (Urteil ohne Verfahren) gegen die Klischee-Kalibrierung mit Hex-Wert (falsifizierbar) — das ist ein 1:1-Tausch, kein Zuwachs, und er gehört in dieselbe Zeile der Matrix.

**d) Der PM ist ein anderer Fall und darf nicht mitgezogen werden.** 220 → 150 Zeilen bei 52,8 KB Lead-Paket gegen 25 KB: dort ist die Adoption ohnehin **null Text**, nur das Router-Muster. Es gibt keinen Grund, für den PM auf Phase 3 zu warten — das Router-Muster **ist** die Kürzungsarbeit. Es sollte im selben Zug wie die Verfassungskürzung passieren, weil die 25 KB nur gemeinsam zu erreichen sind (Verfassung 23,7 KB + PM-SKILL 21,6 KB + agent.md 7,4 KB — kein einzelner Schnitt reicht).

**e) „Danach" ist die einzige Option, die klar falsch ist.** Nach der Kürzung ist jeder Zuwachs ein Regress gegen ein frisch erreichtes Budget, ohne Beleg-Rahmen, gegen ein Gate, das es dann hoffentlich gibt.

**Die Ausnahmeliste — vier Zeilen, die sofort dürfen,** weil ihre Rolle Reserve hat *und* sie einen benannten, reproduzierbaren Defekt beschreiben (dasselbe Genre wie die vorhandene Zeile „form controls do NOT inherit fonts by default — a real run shipped a wrong-font button"):
1. CSS-Spezifitätsfalle → `frontend-developer` (59/150).
2. Anti-Slop-Literale → `frontend-developer`.
3. Black-Box-Skriptregel → `frontend-developer`.
4. X1-Ehrlichkeitskorrektur in `quality-engineer` Schritt 4 („coverage ≥ threshold globally **AND per source area**" behauptet eine Prüfung, die es nicht gibt) — **spart** eine halbe Zeile und ist ohnehin sofort fällig (SYNTHESE D6).

Und der Druckausgleich, der die Frage für den größten Posten auflöst: **`references/ui-copy.md` kann jederzeit und in beliebiger Länge geschrieben werden**, weil sie in keinem der beiden Budgets zählt. Sobald das Sperrlisten-Gate (#4) steht, ist sie gate-gedeckt und darf dort leben. Die Timing-Frage betrifft damit nur noch ~16 Körperzeilen.

---

## 4. Was die 150 Zeilen für Adoption bedeuten

Die Zahl, an der sich alles entscheidet: `frontend-design/SKILL.md` ist 8 260 B / 55 Zeilen / 1 336 Wörter; auf unsere Umbruchbreite reformatiert **121 Zeilen** — 81 % des Budgets einer ganzen Rolle für eine einzige Fremddatei. Wortlaut-Übernahme ist rechnerisch ausgeschlossen, unabhängig von der Qualität. Verwertbar sind daraus ~12 Zeilen: **Verdichtungsverhältnis 10:1.** Das ist die realistische Erwartung an jede publizierte Datei, und deshalb ist die richtige Frage nie „was passt hier rein", sondern „in welchen der fünf Eimer fällt jeder Satz".

**Eimer 1 — in den SKILL-Körper.** Nur Sätze, die (a) eine Entscheidung ändern, welche die Rolle im nächsten Schritt trifft, und (b) einen benennbaren Fehlschlag haben. Formregel, aus `openai/codex` übernommen: **jede Zeile steht entweder als „Regel + ihr Erzwinger" oder trägt das Etikett „nicht erzwungen". Eine Zeile ohne beides wird gestrichen, nicht gekürzt.** Das ist X1 („eine falsche Schutzbehauptung ist schlimmer als eine fehlende Prüfung") als Schreibregel.

**Eimer 2 — in `references/`.** Tabellen, Beispielsammlungen, Begründungsprosa. **Nur wenn ein Gate die Regel erzwingt** — das Gate setzt durch, die Referenz erklärt. Eine unerzwungene Regel nach `references/` zu schieben ist die Degradierung in genau den Fehler, den dieses Harness benennt: eine Regel, die das Modell vielleicht nicht liest, die aber als vorhanden verbucht ist. Praktische Folge für Phase 3: die Paritätsmatrix braucht **eine dritte Kategorie** neben „durch Gate ersetzt" und „gestrichen" — *„nach `references/` verschoben, weiterhin autorisiert, gedeckt durch Gate X"*.

**Eimer 3 — in ein Gate oder in Gate-Code.** Alles, was ein Literal, eine Präsenz, eine auflösbare ID oder eine Zahl ist. Kostet null SKILL-Zeilen. `networkidle` ist der Musterfall: als Regel zwei Zeilen in zwei SKILLs, als Codezeile in `kit_browser_checks.py` null.

**Eimer 4 — in ein `INV`-Item.** Der am meisten unterschätzte Eimer, und die eigentliche Antwort auf „eine 400-Zeilen-SKILL". Ein großer Teil publizierter Skills ist **Projektinhalt, der als Kit-Regel getarnt ist** — Kontrastböden, Reihenfolgen, Pflichtbeschriftungen, Verb-Paare. Bei uns entsteht das pro Projekt als `INV` mit `check.ref`, nicht pro Kit als Regelzeile. Sobald D1 (`INV.check.ref` auflösen) steht, ist das der billigste Landeplatz überhaupt: keine Kit-Zeile, trotzdem gate-fähig.

**Eimer 5 — streichen.** Tautologien („Elegance is executing the chosen vision well"), Merksätze ohne Falsifizierbarkeit (Chanel/Spiegel/ein Accessoire weniger), Zahlen ohne Herkunft („coverage > 90%", „<$100/month → Serverless"), optionale Schutzbehauptungen („screenshots **if your environment supports it**"), unbenannte Qualitätsböden („build to a quality floor **without announcing it**") und das gesamte Genre Fähigkeitsinventar („Service discovery: Consul, etcd, Eureka, Kubernetes"). Prüffrage, die jeden dieser Fälle in einem Schritt erledigt: **kann ich den Satz aufschreiben, mit dem diese Regel scheitert?**

Konkret an `frontend-design` durchgerechnet: 55 Zeilen → 12 nützlich → **5 in den SKILL-Körper, 6 nach `references/ui-copy.md`, 1 in eine Gate-Literalliste, 43 gestrichen.**

---

## 5. Was aus der eigenen Wunschliste diese Recherche ablehnt

- **Storybook als Komponentenvertrag** — nein. Der Harness hat bereits genau das, was die Branche gegen Drift fordert: **eine** eingefrorene, gehashte, per `design_ref` gebundene Datei. Storybook stellt eine zweite Komponentendefinition mit eigenem Build und Release-Zyklus daneben; die dokumentierte Standardfolge ist Drift. Der einzige übernehmenswerte Teil (a11y im CI) ist C1 auf dem bereits laufenden Preview-Server.
- **Ein fertiges publiziertes Rollen-Set übernehmen** (wshobson 203 Agents / VoltAgent / BMAD) — nein. wshobson und VoltAgent sind Fähigkeitsinventare (18 KB, die aufzählen, was existiert, und nie sagen, wann etwas ein Fehler ist). BMAD ist der einzige ernstgemeinte SDLC-Satz und **strukturell inkompatibel**: Story-Markdown als mutierende Monolithdatei mit eingebettetem „Change Log" gegen II.2 („Historie liegt in Git") und gegen Datei-pro-Item; sein Qualitätsgate ist eine 25-Häkchen-Selbstattestierung mit „Completion Score: {{completed}}/{{total}}" — genau das Anti-Pattern aus SYNTHESE §3 („ein Gate, dessen *Bestehen* nichts aussagt").
- **`doc-coauthoring` adoptieren** — nein, obwohl es inhaltlich am besten auf unseren PM abbildet: keine `LICENSE.txt`, kein `license:`-Frontmatter, kein Repo-Root-LICENSE → Default „all rights reserved".
- **`docx`/`pdf`/`pptx`/`xlsx` für das office-team** — nein, hartes Nein. Deren `LICENSE.txt` verbietet ausdrücklich „Create derivative works based on these materials"; auch paraphrasiert nicht in ein ausgeliefertes Kit.
- **Anthropics „do a lot of this planning in your thinking, and only show ideas to the user when you have higher confidence"** — nein. Das ist wörtlich der dokumentierte PM-Realfehler dieses Harness (Freigabe für eine Zusammenfassung, die nur im Thinking existierte; der User entschied blind).
- **„Build to a quality floor without announcing it"** — nein. Ein nicht benannter Qualitätsboden ist nicht gate-fähig; wir nennen Zahlen (150–250 ms, WCAG AA, <100 ms) und bekommen dafür C1/C3.
- **`disallowed-tools: AskUserQuestion` statt der Prosaregel „du sprichst nicht selbst mit dem User"** — nein. Das Feld ist Claude-Code-spezifisch (in der Agent-Skills-Spec steht nur `allowed-tools`, als *experimental*) → der Codex-Mirror bekäme nichts, und II.4 verlangt beweisbare Provider-Parität; außerdem „the restriction clears when you send your next message" — eine Pro-Turn-Gewährung ist keine Pro-Subagent-Garantie. Exakt ein Schutz, der nur als erzwungen *liest*.
- **Gebündelte `scripts/` neben der SKILL** (wie `webapp-testing` es macht) — nein. Unsere ausführbaren Helfer leben in `templates/repo/scripts/` und `hooks/`, werden von Gates gerufen und sind von `gate_write_scope`/Hashing erfasst. Ein zweites Executable neben der SKILL wäre ein Skript, das die Gates nicht kennen. Die **Regel** übernehmen, das Skript nicht.
- **`description` als Trigger-Fläche aufpolieren** — größtenteils wirkungslos: bei preloaded Subagent-Skills wird der volle Inhalt beim Start injiziert (**KORREKTUR 2026-08-02:** für den SESSION-Agenten gemessen widerlegt, für den Subagent-Spawn ungemessen -- `tools/provider_observations.json`), die Description triggert dort gar nicht. Relevant bleibt sie nur für `project-manager` (Session-Agent) und `/name`-Aufrufe; dort könnte statt „Preloaded into the X subagent." die Abgrenzung „wann NICHT diese Rolle" stehen — Frontmatter, null Körperbudget.
- **Mitgeführt aus SYNTHESE §3, weil es weiterhin auf der Wunschliste steht:** DTCG `tokens.json` als Dateiformat (Namenskonvention ja, Format nein) · handgepflegte Zweitfassung des Plandiagramms · Markdown-Kanban · Drag-and-Drop-Board · Coverage-Schwelle auf 90 % · Testpyramiden-Quote · Story Points/Velocity · DORA-Dashboard · Pixel-Visual-Regression · INP als Gate.

**Und die eine Aussage der Herausgeber selbst, die alles begrenzt** (`anthropics/skills` README): „**These skills are provided for demonstration and educational purposes only.** … These skills are meant to illustrate patterns and possibilities." Das ist die Erklärung der Autoren, dass es sich nicht um produktive Regeldateien handelt — was das Verdikt trägt: **Sätze adoptieren, Prozesse nicht, und für vier von sechs Rollen selbst schreiben.**

**Relevante Pfade:** `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\{product-designer,frontend-developer,software-architect,backend-developer,quality-engineer,project-manager}\SKILL.md` · `...\team-kits\dev-team\constitution\AGENTS.md` (220 Z. / 23 733 B) · `...\team-kits\dev-team\agents\project-manager.md` (92 Z. / 7 419 B) · `...\team-kits\dev-team\hooks\guard_memory_budget.py` (Docstring Z. 36–38: die Kürzung darf die Prosaregel nicht auf Gate-Stärke hin streichen) · `...\team-kits\scaffold_team.ps1` Z. 480–489 (rekursive Skill-Kopie → `references/` reist mit) · `...\docs\research\2026-07-27-SYNTHESE.md` (§1 GATE/SKILL-Spalte, §3, §4/D7) · `...\docs\HARNESS_V2_SPEC.md` II.5 und II.11/3.