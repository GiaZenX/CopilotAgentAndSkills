# Recherche: Adaptierbare Rollen-Instruktionssets aus dem publizierten Ökosystem

**Vorbemerkung zum Budget, weil sie das Ergebnis vorentscheidet.** Gemessen im Repo: `software-architect` 99 Z., `backend-developer` 41 Z., `quality-engineer` 146 Z., `project-manager` 220 Z. Gegen II.5 (≤150 Zeilen je Lead-SKILL, ≤25 KB Paket) ist der PM bereits über, QA vier Zeilen unter der Grenze. Der **Netto-Zeilenhaushalt für Übernahmen ist null bis negativ.** „Adaptieren" kann hier deshalb nur heißen: *schwächeren Eigentext durch besser belegten Fremdtext gleicher oder geringerer Länge ersetzen*. Jeder Kandidat unten wird an dieser Latte gemessen, nicht an „ist das interessant".

---

## 1. Fundübersicht

| Quelle | URL | Lizenz | Größe (gemessen) | Rollen | Urteil in einer Zeile |
|---|---|---|---|---|---|
| **google/eng-practices** (Code Review) | https://google.github.io/eng-practices/ | **CC BY 3.0** | 12 Seiten, Kernseite ~1.400 W. | QA, Auditor, Architekt | **Bester Fund.** Echte Entscheidungsregeln mit Begründung; ~8 Zeilen davon sind sofort übernehmbar. Repo seit 21.11.2025 archiviert — Text eingefroren, Lizenz erlaubt Fork. |
| **openai/codex `AGENTS.md`** | https://github.com/openai/codex/blob/main/AGENTS.md | **Apache-2.0** | ~9 KB | Backend, Architekt | **Zweitbester.** Inhalt ist Rust/repo-spezifisch und wertlos für uns — die **Form** ist vorbildlich: jede Regel nennt das Kommando, das sie erzwingt. |
| **github/awesome-copilot `agents/qa-subagent.agent.md`** | https://github.com/github/awesome-copilot | **MIT** | 4.373 B / 94 Z. | QA | Einziger Rollentext im ganzen Feld, der **Anti-Pattern statt Fähigkeiten** schreibt. ~10 Zeilen brauchbar. |
| github/awesome-copilot `instructions/**` | dito | MIT | **15–64 KB je Datei** (`azure-logic-apps` 64.287 B, `security-and-owasp` 30.368 B, `a11y` 27.608 B) | alle | Größenordnung allein disqualifiziert: eine einzige Datei sprengt das 25-KB-Gesamtpaket. |
| github/awesome-copilot `agents/se-system-architecture-reviewer.agent.md` | dito | MIT | 4.371 B / 165 Z. | Architekt | Entscheidungsbäume nach Nutzerzahl und **Hosting-Budget** („<$100/month → Serverless"). Frei erfundene Schwellen ohne Quelle. Nichts. |
| **wshobson/agents** (203 Agents, 175 Skills) | https://github.com/wshobson/agents | MIT | `backend-architect.md` **18.356 B**; `test-automator.md` 2.291 B | Backend, Architekt, QA | Technologie-**Inventar**, keine Regel. 18 KB, die aufzählen was es gibt, und nie sagen, wann etwas ein Fehler ist. |
| wshobson `skills/api-design-principles` | dito | MIT | 3.603 B / 111 Z. | Backend | Lehrbuch-Listicle („Use plural nouns for collections"). Bestätigt indirekt SYNTHESE-A2: nennt „Inconsistent Error Formats" als Pitfall, kennt aber RFC 9457 nicht. |
| wshobson `skills/multi-reviewer-patterns` | dito | MIT | 5.192 B / 127 Z. | QA, Auditor | Dedup-/Severity-Merge-Regeln sind das einzig mechanisch Formulierte im ganzen Repo — für uns trotzdem unbrauchbar (wir haben genau **einen** QA-Reviewer, kein Konsolidierungsproblem). |
| **VoltAgent/awesome-claude-code-subagents** | https://github.com/VoltAgent/awesome-claude-code-subagents | MIT | jede Datei **6,4–7,7 KB** — auffällig gleichförmig, generiert | alle | Nomenphrasen-Taxonomie plus erfundene Zahlen. Nichts. |
| **BMAD-METHOD** | https://github.com/bmad-code-org/BMAD-METHOD | MIT **+ Markenklausel** (BMad™ ist geschützt) | `dev-story/checklist.md` 4.389 B; `create-story/checklist.md` 14.349 B | PM, Dev, QA | Der einzige ernstgemeinte SDLC-Rollensatz — und **strukturell inkompatibel**: Story-Markdown als mutierende Monolithdatei mit „Change Log"-Sektion. Details unten. |
| rohitg00/awesome-claude-code-toolkit · ComposioHQ/awesome-claude-skills · kodustech/awesome-agent-skills · GetBindu | — | MIT (Aggregator) | Listen | — | **Rauschen.** Aggregatoren über die Repos oben; kein Eigentext. |
| tonynguyennvt/cursor-rules-awesome | https://github.com/tonynguyennvt/cursor-rules-awesome | MIT | „4.800+ Zeilen, 72 Themen" | alle | **Rauschen.** Wirbt mit „Perfect 10/10 rating" — selbstvergeben. Zeilenzahl als Qualitätsargument. |
| PatrickJS/awesome-cursorrules · sanjeed5/awesome-cursor-rules-mdc | https://github.com/PatrickJS/awesome-cursorrules | MIT | ~150 Dateien | — | **Rauschen für unsere vier Rollen.** Cursor-Rules sind durchweg *sprach-/framework*-orientiert („Next.js + Tailwind"), nicht rollenorientiert. Es gibt dort schlicht keinen Architekten und keinen PM. |
| agents.md (Agentic AI Foundation / LF) | https://agents.md/ | LF Projects, keine explizite Content-Lizenz | Spec-Seite | — | **Kein Rollentext, per Design.** „AGENTS.md is just standard Markdown. Use any headings you like." Regelt *wo*, nie *was*. Bucket erledigt. |
| GitLab Handbook | https://handbook.gitlab.com/ | **CC BY-SA 4.0** (im Seiten-HTML verifiziert) | Tausende Seiten | PM, alle | **Copyleft-Falle.** Textübernahme zwingt die abgeleitete Kit-Doku unter BY-SA. Nur referenzieren. |
| *Software Engineering at Google* (abseil) | https://abseil.io/resources/swe-book | **CC BY-NC-ND 4.0** | 602 S. | QA, Architekt | **Per Lizenz nicht adaptierbar** — NoDerivatives verbietet gekürzte/umformulierte Fassungen. Zitieren und verlinken, nichts weiter. |
| Google Testing Blog / Testing on the Toilet | https://testing.googleblog.com/ | kein offener Lizenzhinweis | Blog | QA | Kein Übernahmerecht. Nur Referenz. |
| OWASP ASVS 5.0 | https://github.com/OWASP/ASVS | **CC BY-SA 4.0**, offizielle CSV im Release | Architekt, Backend | Als **Daten** (SYNTHESE F3: ID-Auflösung gegen die CSV) einwandfrei. Als *Text* Copyleft. |
| GOV.UK Service Manual | https://www.gov.uk/service-manual | **OGL v3** (Bearbeitung erlaubt, nur Namensnennung) | Web | PM, Designer | Beste Lizenzlage im Feld; von SYNTHESE B4/B5 bereits angezapft. Für Architekt/Backend/QA unergiebig. |
| Kent Beck, *Test Desiderata* | https://testdesiderata.com/ | kein offener Lizenzhinweis (Substack/Medium) | 12 Eigenschaften | QA | **Vokabular**, nicht Text. Siehe §4. |

---

## 2. Die drei besten Funde

### Fund 1 — google/eng-practices, „What to Look for in a Code Review", Abschnitt *Tests* (CC BY 3.0)

Die Stelle, die überzeugt hat, wörtlich:

> „Make sure that the tests in the CL are correct, sensible, and useful. **Tests do not test themselves, and we rarely write tests for our tests—a human must ensure that tests are valid. Will the tests actually fail when the code is broken?** If the code changes beneath them, will they start producing false positives? Does each test make simple and useful assertions? … Remember that tests are also code that has to be maintained. Don't accept complexity in tests just because they aren't part of the main binary."

Warum das kein Listicle ist: der Satz benennt eine **Fehlbedingung** („will the tests actually fail when the code is broken") statt eine Tugend. Das ist genau die Frage, die SYNTHESE D2 (assertionsfreie Tests per `ast`-Walk) und D7 (Mutation Score) *mechanisieren* wollen — hier steht die Primärquelle dafür, aus einem Haus, das die Praxis nachweislich betreibt.

Zweite Stelle, aus „The Standard of Code Review":

> „Reviewers should favor approving a CL once it is in a state where it definitely improves the overall code health of the system being worked on, **even if the CL isn't perfect**. … There is no such thing as 'perfect' code—there is only better code. … If you want to improve some style point that isn't in the style guide, prefix your comment with **'Nit:'** … **Don't block CLs from being submitted based only on personal style preferences.**"

**Was wir genau übernehmen (3–4 Zeilen, in `quality-engineer/SKILL.md`, Schritt 1):** eine Verdikt-Kalibrierung, die es heute nicht gibt —

> Ein `fail` muss **das verletzte AC, INV oder die Guideline benennen**. Ein Befund, der keines davon verletzt, ist ein `Nit:` in `followups` und **niemals** ein `fail`. Es gibt keinen perfekten Code; du blockierst gegen einen benannten Vertrag, nicht gegen Geschmack.

Das ist der seltene Fall, in dem übernommener Text die Hausregeln nicht nur überlebt, sondern sie **gate-fähig macht**: „nennt der `fail` eine auflösbare AC-/INV-ID?" ist eine mechanische Prüfung im selben Stil wie SYNTHESE G1, und ihre Fehlschlagbedingung ist in einem Satz beschreibbar. Es adressiert außerdem eine reale Lücke: die QA-SKILL sagt heute achtmal „is a `fail`", aber nie, wann etwas **kein** `fail` ist — und §14a/G4 (STOP nach 3 QA-Zyklen) ist die teure Reparatur genau dieses Lochs.

**Nebenwirkung, die man mitkaufen muss:** Attributionspflicht (CC BY 3.0) und die Tatsache, dass die Quelle seit November 2025 archiviert ist — sie wird nie wieder aktualisiert. Für einen eingefrorenen Kalibrierungssatz ist das eher Vorteil als Risiko.

### Fund 2 — openai/codex `AGENTS.md` (Apache-2.0): die **Form**, nicht der Inhalt

Der Inhalt ist zu 95 % Rust-/Bazel-spezifisch und für uns wertlos. Was ihn zum zweitbesten Fund macht, ist, dass **fast jede Regel ihren Erzwinger mitliefert**:

> „You can run `just argument-comment-lint` to run the lint check locally. … Note CI checks all three platforms."
> „If you change `ConfigToml` or nested config types, run `just write-config-schema` to update `codex-rs/core/config.schema.json`."
> „If you change Rust dependencies … run `just bazel-lock-update` … **CI verifies lockfile drift.**"
> „Target Rust modules under 500 LoC, excluding tests. If a file exceeds roughly 800 LoC, add new functionality in a new module …"

Und, für unsere QA besonders relevant, drei Verbote gegen **Testtheater**:

> „Do not add tests for values that are statically defined. **Do not add negative tests for logic that was removed.** … Do not create small helper methods that are referenced only once."

**Was wir genau übernehmen:** keinen Satz Text — sondern eine **Formregel für die Phase-3-Kürzung**. Die Paritätsmatrix aus II.11/3 verlangt ohnehin je entfernter Regel einen Beleg. Codex' Datei zeigt die Umkehrung, die wir für die *bleibenden* Regeln brauchen:

> Jede Regel in einer SKILL steht in einer von zwei Formen: **(a) Regel + das Kommando/Gate, das sie prüft**, oder **(b) ausdrücklich als Urteilsheuristik markiert („nicht erzwungen")**. Eine Regel ohne beides wird gestrichen, nicht gekürzt.

Das ist die Hausregel des Harness (X1: „eine falsche Schutzbehauptung ist schlimmer als eine fehlende Prüfung") als *Schreibregel* formuliert, und wir haben jetzt einen publizierten Präzedenzfall aus einem Repo mit realem Durchsatz. Zusätzlich adoptierbar: die **Zwei-Schwellen-Form** („unter 500 → ok, über ~800 → neues Modul"), die für die `software-architect`-SKILL sauberer ist als jede Prozentzahl.

Kosten: null Zeilen. Es ist ein Kürzungskriterium, kein Zusatztext.

### Fund 3 — github/awesome-copilot `agents/qa-subagent.agent.md` (MIT), Abschnitte *Anti-Patterns* + Prinzip 2

Der einzige Rollentext im gesamten Feld, der eine Fehlerliste statt einer Fähigkeitsliste schreibt:

> „**Anti-Patterns (Never Do These)** — Write tests that pass regardless of the implementation (tautological tests). · Skip error-path testing because 'it probably works.' · **Mark flaky tests as skip/pending instead of fixing the root cause.** · Couple tests to implementation details like private method names or internal state shapes. · Report vague bugs like 'it doesn't work' without reproduction steps."

und

> „**Reproduce before you report. A bug without reproduction steps is just a rumor.** Pin down the exact inputs, state, and sequence that trigger the issue."

Warum das trägt: alle fünf Anti-Pattern sind **negativ und beobachtbar**, drei davon sind exakt SYNTHESE D2 (tautologisch), D3 (Skip statt Ursache) und D11 (Flake-Ursache). Der „rumor"-Satz ist die knappste je gelesene Begründung für das Pflichtfeld `BUG.repro` in II.2 — er verwandelt ein Schema-Feld in eine Regel, die eine Rolle sich merkt.

**Was wir genau übernehmen (≈6 Zeilen, `quality-engineer/SKILL.md`, als Ersatz für Prosa in Schritt 3):** die fünf Anti-Pattern als Ein-Zeilen-Liste plus den „rumor"-Satz in Schritt 6 (Bugfix-Verifikation). Wichtig: **als SKILL, nicht als GATE** — bis D2/D3 gebaut sind, ist es Urteil. Die Zeile muss das sagen, sonst produzieren wir selbst eine unbelegte Schutzbehauptung.

**Ausdrücklich NICHT übernehmen** aus derselben Datei: „Fast: Unit tests run in milliseconds", „One assertion per logical concept" (SYNTHESE §3 argumentiert gegen Verhältnis-/Quotenregeln), sowie den kompletten `Bug Report Format`-Block — der ist ein zweites Schema neben `BUG` aus II.2 und damit definitionsgemäß eine zweite Wahrheitsquelle.

---

## 3. Was an diesen Sammlungen systematisch falsch ist

Es ist ein wiederkehrendes Muster, nicht wechselnde Einzelschwächen. Sechs Schichten, von außen nach innen:

**(1) Fähigkeitsinventar statt Entscheidungsverfahren.** Der Prototyp ist VoltAgent `qa-expert.md`: sechs Kilobyte Nominalphrasen — „Test strategy: Requirements analysis · Risk assessment · Test approach · Resource planning · Tool selection". Das ist eine Taxonomie dessen, was Testen *heißt*, und enthält kein einziges „wenn X, dann ist das ein Fehler". wshobsons `backend-architect.md` treibt es auf 18 KB: „Service discovery: Consul, etcd, Eureka, Kubernetes". Solche Texte sind für ein Modell **informationsfrei** — sie nennen ausschließlich Begriffe, die es schon kennt, und verbrauchen dafür Kontext, den man für Projektwissen bräuchte. Sie lesen sich wie Kompetenz und wirken wie Rauschen.

**(2) Keine Fehlschlagbedingung ist formulierbar.** Kein einziger dieser Rollentexte — außer awesome-copilots `qa-subagent` — sagt, welcher Satz geschrieben wird, wenn die Rolle scheitert. Genau das ist die Hausregel des Harness („kein Gate, dessen Fehlschlag niemand beschreiben kann"), und sie fällt hier in **beide** Richtungen: die Texte sagen weder, wann etwas fehlschlägt, noch was ein Bestehen aussagt.

**(3) Zahlen ohne Herkunft, als Autorität getarnt.** VoltAgent: „Test coverage > 90% achieved · Automation > 70% implemented · Critical defects zero maintained". awesome-copilot SE-Architect: „<$100/month → Serverless/managed". Keine dieser Zahlen nennt eine Quelle. SYNTHESE §3 hat den 90-%-Fall bereits erledigt — 90 % ist bei Google „exemplary", nicht Norm, und der eigene Vorfall (`gate_test_coverage.py`: „shipped a frontend with 0 tests, hidden behind a high global backend coverage number") beweist, dass eine höhere Schwelle die reale Lücke nicht geschlossen hätte. Wer diese Zahl übernimmt, importiert exakt den Defekt, den das Repo schon dokumentiert hat.

**(4) Selbstattestierte Checkbox als Qualitätsgate.** BMADs `dev-story/checklist.md` ist der reinste Fall: 25 Häkchen, davon „**Story Context Completeness:** Dev Notes contains ALL necessary technical requirements", „**No Ambiguous Implementation**", „**Quality Gates Passed**", abgeschlossen mit „Definition of Done: {{PASS/FAIL}}" und „Completion Score: {{completed}}/{{total}}". Der Prüfer ist dieselbe Instanz, die die Arbeit gemacht hat, das Kriterium ist unentscheidbar („ambiguous", „sufficient"), und das Ergebnis ist eine Zahl. SYNTHESE §3 hat das vorweggenommen — „Ein Modell füllt zehn Zeilen mühelos. Ein Gate, dessen *Bestehen* nichts aussagt, verletzt die Hausregel in der zweiten Richtung" — und führt „Definition of Ready als Checkliste" bereits als Anti-Pattern. Ich empfehle es folglich nicht; ich melde, dass der beste verfügbare Fremd-PM/Dev-Prozess genau darauf hinausläuft.

**(5) Zeilenzahl als Qualitätssignal.** „4,800+ lines covering 72 topics … **Perfect 10/10 rating**" (cursor-rules-awesome, Selbstbewertung). awesome-copilots `instructions/`-Verzeichnis mit 15–64-KB-Dateien. Die Ökonomie dieser Repos ist Sterne-Sammeln, und Umfang ist die sichtbarste Metrik. Das ist der direkte Gegensatz zu II.5. Die Kopfregel unserer eigenen Kits — „bloated rule files get ignored" — ist im Ökosystem eine **Minderheitsposition**.

**(6) Sie setzen eine andere Welt voraus.** Fast durchgängig: einen Ticket-Tracker mit Stories und Sprints (BMAD), eine mutierende Monolithdatei als Wahrheitsquelle mit eingebettetem Change Log (BMAD — kollidiert frontal mit II.2 „Historie liegt in Git, nicht als Changelog in aktiven Dateien" und mit Datei-pro-Item), mehrere parallele Reviewer, die konsolidiert werden müssen (wshobson `multi-reviewer-patterns`), eine CI, die es hier nicht gibt, und ein Team von Menschen. Der V2-Zustandsmodell-Test bestehen **keine** dieser Sammlungen als Ganzes; einzelne Absätze überleben, Dateien nie.

**Und die Lizenz-Schicht, die fast alle vergessen.** Die Aggregatoren tragen MIT — aber MIT auf einem Aggregator wäscht die Herkunft des Inhalts nicht. wshobsons `api-design-principles` ist erkennbar Lehrbuchmaterial; VoltAgents gleichförmige 6,7-KB-Dateien sind erkennbar generiert. Umgekehrt haben die *fachlich* besten Quellen die restriktivsten Lizenzen: *Software Engineering at Google* ist **CC BY-NC-ND** — NoDerivatives verbietet die gekürzte Fassung, die wir bräuchten, ausdrücklich; GitLab-Handbook und OWASP ASVS sind **BY-SA** und würden abgeleitete Kit-Doku unter Copyleft ziehen. Der einzige fachlich starke Text mit permissiver Lizenz im ganzen Feld ist **google/eng-practices (CC BY 3.0)**. Das ist kein Zufall, sondern die Antwort auf die Frage.

---

## 4. Was besser Referenz ist als kopierter Text

Kurz: alles, was **entweder** ein gepflegter Datensatz **oder** ein benanntes Vokabular ist. Eine SKILL, die auf einen Namen zeigt, altert nicht; eine SKILL, die den Inhalt nacherzählt, hat eine zweite Fassung erzeugt — genau die Falle aus SYNTHESE §3.

- **OWASP ASVS 5.0 — als CSV, nicht als Prosa.** SYNTHESE F3 sieht das schon richtig vor: Mitigation-IDs müssen gegen die mitgelieferte CSV auflösen. Der Text der Requirements gehört nie in eine SKILL; die Datei ist Daten, die Prüfung ist ein Gate, und die BY-SA-Lizenz betrifft die *Datei*, nicht unsere Regel. **Das ist die Blaupause für den ganzen Abschnitt hier.**
- **google/eng-practices, alles außer den 8 übernommenen Zeilen.** „Speed of Code Reviews", „Handling Pushback", „Small CLs" sind gut und für uns unpassend: sie regeln Mensch-zu-Mensch-Latenz und Verhandlungsdynamik. Verlinken aus dem `project-auditor`, nicht einbauen.
- ***Software Engineering at Google*** **— per Lizenz zwingend Referenz.** CC BY-NC-ND schließt eine Bearbeitung aus. Die für uns einschlägigen Kapitel (Test Sizes small/medium/large; „Change-Detector Tests Considered Harmful") als benannte Verweise führen, wenn D2/D5 gebaut werden.
- **Kent Beck,** *Test Desiderata* **— Vokabular, nicht Text.** Die zwölf Eigenschaften (isolated, composable, deterministic, fast, writable, readable …) sind wertvoll, weil sie SYNTHESE D6 (Reihenfolge-Randomisierung → *isolated*) und D11 (Flake-Taxonomie → *deterministic*) **benennbar** machen. Ein Flake-Befund, der „verletzt *deterministic*" schreibt, ist prüfbarer als drei Sätze Prosa. Keine offene Lizenz, also: den Begriff verwenden, den Text nie.
- **RFC 9457 / RFC 9110 §13 / OAS 3.1.** SYNTHESE A1/A2 und der Ausschluss des Idempotency-Key-Drafts sind bereits korrekt entschieden. Für die `backend-developer`-SKILL gilt strikt: die RFC-Nummer nennen, das Schema **nie** in die SKILL kopieren — sonst existiert das Fehlerformat zweimal, in `api/openapi.yaml` und im Rollentext, und driftet.
- **GOV.UK Service Manual (OGL v3)** und **GitLab Handbook (BY-SA)** für PM-Fragen. Ersteres lizenziell offen, aber inhaltlich auf Bürgerdienste zugeschnitten; letzteres inhaltlich reich, aber Copyleft. Beide als Nachschlagewerk verlinken, keine Zeile übernehmen.
- **awesome-copilots Skill-Quality-Gates** (`eng/external-plugin-quality-gates.mjs`, 23 KB, MIT) — geprüft und **verworfen** als Vorbild: das ist eine Ingest-Pipeline (klonen, linten, Smoke-Test), kein Inhaltsstandard. Interessant nur als Beleg, dass selbst die größte kuratierte Sammlung ihre Instruktionstexte **maschinell nur auf Wohlgeformtheit** prüft, nie auf Gehalt. Der Harness prüft mit `kit_checks` bereits mehr.

---

## Fazit in einem Satz

Aus vier Ökosystem-Familien mit zusammen etwa 3.500 publizierten Dateien überleben die fünf Kriterien: **ein Fund mit übernehmbarem Text** (google/eng-practices, CC BY 3.0, ~8 Zeilen QA-Verdikt-Kalibrierung), **ein Fund mit übernehmbarer Form** (openai/codex `AGENTS.md`, Apache-2.0, null Zeilen — ein Kürzungskriterium für Phase 3) und **ein Fund mit übernehmbarer Fehlerliste** (awesome-copilot `qa-subagent`, MIT, ~6 Zeilen). Alles Übrige ist entweder Fähigkeitsinventar, selbstattestierte Checkliste, oder lizenziell gesperrt — und da der Zeilenhaushalt bei QA (146/150) und PM (220/150) ohnehin bei null bis negativ steht, ist „nichts Weiteres übernehmen" hier das teurere, nicht das billigere Ergebnis gewesen.

**Quellen:** [google/eng-practices](https://google.github.io/eng-practices/) · [openai/codex AGENTS.md](https://github.com/openai/codex/blob/main/AGENTS.md) · [github/awesome-copilot](https://github.com/github/awesome-copilot) · [wshobson/agents](https://github.com/wshobson/agents) · [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) · [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) · [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) · [tonynguyennvt/cursor-rules-awesome](https://github.com/tonynguyennvt/cursor-rules-awesome) · [agents.md](https://agents.md/) · [GitLab Handbook](https://handbook.gitlab.com/) · [Software Engineering at Google (abseil)](https://abseil.io/resources/swe-book) · [OWASP ASVS](https://github.com/OWASP/ASVS) · [GOV.UK Service Manual](https://www.gov.uk/service-manual) · [Test Desiderata](https://testdesiderata.com/)