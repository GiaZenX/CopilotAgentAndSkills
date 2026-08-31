# Skill-Umfeld 2026-08-31 — was adoptierbar ist, was nicht (FR-0068)

Drei parallele Recherchen (Anthropic offiziell · Community · Büro-Fachdomäne), Anlass:
Nutzerfrage 2026-08-31 „was für skills gibt es noch die gut bewertet sind und zu unseren Agenten
passen?". Diese Datei hält die MESSUNG fest; die Entscheidung, was davon gebaut wird, steht in
`FR-0068` und den dort genannten Nachbarn. Vorgänger und weiterhin die inhaltlich bessere Analyse
des Anthropic-Textes: `docs/research/2026-07-27-adoption-anthropic.md` + `-SYNTHESE.md`.

## 1. `anthropics/skills` — Stand gegen Juli

19 statt 13 Ordner. Neu: `academy-guide`, `discernment-nudge` (beide Apache-2.0, beide setzen
Endnutzerdialog UND Sitzungsgedächtnis voraus → kein Fit für Rollen, die nicht mit dem Nutzer
sprechen), sowie in der Juli-Liste bereits geführt `doc-coauthoring` (**unlizenziert**, 404 auf
`LICENSE.txt` UND auf das Repo-Root-`LICENSE` → nicht adoptierbar, unverändert).

**`frontend-design`: byte-gleich zu Juli.** Alle in der Juli-Datei wörtlich zitierten Passagen
wurden erneut gezogen und stimmen überein. Apache-2.0, `LICENSE.txt` im Ordner, Copyright
„Anthropic, PBC". Die Juli-Ablehnung stützte sich auf EINE Zahl — 121 Zeilen gegen ein
150-Zeilen-Budget — und die gehört der **Rollendefinition**, nicht einer registrierten SKILL-Datei
(`tools/test_context_budget.py::test_no_skill_a_session_can_reach_claims_to_be_preloaded` pinnt,
dass ein Skill nicht vorgeladen wird). Die ZWEITE Juli-Einschränkung bleibt textlich wahr und ist
die eigentliche Arbeit jeder Adoption: der Text unterstellt einen Agenten, der mit dem Nutzer
spricht und selbst baut, was er entworfen hat.

**Die vier Dokument-Skills (`pdf`, `docx`, `xlsx`, `pptx`) sind PROPRIETÄR** — alle vier
`LICENSE.txt` einzeln geprüft, Wortlaut identisch: „Users may not: Extract these materials from
the Services or retain copies of these materials outside the Services — Reproduce or copy these
materials … — Create derivative works based on these materials — Distribute, sublicense, or
transfer …". Das ist ein hartes Verbot, das auch die **paraphrasierte** Übernahme in ein
ausgeliefertes Kit trifft. Bitter, weil ihr Ausführungsmodell (reine Datei-Ein-/Ausgabe, kein
Dialog, kein Gedächtnis) exakt zum Büro-Kit passt — es gibt hier **keine** Handlungsoption.

**`webapp-testing` ist der übersehene Fund** (Apache-2.0): kein Endnutzerdialog, kein Gedächtnis,
Playwright-Black-Box-Skripte — dasselbe Ausführungsmodell wie unsere Spezialisten. Fit:
`quality-engineer`, `frontend-developer`; und es ist genau die Fähigkeit, die `BUG-0076` braucht
(einen Entwurf rendern und ansehen). `internal-comms` trägt ein FORM-Muster (Körper = Router,
Detail in `examples/`), `brand-guidelines` die Form eines Anti-Referenz-Eintrags.

## 2. Community — die Sichtbarkeit korreliert negativ mit der Brauchbarkeit

Die drei sternenstärksten Sammlungen sind **lizenzlos** und damit raus: `ComposioHQ`
(74 136 ★), `travisvn` (14 913 ★), `BehiSecc` (10 080 ★) — je `license: null`, kein Root-LICENSE.
Eine Sammlung ohne Lizenz ist ein Wegweiser für eigene Recherche, keine Quelle zum Übernehmen.

Brauchbar, per GitHub-API gemessen (nicht aus Werbetexten):

| Repo | Lizenz | ★ | letzter Push | Fit | Preis der Adoption |
|---|---|---|---|---|---|
| `wshobson/agents` | MIT | 39 293 | 2026-08-31 | `quality-engineer`, `devops-engineer`, `backend-developer`, `software-architect` | Rollentexte unterstellen Direktdialog mit dem Entwickler UND ein externes Gedächtnismodul (Pensyve) — beides gegen II.5 und gegen unsere PM-Konvention; jede Datei muss umgeschrieben werden |
| `alirezarezvani/claude-skills` | MIT | 25 303 | 2026-08-30 | `compliance-researcher` (Compliance/ISO/GDPR), `marketing-planner`, teils `product-editor` | 388 Skills, im Detail UNGELESEN; Finance-Bereich ist Investorenanalyse, NICHT Buchhaltung → kein `bookkeeper`-Fit |
| `GetBindu/awesome-…` | Apache-2.0 | 187 | 2026-08-31 | ungeprüft | klein, aktiv, für eine Folgerunde vorgemerkt |

`VoltAgent/awesome-agent-skills` (33 464 ★, MIT) ist ein **Register**, kein Inhalt — als Suchindex
nützlich, jeder Treffer einzeln zu prüfen.

**Ehrliche Lücke:** für `bookkeeper`, `records-clerk`, `shop-curator` und die Research-Rollen wurde
NICHTS lizenzsauber Passendes gefunden. Das heißt „nichts gefunden", nicht „gibt es nicht".

## 3. Büro-Fachdomäne — Quellen, keine Skills

Für die Büro-Rollen ist die Ausbeute strukturell anders: es gibt keine fertigen Skills, sondern
**autoritative Quellen**, aus denen wir selbst schreiben müssten. Die belastbaren:
XRechnung-Spezifikation 3.0.2 über KoSIT/`xeinkauf.de` (Lizenztext ungeprüft), `schema.org/gtin`
(Formatregeln verifiziert: 8/12/13/14 Stellen, GS1-Prüfziffer), GS1 Germany als Vergabestelle,
und die E-Rechnungs-Fristen (Empfangspflicht seit 2025; Ausstellungspflicht 2027 ab 800 000 €
Vorjahresumsatz, 2028 für alle).

**Nicht belastbar und ausdrücklich so gemeldet:** der wörtliche GoBD-Pflichtinhalt einer
Verfahrensdokumentation (die amtlichen PDFs ließen sich nicht textextrahieren), der Gesetzeswortlaut
zu den verkürzten Aufbewahrungsfristen (BEG IV: 8 Jahre für Buchungsbelege, 10 für Abschlüsse — nur
sekundär belegt), § 14 UStG, der Stand der Anlage EÜR 2026, und die Kleinunternehmer-Schwellen 2026.
Bei einem Thema mit der Folge „Buchführung verworfen" ist eine Steuerberater-Blogquelle **kein**
Fundament für eine Kit-Regel. Wer daraus etwas baut, zieht vorher die amtlichen Texte selbst.

## Urteil

Adoptieren: `frontend-design` (Apache-2.0, FR-0068) und `webapp-testing` (Apache-2.0) — beide mit
Lizenzkopie, Änderungskennzeichnung und einer Zeile in `NOTICES.md`. Prüfen, dann entscheiden:
`wshobson/agents` je Datei, `alirezarezvani` je Datei. Nicht adoptierbar: die vier
Dokument-Skills (proprietär), `doc-coauthoring` (unlizenziert), die drei sternenstarken
Sammlungen (lizenzlos). Selbst schreiben, aus amtlichen Quellen: die Büro-Fachregeln.
