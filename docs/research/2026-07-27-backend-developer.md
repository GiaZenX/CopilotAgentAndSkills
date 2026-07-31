# Backend-Developer — Rollenanalyse gegen publizierte Standards

Gelesen: `docs/HARNESS_V2_SPEC.md` II.2/II.4/II.5/II.6a/II.11, `team-kits/dev-team/skills/backend-developer/SKILL.md` (42 Zeilen), die Schwesterrollen `frontend-developer`, `software-architect`, `quality-engineer`, `team-kits/office-team/skills/office-developer/SKILL.md`, `team-kits/research-team/skills/research-engineer/SKILL.md`, `team-kits/dev-team/constitution/AGENTS.md` §2/§5/§6, sowie die real existierende Mechanik: `team-kits/kernel/backlog_types.py` (`REQUIRED_FIELDS["SR"] = ("title","derives_from","contract","affected_components")`), `team-kits/dev-team/templates/repo/scripts/kit_checks.py`, `.../quality.py`, `team-kits/dev-team/hooks/gate_test_coverage.py`, `team-kits/dev-team/templates/project_memory/project_config.yaml`.

---

## 1. Was die SKILL.md heute gut macht

**(a) Sie bindet die Rolle an einen Work Order statt an Prosa.** Der „Read first"-Block nennt exakt die Felder, die ein Gate ebenfalls liest:

> „Dein `TSK` — `derives_from` names the SR, `acceptance_refs` the criteria you are measured against, `required_inputs` the exact files, and `allowed_scope`/`forbidden_scope` the only paths you may touch."

Das ist die richtige Konstruktion: Die Instruktion beschreibt genau die Felder, die `gate_dispatch` und `gate_write_scope` mechanisch auswerten. Anweisung und Durchsetzung sprechen über dasselbe Objekt.

**(b) Sie verweigert die Selbstermächtigung und nennt den Durchsetzer.**

> „Do NOT create or edit task items: the kernel created your `TSK` before you were spawned and its work-order fields are frozen. Your status moves through the result envelope you hand back (`SUBMITTED` or `FAILED`) — never by editing the file, which `gate_write_scope` refuses anyway."

Vorbildlich nach der Harness-Regel: Die SKILL behauptet keine Durchsetzung, sie *zitiert* die vorhandene.

**(c) Die Kostenregel hat eine empirische Herkunft, keine Meinung.**

> „in your dev loop run ONLY the failing + affected tests (single files / `-k`), and run `scripts/quality.py` at most ONCE right before handing off … (a real task ran the full pipeline 4x for identical content)."

**(d) Die Autoritätsgrenze bei fehlenden Regeln ist sauber gezogen:** „If a coding/testing guideline for your language is missing, flag it to the PM (architect appends it) — never invent a permanent rule yourself." Genau richtig — der Implementierer wird nicht zum Regelgeber.

**(e) Envelope-Disziplin** (`≤ 4 KB`, Logs referenziert statt eingefügt) ist konsistent mit II.5.

---

## 2. Der Befund, der alles andere ordnet

Der User sieht das Problem im Frontend. Der Grund, warum es dort sichtbar ist und im Backend nicht, steht in den Skills selbst:

| | Frontend-Developer | Backend-Developer |
|---|---|---|
| Eingefrorenes Vertragsartefakt | **ja** — `design_ref` → `design/revisions/DSN-nnnn.html` | **keins** |
| Dispatch blockiert ohne dieses Artefakt | **ja** (Gate-Schicht 2, II.4) | **n/a** |
| Pflicht-Vorstufe vor Implementierung | **ja** — WFR bei *jedem* UI-Scope, „auch class small" (II.2) | **keine** |
| Craft-Regeln mit benanntem Fehlermodus | 5 (mockup-as-base, jsdom≠Browser, Delivery-Freshness, Consistency-Assertions, Secure-Context-Helper) | **0** |
| Fachlicher Kern | ~28 Zeilen | **1 Satz**: „Implement the server-side code in `src/**` against the SRs and the coding guidelines" |

Das ist keine Nachlässigkeit einer Datei, sondern eine **Asymmetrie in der Spezifikation**: II.2 macht die Wireframe-Stufe für jeden UI-Scope verpflichtend und `design_ref` zur Dispatch-Bedingung; für einen API-Scope existiert kein Gegenstück. Der Backend-Entwickler bekommt einen `SR.contract` — ein Freitextfeld — und darf sich den Rest ausdenken. „Lifeless und AI-generated" ist im Backend genau das: keine durchgehende Fehlerhülle, keine benannten Operationen, jedes Endpoint ein Einzelstück. Man sieht es nur nicht.

Die Verdachtsdiagnose des Users ist damit textlich bestätigt, bevor eine Zeile Code angesehen wurde.

---

## 3. Lücken gegen publizierte Standards — je mit GATE/SKILL-Urteil

### L1 — Kein Schnittstellenartefakt: OpenAPI fehlt vollständig

**Standard:** [OpenAPI Specification](https://spec.openapis.org/) (OpenAPI Initiative / Linux Foundation), [Repo](https://github.com/OAI/OpenAPI-Specification). Wichtig für die Ehrlichkeit: Die OAI **schreibt design-first nicht vor** — die Spec unterstützt beide Richtungen. „Spec zuerst geschrieben" ist deshalb *nicht* prüfbar; „Spec existiert, ist gültig und deckt sich mit der Implementierung" ist es.

**Urteil: GATE (drei Stufen, alle mit beschreibbarem Fehler) + SKILL (der Rest).**

GATE-Stufe 1 — *Existenz und Gültigkeit*: Deklariert `project_config.yaml` eine HTTP-Oberfläche, muss `api/openapi.yaml` existieren und gegen OAS 3.1 validieren.
Fehler: `api/openapi.yaml: 'paths./orders.post.responses.422.content' → unbekannter Media-Type-Key` → Block.

GATE-Stufe 2 — *Bindung an den Zustand*: Jede `SR`, deren `contract` einen `operationId` nennt, muss auf eine Operation zeigen, die in dem Dokument wirklich existiert — und umgekehrt darf keine Operation ohne SR existieren.
Fehler: `SR-0007.contract.operation: createOrder — kein operationId 'createOrder' in api/openapi.yaml` → Block. Bzw.: `Operation 'deleteOrder' in api/openapi.yaml wird von keiner aktiven SR getragen` → Block.
Das ist billig (reines YAML-Lesen, stdlib) und es ist der Punkt, an dem `SR.contract` aufhört, Prosa zu sein.

GATE-Stufe 3 — *Breaking-Change-Erkennung*: [oasdiff](https://github.com/oasdiff/oasdiff) gegen den Merge-Base; ein Breaking Change ohne APPROVED `CR` blockiert den Merge.
Fehler: `response-property-removed: GET /orders/{id} → 200 → total; kein CR-Item nennt diese Änderung` → Block.
Das ist die exakte Backend-Entsprechung zur bestehenden UI-Inventory-Snapshot-Regel („Removing/replacing/renaming a VISIBLE UI element is ALWAYS a CR", §7 der Verfassung). Ein entferntes Response-Feld ist derselbe Vertragsbruch, nur unsichtbar.

**SKILL** bleibt: *welche* Ressourcen es gibt, wie sie geschnitten sind, welche Statuscodes fachlich richtig sind. Reines Urteil.

**Adoption/Streit, ehrlich:** [OAS 3.2](https://spec.openapis.org/oas/v3.2.0.html) ist veröffentlicht, aber Tooling (Spectral, oasdiff, Generatoren) hinkt hinterher. **3.1 als Boden festschreiben**, 3.2 nicht erzwingen. — Für Stil-Linting ist [Spectral](http://opensource.zalando.com/zally/) bzw. [Zally](http://opensource.zalando.com/zally/) verfügbar; die [Zalando RESTful API Guidelines](http://opensource.zalando.com/restful-api-guidelines/) sind der bekannteste extern publizierte, maschinenlesbare Regelsatz mit MUST/SHOULD/COULD-Severities. Das ist der Beleg, dass „API-Geschmack" tatsächlich in Regeln zerlegbar ist — aber der volle Zalando-Satz ist für dieses Harness zu groß; er gehört als *optionaler* Ruleset-Verweis in die SKILL, nicht als Default-Gate.

---

### L2 — Fehlerformat: kein Standard, kein Zwang

**Standard:** [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) (obsoletet RFC 7807, mit IANA-Registry für Problem-Type-URIs).

**Urteil: GATE.** Und zwar das billigste hier mit dem größten Sichtbarkeitseffekt.

**Das ist im Backend, was das Farb-Token im Frontend ist.** Die Frontend-Diagnose „hardcodiert eine Farbe → Gate FAIL" hat ihr exaktes Gegenstück: Drei Endpoints, die `{"error": "..."}`, `{"detail": ...}` und `{"message": ..., "code": 4711}` zurückgeben, sind genau derselbe Defekt — eine Oberfläche ohne System, Endpoint für Endpoint neu erfunden. Und es ist genauso mechanisch prüfbar.

Prüfung: Jede `4xx`/`5xx`-Response im OpenAPI-Dokument deklariert `application/problem+json` und ein Schema, das `type`/`title`/`status` enthält.
Fehler: `POST /orders → 422 deklariert 'application/json'; RFC 9457 verlangt 'application/problem+json' (INV-0004)` → Block.
Zweite Stufe, sobald Stufe 1 läuft: ein Test, der jede deklarierte Fehlerantwort einmal auslöst und den Content-Type der *echten* Antwort prüft — sonst prüft man nur das Dokument, nicht den Server.

---

### L3 — Idempotenz und Nebenläufigkeit kommen nirgends vor

**Standards:**
- [draft-ietf-httpapi-idempotency-key-header-07](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) (IETF HTTPAPI WG, Stand Okt. 2025). **Ausdrücklich: Internet-Draft, kein RFC.** Wer das in einer SKILL „RFC" nennt, lügt die Verbindlichkeit hoch. Der Header-*Name* ist de-facto verbreitet (Stripe u. a.), aber nicht standardisiert.
- [RFC 9110 §13 — Conditional Requests](https://www.rfc-editor.org/rfc/rfc9110.html), `ETag` + `If-Match` → `412 Precondition Failed` als der standardisierte Weg gegen das Lost-Update-Problem. Das *ist* ein verabschiedeter Standard.

**Urteil: SKILL für das Ob, GATE für das Behauptete.**

Ob ein Endpoint Idempotenz *braucht*, ist Urteil (hängt an Retry-Verhalten, Geld, Seiteneffekten) → SKILL. Aber sobald eine SR es behauptet, ist die Behauptung prüfbar:

GATE: Eine `SR`, deren `contract` `idempotent: true` oder `concurrency: optimistic` trägt, muss ein `INV`-Item nennen, dessen `check.ref` auf einen **existierenden und sammelbaren** Test zeigt. Die Mechanik dafür ist schon spezifiziert (II.2: „Der State-Validator (fail-closed) prüft EXISTENZ und Sammelbarkeit des referenzierten Tests; fehlt er, gilt die Invariante als `unverified` und blockiert Merge/Abnahme") — sie muss nur für diesen Fall *verlangt* werden.
Fehler: `SR-0011 erklärt POST /payments idempotent, nennt aber kein INV mit check.ref` → Block. Bzw. `INV-0009.check.ref = tests/test_payments.py::test_replay_same_key — nicht sammelbar` → `unverified` → Merge blockiert.

Der Test selbst ist trivial beschreibbar und gehört in die SKILL als *Muster*: derselbe Request zweimal mit demselben Key → identische Antwort, **eine** Zeile in der Datenbank. Bzw. für Concurrency: zwei `PUT` mit demselben `If-Match`-ETag → der zweite bekommt `412`.

---

### L4 — Observability: kein Wort über Instrumentierung

**Standards:** [OpenTelemetry Semantic Conventions for HTTP spans](https://opentelemetry.io/docs/specs/semconv/http/http-spans/) — **stabil** ([Stabilitätsankündigung](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)); Required für Server-Spans: `http.request.method`, `url.path`, `url.scheme`. `http.route` ist *conditionally required* und „MUST be low-cardinality and include all static path segments, with dynamic path segments represented with placeholders". Span-Name = `{method} {target}`, und ausdrücklich: „Instrumentation MUST NOT default to using URI path as a `{target}`". Kontextweitergabe: [W3C Trace Context](https://www.w3.org/TR/trace-context/) (W3C Recommendation, `traceparent`/`tracestate`).

**Urteil: SKILL im Default, GATE nur bei deklarierter Observability.**

*Ob* instrumentiert wird, ist eine Architekturentscheidung (Decision-Item des Architekten). Ein lokal laufendes Einzelprojekt braucht kein OTel; das als Gate zu erzwingen wäre Zeremonie. **Sobald aber ein Knopf in `project_config.yaml` (`observability: otel`) gesetzt ist, wird es hart prüfbar** — und zwar gerade das, was Menschen falsch machen:

GATE: Ein Test startet die App mit einem In-Memory-Span-Exporter, ruft je deklarierter Route einmal auf und prüft: (1) genau ein Server-Span, (2) `http.route` vorhanden und gleich dem Template-Pfad, (3) Span-Name == `{method} {route}`, (4) `traceparent` wird an ausgehende Requests weitergereicht.
Fehler: `Span-Name 'GET /orders/1f3c-9ab2-…' enthält ein dynamisches Segment → Kardinalitätsexplosion; erwartet 'GET /orders/{id}' (semconv http-spans)` → FAIL.

Das ist ein Gate mit einem präzise beschreibbaren Fehler und es fängt genau den Defekt, der in Produktion teuer wird und den kein Reviewer sieht.

---

### L5 — Sicherheit ist an das Jahr gebunden, nicht an die Änderung

**Standards:** [OWASP ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/) (Mai 2025, ~350 Anforderungen in 17 Kapiteln, L1/L2/L3; als PDF/Word/**CSV** und über [github.com/OWASP/ASVS](https://github.com/OWASP/ASVS)); [OWASP API Security Top 10 – 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) mit **API1:2023 Broken Object Level Authorization** an Platz 1.

Heute deckt das Harness Sicherheit über zwei Wege ab: `quality.py` fährt SAST + Secret-Scan + SCA, und der Architekt legt bei sicherheitsrelevanten SRs ein STRIDE-Decision-Item an (Architect-SKILL Schritt 7). Was fehlt, ist die **Bindung an die konkrete Änderung** — und exakt die Klasse Fehler, die SAST prinzipiell nicht findet.

**Urteil: zwei getrennte Dinge, unterschiedlich einzuordnen.**

**ASVS-Inhalt = SKILL.** 350 Anforderungen pro Task durchzugehen ist Theater. OWASP selbst nennt als Verwendungszwecke „yardstick / development guidance / procurement" — kein Hook. Das gehört als kurze, auf die Änderung anwendbare Auswahl in die SKILL.

**ASVS-*Referenz* = GATE.** Eine `SR`, die eine authentifizierte oder autorisierende Oberfläche berührt, trägt `asvs: [V8.1.1, …]`; jede ID muss in der mitgelieferten ASVS-5.0-CSV auflösbar sein.
Fehler: `SR-0014.asvs nennt 'V99.1.1' — in ASVS 5.0 nicht vorhanden` → Block. (Fängt genau das, was ein LLM hier zuverlässig produziert: plausibel aussehende, erfundene Requirement-IDs.)

**Der wertvollste Einzel-Gate steht bei BOLA und ist vollständig aufzählbar:**
Aus dem OpenAPI-Dokument sind alle Operationen mechanisch bestimmbar, die (a) einen Pfadparameter haben und (b) ein `security`-Requirement tragen. Für jede davon muss ein Test registriert sein, der die Ressource als **anderer, ebenfalls authentifizierter** Principal anfragt und `403`/`404` erwartet.
Fehler: `Operation 'getOrder' (GET /orders/{id}) hat Pfadparameter + security, aber keinen registrierten Cross-Tenant-Negativtest` → Block.
Das ist die publizierte **Nummer-1-API-Risiko-Klasse**, sie ist eine reine Logiklücke, und weder Linter noch SAST noch Secret-Scan finden sie je. Es ist damit eine echte Ergänzung der Pipeline und keine Dublette.

---

### L6 — Migrationen: keine Regel für alles Persistente

**Standards:** [DORA — Database change management](https://dora.dev/capabilities/database-change-management/): „Teams that do well at continuous delivery store their database changes as scripts in version control and manage these changes in the same way they manage production application changes", „Treat all database schema changes as migrations", und für Zero-Downtime explizit das Parallel-Change-Muster. [Fowler, ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) — *expand → migrate → contract*. [Fowler/Sadalage, Evolutionary Database Design](https://martinfowler.com/articles/evodb.html) — „we represent every change to the database as a database migration script which is version controlled together with application code changes."

**Urteil: GATE für die Form, SKILL für das Muster.**

GATE 1: Ändert ein Commit-Bereich ein Persistenzmodell (deklarierte Modelldateien/Verzeichnis), muss im selben Bereich eine neue nummerierte Migrationsdatei liegen.
Fehler: `src/db/models.py geändert, keine neue Datei unter migrations/ in diesem Bereich` → Block.

GATE 2: Eine Migration, die `DROP COLUMN`/`DROP TABLE`/`RENAME` enthält, braucht ein aktives `CR`- oder Decision-Item, das sie nennt.
Fehler: `migrations/0007_x.sql enthält 'DROP COLUMN total'; kein CR/Decision-Item nennt diese Migration — destruktive Schemaänderungen laufen über expand/contract oder über eine Freigabe` → Block.
Das liegt mechanisch sehr nah an dem, was `check_module_invariants` in `kit_checks.py` schon kann („files that must never contain given tokens") — nur pfad-glob- und diff-bewusst statt datei-fix.

GATE 3: Die Migration läuft in CI *vorwärts gegen eine leere UND gegen eine geseedete DB*, danach die Suite. Fehler: der Migrationslauf bricht ab → FAIL, mit dem Tool-Output.

**Ausdrücklich NICHT: „jede Migration braucht ein `down()`."** Siehe Abschnitt 5.

---

### L7 — „Write unit tests" ist die einzige Testaussage der Rolle

**Standard/Diskussionsstand:** [Fowler, „On the Diverse and Fantastical Shapes of Testing"](https://martinfowler.com/articles/2021-test-shapes.html) zitiert zustimmend Justin Searls: „People love debating what percentage of which type of tests to write, but it's a distraction. Nearly zero teams write expressive tests that establish clear boundaries, run quickly & reliably, and only fail for useful reasons. Focus on that instead." Für die Datenschicht: [Testcontainers](https://java.testcontainers.org/) als der etablierte Weg, gegen die echte Engine statt gegen Mocks/In-Memory-DB zu testen.

Die Lücke ist **nicht** „das Verhältnis stimmt nicht". Sie ist: Die SKILL nennt genau *einen* Testtyp und lizenziert damit eine mock-only Datenschicht. Die QA-SKILL verbietet mock-only für laufzeitkritische Pfade — aber erst *nachdem* der Code geschrieben ist. Das Harness bezahlt diese Schleife zweimal, und die Verfassung §14a zählt die dritte QA-Runde als Stopp-Bedingung.

**Urteil: SKILL (der Satz über echte Engines) + ein schmales GATE.**

GATE: Ist ein DB-Stack in `project_config.yaml` `stacks:` deklariert, muss mindestens ein Test die echte Engine benutzen (Fixture-/Marker-Konvention).
Fehler: `stack 'postgres' deklariert, aber kein Test verwendet die 'postgres_container'-Fixture — die Datenschicht ist nur gegen Mocks geprüft` → Block.
Das fügt sich exakt in die bestehende Logik von `quality.py` („A DECLARED stack with no check definition here is a FAIL") und ergänzt `gate_test_coverage.py`, das heute nur fragt, *ob* ein Bereich überhaupt irgendeinen Test hat.

**Kostenehrlichkeit:** Testcontainers braucht Docker. Die QA-SKILL sagt bereits, ein aus Umgebungsgründen übersprungener Real-Run ist „NOT a pass" — dieses Gate muss also *fehlschlagen*, nicht überspringen, und das ist ein echter Preis auf Maschinen ohne Docker-Daemon.

---

### L8 — Harness-Fallstrick, der jede Konfig-Idee betrifft

Alle bestehenden konfigurierbaren Checks (`module_invariants`, `file_budget`, `yaml_lint_exclude`, `coverage_areas`) lesen ihre Knöpfe aus `coding_guidelines.yaml` / `testing_guidelines.yaml`. **V2 liefert für beide kein Template** (Verfassung §2.7, Architect-SKILL Schritt 6), und `gate_write_scope` verhindert, dass irgendeine Rolle sie anlegt. Diese Knöpfe sind heute faktisch tot.

**Konsequenz für jede Empfehlung oben:** Neue Schalter gehören nach `project_config.yaml` — die Datei wird als Template ausgeliefert, und `local_first: false` ist der bestehende Präzedenzfall für „ein Bool, das die Pipeline FAILen lässt". Alles andere wäre ein Gate, das nie feuert — die Sorte Schutzbehauptung, die die Harness-Lessons als wiederkehrenden Fehler notieren.

---

## 4. Die drei hebelstärksten Ergänzungen, in Reihenfolge

### #1 — `api_ref`: dem Backend geben, was `design_ref` für das Frontend ist

Ein `api/openapi.yaml` (OAS 3.1) als eingefrorenes Vertragsartefakt, `SR.contract` bindet an `operationId`, Gate-Stufen 1+2 aus L1. Optional später Stufe 3 (oasdiff).

Warum zuerst: Es behebt die Ursache statt eines Symptoms. Alles andere in dieser Liste — RFC 9457, BOLA-Enumeration, Idempotenz-Deklaration, OTel-Routen — *hängt* an einem maschinenlesbaren Inventar der Endpoints. Ohne das Dokument sind sie nicht aufzählbar und daher nicht gate-fähig. Und es schließt die Spec-Asymmetrie: II.2 verlangt für jeden UI-Scope einen Wireframe, „auch class small"; ein API-Scope hat bis heute keine Pflicht-Vorstufe.

Kosten: eine Konvention für den Dateiort; ~120 Zeilen neuer Check in `kit_checks.py` (stdlib-YAML reicht für Stufe 2; für Stufe 1 `openapi-spec-validator` via pip — Python ist ohnehin die Basis); ein SKILL-Abschnitt bei Backend *und* Architekt (der Architekt besitzt `SR.contract`); eine Ergänzung in `project_config.yaml`. Kein Kernel-Eingriff, kein State-Migration — `contract` ist ein freies Feld und bleibt es formal. Risiko: Projekte ohne HTTP-Oberfläche (CLI, Library, Firmware) müssen sauber ausgeschlossen sein, sonst blockiert das Gate legitime Arbeit — der Schalter in `project_config.yaml` ist dafür Pflicht, nicht Komfort.

### #2 — RFC 9457 als *eine* Fehlerhülle, per Gate

Kosten: am geringsten von allen dreien — sobald #1 steht, ist es ein Durchlauf über `paths.*.responses.4xx|5xx` und ein Vergleich zweier Strings. Plus drei SKILL-Zeilen. Nutzen: der sichtbarste „nicht AI-generiert"-Effekt pro investierter Stunde, weil eine uneinheitliche Fehleroberfläche der zuverlässigste Marker für zusammengestückelte Endpoints ist. Risiko: nahe null — bei bestehenden Projekten ein Migrationsaufwand, den man über einen `CR` fährt.

### #3 — BOLA-Negativtest je parametrisierter, gesicherter Operation

Kosten: mittel. Die Aufzählung ist trivial (aus #1). Die Registrierung braucht eine Konvention (Marker/Naming, der einen Test einer `operationId` zuordnet) und pro Projekt ein zweites Test-Principal-Fixture. Nutzen: fängt das publizierte Nummer-1-API-Risiko, das strukturell außerhalb der Reichweite jedes bereits vorhandenen Pipeline-Schritts liegt. Risiko: Falsch-Positive bei Operationen, deren Pfadparameter kein Ownership trägt (z. B. `/countries/{iso}`) — braucht eine Ausnahmeliste **mit Begründungspflicht**, wie sie `file_budget` bereits vorexerziert.

---

## 5. Was gegen populäre Empfehlungen für diese Rolle spricht

**(a) Pact / Consumer-Driven Contract Testing — hier NICHT einbauen.**
Pacts eigene Dokumentation listet als Nicht-Eignung u. a.: „Testing APIs where the team maintaining the other side of the integration will not also be using Pact", „Testing APIs where the consumers cannot be individually identified (eg. public APIs)", „Functional testing of the provider — that is what the provider's own tests should do" ([docs.pact.io](https://docs.pact.io/getting_started/what_is_pact_good_for)). In diesem Harness sind Consumer und Provider typischerweise **dasselbe Repo, derselbe Branch, zwei Rollen desselben Teams**. Es gibt keinen unabhängigen Consumer, der einen Vertrag treiben könnte. Pact brächte einen Broker, einen `can-i-deploy`-Schritt und eine zweite CI-Abhängigkeit — um eine Garantie zu reproduzieren, die ein einziges OpenAPI-Dokument plus [Schemathesis](https://schemathesis.readthedocs.io/) (property-based Konformanz gegen dieselbe Spec) zu einem Bruchteil liefert. Pact gehört ins Bild, *sobald* ein Projekt real einen zweiten, separat deployten Consumer hat — und dann als **Decision-Item des Architekten**, nicht als Zeile in der Backend-SKILL. (PactFlows eigene Gegenüberstellung ordnet bi-direktionales Contract-Testing ausdrücklich den Fällen zu, in denen man den Provider *nicht* kontrolliert — [pactflow.io](https://pactflow.io/difference-between-consumer-driven-contract-testing-and-bi-directional-contract-testing/).)

**(b) Eine Regel zur Testpyramiden-*Quote* wäre ein Fehler.**
Fowler selbst nennt die Verhältnis-Debatte eine Ablenkung (siehe L7). Ein Gate auf Testtyp-Anteile würde eine Zahl mit maschineller Autorität durchsetzen, die niemand verteidigen kann — genau die Sorte Schein-Gate, gegen die die GATE/SKILL-Trennung dieses Harness existiert. Der prüfbare Kern ist „jeder Quellbereich hat Tests" (hat `gate_test_coverage.py` bereits) und „die Datenschicht wurde gegen die echte Engine geprüft" (L7) — nicht „30 % Integration".

**(c) „Jede Migration braucht eine `down()`-Migration" — die Primärquelle sagt das Gegenteil.**
Fowler/Sadalage zu automatisierten Rückwärtsmigrationen: „We haven't found this to be cost effective and beneficial enough to try all the time"; sie bevorzugen stattdessen, die Datenzugriffsschicht mit **beiden** Schema-Versionen arbeiten zu lassen ([evodb](https://martinfowler.com/articles/evodb.html)). Ein Reversibilitäts-Gate würde das Team zum gefährlicheren Muster drängen (eine große, „rückrollbare" Änderung) statt zum sichereren (Parallel Change). Deshalb oben GATE auf *Form und Freigabe* der Migration, nie auf `down()`.

**(d) „Idempotency-Key ist Standard" — nein, noch nicht.**
`draft-ietf-httpapi-idempotency-key-header-07` ist Internet-Draft mit Zielstatus Standards Track, kein RFC ([datatracker](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)). Verbreitet, aber nicht verabschiedet. Eine SKILL darf den Header empfehlen; ein Gate darf ihn nicht als Norm erzwingen. Der *verabschiedete* Standard für den benachbarten Fall ist [RFC 9110 §13](https://www.rfc-editor.org/rfc/rfc9110.html) (`ETag`/`If-Match` → `412`) — dort darf man härter sein.

**(e) „Immer die neueste OpenAPI-Version."**
OAS 3.2 ist da, das Ökosystem nicht. 3.1 als Boden, 3.2 erlauben, nicht verlangen.

**(f) „OpenAPI-first" als Regel formulieren.**
Die OAI schreibt keine Reihenfolge vor. „Die Spec wurde zuerst geschrieben" ist unbeobachtbar und wäre damit ein Gate ohne beschreibbaren Fehler — also gar keins. Prüfbar ist ausschließlich, dass die Spec existiert, gültig ist und zur Implementierung passt. Diese Unterscheidung ist der Unterschied zwischen einem Gate und einer Behauptung, und sie sollte in der SKILL selbst so stehen.

---

**Relevante Pfade:**
`c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\backend-developer\SKILL.md`
`c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\kit_checks.py`
`c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\repo\scripts\quality.py`
`c:\Offline Repos\AgentAndSkills\team-kits\dev-team\hooks\gate_test_coverage.py`
`c:\Offline Repos\AgentAndSkills\team-kits\dev-team\templates\project_memory\project_config.yaml`
`c:\Offline Repos\AgentAndSkills\team-kits\kernel\backlog_types.py`

**Quellen:** [OpenAPI Specification](https://spec.openapis.org/) · [OAS 3.2](https://spec.openapis.org/oas/v3.2.0.html) · [OAI Repo](https://github.com/OAI/OpenAPI-Specification) · [oasdiff](https://github.com/oasdiff/oasdiff) · [Zalando RESTful API Guidelines](http://opensource.zalando.com/restful-api-guidelines/) · [Zally](http://opensource.zalando.com/zally/) · [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) · [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) · [draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) · [OTel HTTP semconv](https://opentelemetry.io/docs/specs/semconv/http/http-spans/) · [OTel HTTP stable](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/) · [W3C Trace Context](https://www.w3.org/TR/trace-context/) · [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) · [OWASP/ASVS GitHub](https://github.com/OWASP/ASVS) · [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) · [DORA Database Change Management](https://dora.dev/capabilities/database-change-management/) · [Fowler ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) · [Fowler Evolutionary Database Design](https://martinfowler.com/articles/evodb.html) · [Fowler Test Shapes](https://martinfowler.com/articles/2021-test-shapes.html) · [Pact: what is Pact good for](https://docs.pact.io/getting_started/what_is_pact_good_for) · [PactFlow CDC vs BDCT](https://pactflow.io/difference-between-consumer-driven-contract-testing-and-bi-directional-contract-testing/) · [Schemathesis](https://schemathesis.readthedocs.io/) · [Testcontainers](https://java.testcontainers.org/)