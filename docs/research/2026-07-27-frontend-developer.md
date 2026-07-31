## 1. Was die `software-architect`-SKILL heute gut macht

Datei: `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\software-architect\SKILL.md` (99 Zeilen)

**(a) Sie kennt die GATE/SKILL-Linie bereits und wendet sie an.** Schritt 6: *"hard, project-wide rules become `INV` items with a `check` reference (`{kind: test|script, ref: …}`), so a rule that nothing can verify is visible as unverified instead of living as prose."* Das ist exakt die Regel, um die es hier geht — und sie ist im Kernel gedeckt (`REQUIRED_FIELDS["INV"] = ("scope","source","check")`, Spec II.2: der Validator prüft EXISTENZ und Sammelbarkeit des Tests, sonst `unverified` → Merge-Block).

**(b) `packaging.method` ist ein echtes, sauber gebautes Gate.** `gate_packaging_decision.py` liest `packaging.method` aus dem ARC-Companion über `ProjectState.active_dir("ARC")` und behandelt *"kein Architektur-Item vorhanden"* als **unresolved**, nicht als Ausnahme. Das ist die seltene Sorte Gate, die nicht false-open geht. Der Skill-Text dazu ist ehrlich: *"Even 'none / library only' is valid — but it MUST be stated."*

**(c) `premise_invalidation_triggers` / `premise_rechecks` sind besser als der publizierte Stand.** MADR 4.0 kennt "Confirmation" und den Status `superseded`, aber **keine messbaren Verfallsbedingungen einer Entscheidung**. Der Skill fordert sie (*"MEASURABLE tipping points (e.g. 'index.html grows beyond 500 lines')"*) und verbietet explizit das Killerargument (*"'That decision is not up for renegotiation' is a FORBIDDEN argument"*), mit Vorfallbeleg (9× über dem eigenen Kipppunkt). Das gehört zum Besten in der Datei und hat keine Entsprechung in adr.github.io/madr.

**(d) Der Anti-Gedächtnis-Reflex bei der Toolchain.** Schritt 3: *"If you are NOT certain what the standard/best-practice toolchain for this domain is, task the `research-engineer` (via the PM) to find it WITH SOURCES before you decide — relying on memory is exactly how a critical tool/test gets missed."* Gekoppelt an ein Gate: `project_config.yaml` `stacks:` + `quality.py` (ein deklarierter Stack ohne Checks = FAIL, `[TODO]` bei vorhandenem Code = FAIL).

**(e) Saubere Zuständigkeitsteilung Strategie/Vollständigkeit.** *"For every component state `criticality` (low|med|high) and a `test_strategy` … This is the **input** QA uses to prove coverage; you do NOT write the QA test files."*

**(f) Ehrlichkeit über die eigene Ohnmacht.** Zu `coding_guidelines.yaml`: *"that guard is currently unreachable — report it rather than inventing a file elsewhere."* Genau die Haltung, die verhindert, dass Instruktionstext vortäuscht, erzwungen zu sein.

---

## 2. Lücken gegen publizierten Stand — mit Quelle

| # | Lücke | Publizierter Standard | Heute in der SKILL |
|---|---|---|---|
| A | Schnittstellenvertrag ist Freitext | OpenAPI 3.2.0, 19.09.2025 — https://spec.openapis.org/oas/latest.html · Spectral-Linting · Schemathesis/Dredd für Drift | `SR.contract` = freier String; Wort "OpenAPI" kommt im ganzen Repo **nicht** vor |
| B | Keine SLIs/SLOs zur Entwurfszeit | Google SRE Workbook, *Implementing SLOs* — https://sre.google/workbook/implementing-slos/ · OpenSLO v1 — https://openslo.com/ · ISO/IEC 25010:2023 (9 Qualitätsmerkmale) — https://www.iso.org/standard/78176.html | nichts. `criticality: high` zieht **keine** Zahl nach sich |
| C | Threat Model ist der schwächste Schritt | OWASP Threat Modeling Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html · NIST SP 800-218 SSDF **PW.1.1** — https://csrc.nist.gov/projects/ssdf · OWASP ASVS 5.0 (Mai 2025) — https://owasp.org/www-project-application-security-verification-standard/ | Schritt 7, ein Satz, Trigger = *"for security-relevant SRs"* (Selbsteinschätzung → kann still nie feuern); keine 4. Manifest-Frage *"Did we do a good enough job?"*; keine Wiederholungspflicht, obwohl der Skill für Decisions genau diesen Mechanismus erfunden hat |
| D | Kein Abstraktionsniveau für die `.drawio.svg` | C4-Modell — https://c4model.com/ · Review-Checkliste — https://c4model.com/diagrams/checklist | nur *"Keep diagrams SMALL — one concern per file"*. `arc_companion.yaml` `scope:` = `type: str`, **offene** Zeichenkette |
| E | Fitness Functions nur als Token-Grep | ArchUnit / dependency-cruiser / import-linter; Ford/Parsons/Kua, *Building Evolutionary Architectures* | `kit_checks.check_module_invariants` = Liste verbotener Tokens pro Datei. Kann **keine Richtung** ("`domain/` darf `infrastructure/` nicht importieren") und **keine Zyklen** ausdrücken; scheitert an jeder Import-Schreibweise, die die Tokenliste nicht vorhergesehen hat |
| F | Qualitätsszenarien fehlen | arc42 §10 + ATAM-Utility-Tree — https://quality.arc42.org/standards/iso-42010 · ISO/IEC/IEEE 42010 | PR hat `acceptance_criteria`, SR hat `contract` — nirgends *"bei 100k Katalogeinträgen p95 < 300 ms"* |
| G | Lieferkette ist kein Architekturentscheid | SLSA v1.0 Build-Level — https://slsa.dev/spec/v1.0/levels · CycloneDX/SPDX · EU CRA (Meldepflichten ab 11.09.2026) — https://openssf.org/blog/2025/10/22/sboms-in-the-era-of-the-cra-toward-a-unified-and-actionable-framework/ | `quality.py::sbom()` erzeugt CycloneDX — aber nur als `warn`, wenn `cyclonedx-py` fehlt, und die Architekten-SKILL erwähnt SBOM **nie**. `packaging.method` sagt WIE geliefert wird, nichts über Provenienz |
| H | Decision-Items ohne Alternativen | MADR 4.0.0, 17.09.2024 — https://adr.github.io/madr/ (Felder *Considered Options*, *Decision Drivers*, *Confirmation*) | `REQUIRED_FIELDS["DEC"] = ("title","context","decision","consequences","source")` — das ist Nygard 2011. **Kein `options_considered`.** |
| I | ARC-Drift nach dem Einfrieren | C4/arc42: Diagramme veralten binnen Wochen | Spec II.12 hat nur *"ARC ohne derives_from → Validator-Flag"*; kein Check, ob die referenzierten SRs noch leben |

**Interne Inkonsistenz, die auffällt:** Schritt 3 warnt *"relying on memory is exactly how a critical tool/test gets missed"* — und liefert dann selbst eine **Gedächtnisliste** von sechs Domänen. In dieser Liste steht für `web/services` nur *"e2e (Playwright) + a real container build + health smoke"*. **Contract-Testing gegen eine Schnittstellenbeschreibung fehlt** — also genau der Prüftyp, der bei einem Backend, das der User nicht beurteilen kann, den Unterschied macht.

---

## 3. Pro Lücke: GATE oder SKILL

### A — OpenAPI-first → **beides, klar getrennt**
- **SKILL:** *ob* design-first gearbeitet wird. Das ist **umstritten**: FastAPI/NestJS-Teams generieren die Spec aus dem Code und fahren gut damit. Kein Gate kann die *Reihenfolge* prüfen — es kann nur das *Artefakt* prüfen. Genau so muss der Text es sagen.
- **GATE (eng, machbar):** `SR.contract` wird strukturiert: `contract: {kind: http-api|cli|library|event|internal, spec_ref: <pfad>}`. `kind` als **geschlossenes Vokabular** — der Kernel argumentiert diesen Trick bereits selbst bei `TASK_TYPES` (*"Left free-form it is unusable as a GATE input … fails OPEN on every synonym the orchestrator invents"*).
- **Fehlermeldung 1:** „SR-0007 deklariert `contract.kind: http-api`, nennt aber keinen `spec_ref` — ein Netzvertrag ohne maschinenlesbare Beschreibung ist eine Absichtserklärung."
- **Fehlermeldung 2:** „`api/openapi.yaml` ist unter `spectral lint` mit 6 Fehlern durchgefallen (u. a. `operation-operationId` fehlt an 3 Pfaden)."
- **Fehlermeldung 3 (teurer, Stack-Runner in `quality.py`):** „Schemathesis: `POST /orders` antwortet mit 500 auf ein schema-valides Beispiel; `GET /orders/{id}` existiert im Code, nicht in der Spec." — Das ist der Drift-Nachweis und der eigentliche Wert.
- Hinweis: `SR.contract` steht in `HASHED_FIELDS` — eine Strukturierung ist freigaberelevant und damit konsistent mit der Harness-Logik.

### B — SLIs/SLOs → **GATE, und zwar fast gratis**
Der Mechanismus existiert schon: **INV mit `check`-Referenz**. Ein SLO ist nichts anderes als eine Invariante mit einer Zahl und einem messenden Test.
- **GATE:** Eine Komponente mit `criticality: high` in ihrer SR muss mindestens ein INV-Item der Form `{metric, target, window, check: {kind: test, ref: …}}` unter sich haben.
- **Fehlermeldung:** „SR-0012 führt Komponente `pricing-api` mit `criticality: high`, aber kein INV nennt ein Latenz-/Fehler-/Frische-Ziel dafür. Ein Zielwert, der nach dem ersten Vorfall entsteht, ist ein Postmortem, kein Requirement."
- **Zweite Fehlermeldung, umsonst mitgeliefert:** der bestehende Validator prüft die Existenz des `check`-Tests → „INV-0004 (`p95 < 300ms`) referenziert `tests/perf/test_pricing.py::test_p95`, der nicht existiert → `unverified` → Merge blockiert."
- **Ehrlichkeitsgrenze, die im Text stehen muss:** Die Harness kann nicht prüfen, ob der SLO *gut gewählt* ist, und hat keine Produktionstelemetrie. Sie prüft, dass eine **Zahl mit Messvorschrift existiert**. Mehr nicht — und das muss so dastehen, sonst ist es ein Gate, das etwas behauptet.

### C — Threat Modelling → **GATE, als Klon des Packaging-Gates**
Das ist die stärkste Analogie im ganzen Befund. `gate_packaging_decision` feuert bei **jedem** Projekt und akzeptiert *"none / library"* als Antwort — aber nur als **ausgesprochene**. Genau das braucht das Threat Model, weil "security-relevant" heute die Selbsteinschätzung dessen ist, der die Arbeit spart.
- **GATE `gate_threat_model`:** Sobald ein Root-Item existiert, muss ein aktives Decision-Item ein Feld `threat_model:` tragen, mit je Eintrag `{stride, asset, mitigation, check}`. Kein Threat-Model-Item = **unresolved**, nicht Ausnahme.
- **Fehlermeldung 1:** „Kein aktives Decision-Item nennt ein Threat Model. NIST SSDF PW.1.1 macht Risiko-/Threat-Modelling zur benannten Entwurfspraxis; auch die Antwort ‚keine Authentifizierung, keine Fremd-Eingabe, keine externe Integration — keine Bedrohungen im Scope' ist gültig, aber sie muss dastehen."
- **Fehlermeldung 2:** „TM-3 (Tampering auf dem Upload-Pfad) nennt eine Mitigation ohne `check` → `unverified` → Merge blockiert." — dieselbe Mechanik wie INV, also kein neuer Code.
- **SKILL-Anteil (nicht gate-bar):** die 4. Frage des Threat Modeling Manifesto — *"Did we do a good enough job?"* — sowie die Zuordnung jeder Mitigation zu einer ASVS-5.0-Anforderung, damit QA eine testbare Formulierung bekommt statt Prosa. Und: das Cheat Sheet sagt ausdrücklich *"it is not something that is performed once and never again"* → die **Wiederholungspflicht** gehört an dieselbe Stelle wie `premise_rechecks`, also in die PR/CR.

### D — C4 + Diagramm-Checkliste → **GATE, weil der Parser schon läuft**
Der Kernel prüft bei der ARC-Promotion bereits die eingebettete mxGraph-XML auf Wohlgeformtheit (Spec II.6a, fail-closed). Drei zusätzliche Assertions auf demselben Parse-Baum:
1. `arc_companion.scope` wird **geschlossenes Vokabular**: `{context, container, component, code, deployment}` (C4-Level).
2. Jede Kante (`mxCell` mit `edge="1"`) trägt ein nicht-leeres Label.
3. Jeder Knoten (`vertex="1"`) trägt einen nicht-leeren `value`.
- **Fehlermeldung:** „ARC-0003 Promotion verweigert: 4 von 11 Kanten ohne Beschriftung. C4-Review-Checkliste: *‚Does every arrow have a label describing the intent of that relationship?'* — eine unbeschriftete Kante sagt, dass zwei Dinge verbunden sind, und sonst nichts."
- **Fehlermeldung:** „`scope: 'system overview'` ist kein C4-Level. Erlaubt: context | container | component | code | deployment."
- **Bewusst NICHT Gate:** die Legende (*"Does the diagram have a key/legend?"*). Ein Textknoten mit "Legende" ist zu leicht zu erschleichen und produziert Fehlalarme — das bleibt SKILL.
- Das ist die Prüfung, die dem Symptom des Users am direktesten entspricht: das Kastenschema, das nach Architektur aussieht und keine Aussage trifft.

### E — Fitness Functions mit Richtung → **GATE, aber teurer**
Abhängigkeitsrichtung ist eine reine Grapheigenschaft, also mechanisch prüfbar. Der bestehende `module_invariants`-Knopf ist die schwächstmögliche Form davon.
- **GATE:** neuer Knopf `layers:` in derselben Guidelines-Datei, `layers: [domain, application, infrastructure]` + `forbidden: [{from: domain, to: infrastructure}]`, ausgewertet über `import-linter` (Python) bzw. `dependency-cruiser` (TS/JS) als Stack-Runner in `quality.py`; zusätzlich ein Zykluscheck.
- **Fehlermeldung:** „`domain/pricing.py` → `infrastructure.db` (Kette: domain.pricing → infrastructure.db). Layer-Regel ‚domain darf nicht von infrastructure abhängen' (DEC-0007)." Plus: „Importzyklus: `orders → billing → orders`."
- **Warnung, die die Harness selbst schon gelernt hat:** ohne deklarierte Layer scannt das Gate nichts und meldet grün — dasselbe Muster wie `kit_checks.py:75` (*"kept its whole codebase under compounder/ and 'PASS file budget' was false-green for weeks"*). Also: **undeklarierte Layer bei vorhandenem Code = FAIL**, exakt analog zu `stacks: [TODO]`.
- **SKILL-Anteil:** *welche* Layer es gibt, ist Urteil. Die Richtung ist Gate.

### F — Qualitätsszenarien → **SKILL** (mit einer gate-baren Ecke)
Welche der neun ISO-25010-Merkmale zählen, ist Urteilssache und projektspezifisch — nicht gate-bar. Die SKILL sollte die ATAM-Szenarioform vorgeben (*Stimulus / Umgebung / Antwort / Antwortmaß*), weil das die Form ist, die sich in einen Test übersetzt. Die einzige gate-bare Ecke ist Lücke B.

### G — Lieferkette → **überwiegend SKILL, ein schmales Gate**
- **GATE:** wenn `packaging.method` ein verteiltes Artefakt ist (`container | installer | wheel | npm | service-image`), muss die Release-Evidence eine SBOM referenzieren. Der ARC-Companion hat die Hash-Maschinerie (`assets: {mode: manifest, files: {pfad: sha256}}`) bereits. **Fehlermeldung:** „`packaging.method: container`, aber die Acceptance-Evidence nennt keine SBOM — CycloneDX/SPDX ist die de-facto Anforderung für alles, was das eigene Gerät verlässt."
- **SKILL, nicht Gate:** SLSA-Build-Level. Die Harness kann eine gehostete, isolierte Buildplattform nicht verifizieren — ein SLSA-L2/L3-Gate wäre Theater (siehe §5).

### H — MADR `options_considered` → **GATE, einzeilig**
- **GATE:** ein Decision-Item, das `premise_invalidation_triggers` trägt (= richtungsgebend, so definiert die SKILL es selbst), braucht `options_considered` mit ≥ 2 Einträgen, jeder mit einem Ein-Zeilen-Ablehnungsgrund.
- **Fehlermeldung:** „DEC-0004 trägt `premise_invalidation_triggers` (richtungsgebend), nennt aber nur eine erwogene Option. Eine Entscheidung ohne Alternative ist ein Bericht (MADR 4.0: *Considered Options*)."
- **Ehrlichkeitsgrenze:** Das Gate kann Optionen **zählen**, nicht beurteilen, ob die Alternative ein Strohmann ist. Es lohnt trotzdem: eine benannte Alternative ist für den `project-auditor` sichtbar, eine ungenannte nicht.
- Nebenbei bestätigt MADR 4.0 den Harness-Instinkt: das Feld heißt dort seit 4.0 **"Confirmation"** — die Harness nennt dasselbe `check`.

### I — ARC-Drift → **GATE, Validator-Regel**
`ARC.derives_from` muss auf existierende, nicht-`SUPERSEDED` SR/PR zeigen. **Fehlermeldung:** „ARC-0002 `derives_from: [SR-0009]`, SR-0009 ist SUPERSEDED — das eingefrorene Diagramm beschreibt einen Vertrag, den das Projekt ersetzt hat." Billig, halb vorhanden (II.12 flaggt nur fehlendes `derives_from`).

---

## 4. Die drei wirksamsten Ergänzungen, in Reihenfolge

**1. `options_considered` ≥ 2 an richtungsgebenden Decision-Items (MADR 4.0).**
*Kosten:* am geringsten von allen — ein Eintrag in `REQUIRED_FIELDS["DEC"]` bzw. eine bedingte Validatorregel (nur wenn `premise_invalidation_triggers` gesetzt), plus drei Zeilen SKILL-Text. Keine neue Abhängigkeit, kein neuer Hook.
*Warum zuerst:* Genau das ist das Rückgrat des Symptoms, das der User im Frontend sieht und im Backend vermutet. „Eine Option, als Schlussfolgerung präsentiert" ist die Signatur maschinell erzeugter Architektur. Der Zwang, die verworfene Alternative zu **nennen**, ist der billigste bekannte Hebel dagegen — und er macht die Entscheidung für den Auditor lesbar.

**2. ARC-Promotion prüft C4-Level + Kantenbeschriftung + Knotennamen.**
*Kosten:* niedrig. Der mxGraph-Parse existiert bereits im Kernel-Promotionspfad; es kommen drei Assertions und ein `enum:` im `arc_companion.yaml` dazu (`scope` von `type: str` auf geschlossenes Vokabular). Risiko: bestehende Diagramme in Pilotrepos müssen einmalig nachbeschriftet werden — der Gate ist fail-closed, das ist gewollt.
*Warum zweitens:* Es ist das einzige Artefakt der Rolle, das der User **selbst beurteilen kann**. Ein Diagramm mit benannten Kanten zwingt den Architekten zu einer Aussage über Protokoll und Richtung; unbeschriftete Kästen sind das visuelle Äquivalent zu lebloser Prosa.

**3. `gate_threat_model` als Klon von `gate_packaging_decision` + Mitigation-`check`.**
*Kosten:* mittel — ein neuer Hook nach exakt vorhandenem Muster (~140 Zeilen, davon der Großteil kopierbar), ein Feld im DEC-Schema, ein Eintrag in `settings.json`, plus die Testfälle (kein TM → Block; TM mit „nichts im Scope" + Begründung → pass; Mitigation ohne `check` → Block). Keine neue externe Abhängigkeit.
*Warum drittens:* Es schließt die Lücke, die der User **prinzipiell nicht sehen kann**, und es hat mit NIST SSDF PW.1.1 eine normative Grundlage statt einer Geschmacksfrage. Der heutige Trigger („security-relevant SRs") ist eine Selbsteinschätzung und damit kein Trigger.

**Knapp dahinter (Platz 4), bewusst nicht in den Top 3:** die Layer-/Zyklus-Fitness-Function (Lücke E). Größte Zähne für das unsichtbare Backend, aber echte Kosten: eine neue Werkzeugabhängigkeit **pro Stack** (`import-linter`, `dependency-cruiser`), ein neuer Guidelines-Knopf, und die reale Gefahr des False-Green bei undeklarierten Layern. Erst sinnvoll, wenn ein Pilotprojekt mehr als eine Handvoll Module hat.

---

## 5. Was gegen populäre Empfehlungen für diese Rolle spricht

**DORA-Vier-Schlüssel als Dashboard: nicht einbauen.** Der DORA-Report 2025 hat die Elite/High/Medium/Low-Cluster **aufgegeben** und die Metriken in drei Durchsatz- (Deployment-Frequenz, Lead Time, Rework Rate) und zwei Instabilitätsmetriken (Change Failure Rate, Failed Deployment Recovery Time) reorganisiert; die klassischen vier erscheinen 2025 nur noch in einer Fußnote als *eine* Messweise unter vielen. Zusätzlich ist es ein **Umfrageinstrument über Organisationen hinweg**, nicht ein Repo-Zähler — für ein Ein-Personen-Projekt mit LLM-Team ohne statistische Basis. Der einzige DORA-2025-Befund, der hier zählt, ist ein Argument *für* die schon vorhandene QA-Evidence-Schranke, nicht für neue Kennzahlen: KI-Einsatz steigert den Durchsatz und **verschlechtert messbar die Stabilität** (mehr Change Failures, mehr Rework, längere Erholungszeiten).

**SLSA L2/L3 als Gate: nein.** Die Harness kann eine gehostete, isolierte, signierende Buildplattform nicht verifizieren — ein Level-Gate wäre eine Behauptung ohne Prüfung, also genau das, was die Harness verbietet. SBOM-Erzeugung bei verteilten Artefakten ist prüfbar, das Build-Level nicht.

**Clean Architecture / SOLID vollständig: überlebt den Kontakt mit einem Kleinteam nicht.** Bemerkenswert ist schon, dass **keine Normungsorganisation** Clean Architecture publiziert — die Quellenlage sind Praktiker-Blogs, und die sind sich uneins: Three Dots Labs verteidigt sie, James Hickey und Ardalis (selbst Autor einer Clean-Architecture-Vorlage!) listen die Nachteile. Der Konsens der Kritik: Über-Engineering, wenn die Domäne trivial ist; Reibung gegen meinungsstarke Frameworks (Rails, Django, Spring Boot, Laravel); und der Nutzen hängt daran, dass mehrere Senior-Entwickler das Muster schon produktiv gefahren haben. **Was überlebt, ist genau ein Satz: die Abhängigkeitsrichtung** — und der ist eine Grapheigenschaft, also gate-bar (Lücke E). **Was nicht überlebt:** ein Interactor pro Use Case, ein Repository-Interface mit genau einer Implementierung, DTO-Mapping über drei Schichten. Praktischer Vorschlag für die SKILL statt eines Gates: *„Ein Interface mit genau einer Implementierung und ohne Test-Double ist ein Löschkandidat — nenne den Grund, warum es bleibt."* Bewusst SKILL, nicht Gate: „genau eine Implementierung" ist zählbar, aber die Schlussfolgerung „also weg" ist es nicht (ein legitimer Plugin-Punkt hat heute auch nur eine).

**OpenTelemetry-Semconv als Gate: heute zu früh.** Die HTTP-Semantic-Conventions sind als *Mixed* geführt, nicht durchgehend stabil, und die Migration läuft über ein Opt-in (`OTEL_SEMCONV_STABILITY_OPT_IN`). Ein Gate darauf würde gegen ein bewegliches Ziel prüfen. Als SKILL-Empfehlung („benutze die Semconv-Namen, erfinde keine eigenen") sinnvoll, als Schranke nicht.

**ATAM als Methode: nein — die Szenarioform: ja.** ATAM setzt eine Stakeholder-Gruppe und einen Bewertungsworkshop voraus, die es hier nicht gibt. Was übrig bleibt und trägt, ist ausschließlich das **Qualitätsszenario als Satzform** (Stimulus/Umgebung/Antwort/Antwortmaß), weil es „fühlt sich träge an" in eine Zahl mit Test übersetzt.

**„ADR für alles": bereits richtig begrenzt.** Die SKILL sagt *"record each significant decision"* und reserviert `premise_invalidation_triggers` für richtungsgebende Entscheidungen. Diese Zweiteilung sollte beim Einbau von Punkt 1 aus §4 **erhalten** bleiben — der `options_considered`-Zwang gehört nur an die richtungsgebende Klasse, sonst erzeugt er Formularausfüllen an fünfzig Trivialentscheidungen und entwertet sich selbst.

**Design-first vs. Code-first ist echt umstritten.** Deshalb darf die SKILL OpenAPI-first nicht als Norm behaupten. Prüfbar ist die **Existenz und Konsistenz** der Spezifikation, nie die Reihenfolge ihrer Entstehung.

---

**Relevante Dateien:**
- `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\software-architect\SKILL.md`
- `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\hooks\gate_packaging_decision.py` (Vorlage für Punkt 3)
- `c:\Offline Repos\AgentAndSkills\team-kits\kernel\backlog_types.py` (`REQUIRED_FIELDS`, `HASHED_FIELDS`, `TASK_TYPES` als Vorbild für geschlossene Vokabulare, `ACTIVE_DIRS`)
- `c:\Offline Repos\AgentAndSkills\team-kits\kernel\schemas\arc_companion.yaml` (`scope` ist heute offener String; `packaging` optional mit Pflicht-`method`)
- `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\kit_checks.py` (`check_module_invariants` — heutige Fitness-Function-Vorstufe; `_knob_hint`-Muster für neue Guidelines-Knöpfe)
- `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\quality.py` (`declared_stacks`, `STACKS`, `sbom`)
- `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\project_memory\project_config.yaml`

Sources:
- [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/latest.html)
- [Leveraging the OpenAPI Specification for API Governance (Bump.sh)](https://bump.sh/blog/leveraging-openapi-specification-api-governance/)
- [Schemathesis / OpenAPI contract testing](https://qaskills.sh/blog/api-contract-testing-schemathesis-guide)
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [OpenSLO](https://openslo.com/) · [OpenSLO on GitHub](https://github.com/OpenSLO/OpenSLO)
- [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html)
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- [NIST SSDF (SP 800-218)](https://csrc.nist.gov/projects/ssdf) · [CISA-Eintrag](https://www.cisa.gov/resources-tools/resources/nist-sp-800-218-secure-software-development-framework-v11-recommendations-mitigating-risk-software)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) · [ASVS 5.0 GitHub](https://github.com/OWASP/ASVS)
- [C4 model](https://c4model.com/) · [C4 diagram review checklist](https://c4model.com/diagrams/checklist)
- [MADR](https://adr.github.io/madr/) · [MADR releases](https://github.com/adr/madr/releases)
- [arc42 Quality Model — ISO/IEC/IEEE 42010](https://quality.arc42.org/standards/iso-42010) · [arc42 template overview](https://arc42.org/overview)
- [SLSA v1.0 security levels](https://slsa.dev/spec/v1.0/levels) · [SLSA provenance](https://slsa.dev/spec/v1.0/provenance)
- [OpenSSF: SBOMs in the era of the CRA](https://openssf.org/blog/2025/10/22/sboms-in-the-era-of-the-cra-toward-a-unified-and-actionable-framework/)
- [OpenTelemetry HTTP semantic conventions](https://opentelemetry.io/docs/specs/semconv/http/) · [semconv index](https://opentelemetry.io/docs/specs/semconv/)
- [DORA 2025 — RedMonk analysis](https://redmonk.com/rstephens/2025/12/18/dora2025/) · [The Register on DORA 2025](https://www.theregister.com/2025/09/24/googlesponsored_dora_report_reframes_ai/)
- [Is Clean Architecture Overengineering? (Three Dots Labs)](https://threedots.tech/episode/is-clean-architecture-overengineering/) · [Clean Architecture Disadvantages (James Hickey)](https://www.jamesmichaelhickey.com/clean-architecture/) · [Clean Architecture Sucks (Ardalis)](https://ardalis.com/clean-architecture-sucks/)
- [Fitness functions / ArchUnit](https://lukasniessen.com/blog/155-fitness-functions-guide/)