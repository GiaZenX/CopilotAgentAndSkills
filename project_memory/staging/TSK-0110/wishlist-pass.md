# TSK-0110 / FR-0036 — wishlist pass over `docs/POST_V2_WISHLIST.md` sections 1-10

**For the LEAD to apply.** This stream may not edit the wishlist (six other streams append to it),
so this is the list, not the edit. One line per section: the FR pointer that exists, a thin FR that
does not exist yet, or a supersession with the closing reference.

Read against `project_memory/inbox/active/FR-*.yaml` and `project_memory/archive/FR/2026/FR-*.yaml`
(74 items) and `decisions/active/` on 2026-09-02.

**FR-0003 folds in — already, in the state, not by this pass.** `archive/FR/2026/FR-0003.yaml` is
`status: MERGED`, `resulting_item: FR-0036`, `closed_at: 2026-08-25`. Its `triage_result` names
exactly the remainder this pass closes: "wishlist sections 1-10 still have no thin FR items". No
action for the lead beyond citing it.

---

## Section 1 — Skills der Rollen gegen anerkannte Standards härten

Three sub-sections, and they do NOT share a fate:

- **1b (Claude Design — Bündelformat übernehmen): SUPERSEDED by `FR-0045`**
  (`archive/FR/2026/FR-0045.yaml`, `MERGED`). Its own `request_text` names the origin: "it lives as
  prose in POST_V2_WISHLIST section 1b, never migrated". Delivered in the first stream generation
  (stream A / TSK-0100, see `DEC-0060`).
- **1c residue — THIN FR NEEDED: "Die mechanisch prüfbaren Hälften der Standard-Härtung bauen
  (C1/C2/C3 axe-Lauf + Tastaturpfad + `prefers-reduced-motion`/`:focus-visible`, B2/B3 Farbliterale)"**.
  The section says of these, verbatim, "NICHT gebaut", and nothing in the store carries them.
  `FR-0068`/`FR-0070`/`FR-0071` (all `MERGED`) vendored Anthropic's skills — that is a different
  wish; it added capability, it did not build the mechanical checks §1c lists.
- **1 + 1a (Führung und Rangfolge): THIN FR NEEDED — "Ein GATE auf je genau EIN primäres Ziel pro
  View, plus die SKILL-Zeile mit Verfahren statt Adjektiv"**. §1a names the gate/skill split itself;
  no item carries it.

## Section 2 — Board- und Backlog-Ansichten

- **FR pointer exists: `FR-0024`** (ACTIVE, TRIAGED). Its `request_text` says so in the file:
  "Beruehrt: Wunschliste Abschnitt 2 (Board-Ansichten)". The wishlist has no pointer back — that is
  the edit.
- Also delivered against this section: `FR-0030` and `FR-0053` (both `MERGED`, dashboard/board v2)
  and `FR-0017` (ACTIVE) for the "Gliederungsebene über dem Requirement" decision.
- **Remainder — THIN FR NEEDED: "Termine für die Timeline als eigener Vorgangstyp (MST) statt als
  Feld"**. The section states it as the decision that must fall before implementation; no item
  holds it.

## Section 3 — Der Plan als Bild, nicht nur als Text

- **THIN FR NEEDED: "Umsetzungsplan und Mindmap als `.drawio.svg`, generiert statt gepflegt"**.
  Re-measured 2026-09-02 (the first pass of this file said "no item contains `drawio`" and was
  wrong by one item): `mindmap` occurs in NO item at all, and `drawio` in exactly one —
  `bugs/active/BUG-0074.yaml`, where it names the wireframe files a freeze cleared
  (`WFR-000n.drawio.svg`). So the FORMAT is already in use in the kits for wireframes (`WFR`) and
  architecture diagrams (`ARC-0001.drawio.svg`, see `project_memory/README.md`); the wish is to
  extend it to the plan and the mindmap, and the thin FR should say so rather than introduce the
  format. The section's own open question is already answered inside it (generated, via
  `docs/research/2026-07-27-plan-als-diagramm.md`), so the FR is a build wish, not a research one.

## Section 4 — Effort-Stufen pro Rolle statt pro Modell

- **FR pointer exists: `FR-0047`** (ACTIVE, "Modell-Stufe je Rolle festnageln und stilles
  Herunterstufen sichtbar machen"), and the target state is decided in **`DEC-0034`** (T0-T3 ladder,
  VALID, deliberately not built) with **`DEC-0059`** as the casting layer over it.
- Note for the lead: this is the section where CLAUDE.md's "SOLL-Frage zuerst gegen
  `decisions/active/`" rule bites — the built `model_tiers.yaml` and `DEC-0034` disagree by design.
  A pointer that names only `FR-0047` repeats the 2026-08-17 incident; name `DEC-0034` beside it.

## Section 5 — Finanz-Vorlagen für das Office-Kit

- **FR pointer exists for the Nachtrag (the VIEW): `FR-0032`** (ACTIVE, "Office: standardisiertes
  Finanz-HTML-Dashboard — Einnahmen/Ausgaben, offene Posten, EÜR auf einen Blick").
- **Generic half — THIN FR NEEDED: "Kontenrahmen (SKR03/SKR04) + Konto→EÜR-Zeile-Abbildung als
  jahresversionierte Vorlage mit benanntem Rechtsraum"**. `FR-0002` (ACTIVE, eight field adoptions)
  covers filing/retention (F1-F8) and not the chart of accounts; the section's own two conditions
  (year-versioned, legal space named) belong in that new item's acceptance criteria.

## Section 6 — Mehrere Spezialisten derselben Rolle parallel

- **FR pointer exists: `FR-0021`** (ACTIVE). Its `request_text` says it in the file: "Nutzerwunsch
  2026-08-15 (deckt Wunschliste Abschnitt 6 vom 2026-07-31)". Only the back-pointer is missing.

## Section 7 — Ein dritter Evidence-Ausgang: `blocked`

- **THIN FR NEEDED: "`EVIDENCE_RESULTS += blocked`, `gate_git` schliesst darauf wie auf `fail`, und
  der Ehrlichkeitssatz wird mitgebaut"**. Measured: no FR carries it. `FR-0040` (ACTIVE) is the
  neighbour, not the same wish — it wants the SCOPE of a run recorded, this wants a third outcome.
  The new item must carry the section's last paragraph as an acceptance criterion, because the
  section itself says a `blocked` without that sentence reads as a checked fact.

## Section 8 — Ein Projekt vollautonom von Anfang bis Ende

- **FR pointer exists: `FR-0074`** (ACTIVE, TRIAGED 2026-09-02), and the decision behind it is
  **`DEC-0058`** ("Plan-level approval: the user approves the derived goal list ONCE"). Both are
  from 2026-09-02, i.e. AFTER the section was written.

## Section 9 — Der Masterplan braucht einen Zustand

- **SUPERSEDED in its buildable half by `DEC-0058` / `FR-0074`**: the section's one buildable
  sentence ("Eine scope-Freigabe wird nicht angeboten, solange der Plan offene Fragen führt") is
  point (2) of `FR-0074` and is decided in `DEC-0058`.
- **Not superseded, and it must not be presented as if it were:** the other half of the section —
  the masterplan has no WRITER after the install — is the hole list's own `L1` and stays open there.
  The pointer the lead writes has to say which half is closed by what.

## Section 10 — Die Freigabe programmatisch erteilen

- **THIN FR NEEDED: "Freigabe über das Claude Agent SDK (`canUseTool`) erteilen, und ein
  programmatisch geprägter Token muss von einem menschlich geprägten unterscheidbar bleiben"**.
  Measured: no item carries it; the only two files in the store naming the SDK/`canUseTool` are
  `FR-0024` and `FR-0047`, in a different sense.
- The section is already **partly corrected in place** (TSK-0097, 2026-08-30: the "headless
  unerreichbar" premise was refuted, chain and counter-measurement at `H80`), so the thin FR carries
  the wish, not the refuted premise.

---

## Summary for the lead

| § | verdict | reference |
|---|---|---|
| 1b | superseded | `FR-0045` (MERGED) |
| 1c | thin FR needed | mechanical halves C1/C2/C3, B2/B3 — "NICHT gebaut" per the section |
| 1/1a | thin FR needed | one primary goal per view as a gate + procedure line in the SKILL |
| 2 | pointer exists | `FR-0024` (says so itself); `FR-0030`, `FR-0053`, `FR-0017` |
| 2 | thin FR needed | timeline dates as an own item type (MST) |
| 3 | thin FR needed | plan + mindmap as generated `.drawio.svg` |
| 4 | pointer exists | `FR-0047` **and** `DEC-0034` (+ `DEC-0059`) |
| 5 | pointer exists | `FR-0032` (the view half) |
| 5 | thin FR needed | chart of accounts + EÜR mapping, year-versioned, legal space named |
| 6 | pointer exists | `FR-0021` (says so itself) |
| 7 | thin FR needed | `blocked` as a third evidence outcome |
| 8 | pointer exists | `FR-0074` + `DEC-0058` |
| 9 | superseded (half) | `DEC-0058`/`FR-0074`; the writer half stays open as `L1` |
| 10 | thin FR needed | approval via the Agent SDK, with token provenance |

**Die Tabelle darüber IST die Liste; diese Zeile zählt sie, sie zählt nicht zum zweiten Mal.**
Gezählt am 2026-09-02 mit `_round-scratch/TSK-0110/rework1/count_pass.py` über genau diese Tabelle
(Ausgabe im Rundenprotokoll, Abschnitt 9): **14 Zeilen — 7× „thin FR needed", 5× „pointer exists",
2× „superseded"**. Die erste Fassung dieser Zeile sagte „eight / six / two" und war falsch; keine
Zeile fehlte, die Zahl war es. Drei Abschnitte (1, 2, 5) brauchen BEIDES — einen Rückverweis und ein
dünnes FR —, weil der Abschnitt mehr trägt als das vorhandene Item; das ist der Grund, warum
FR-0036 einen gemessenen Durchgang verlangt hat und keine Zählung.

---

## Was der Lead eintragen soll — Wortlaut je Abschnitt (Nacharbeit 1, N6)

Damit die Zeigerzeilen ohne Nachlesen ausführbar sind: je Abschnitt der Anker (Überschrift, mit der
Zeilennummer vom Stand 2026-09-02 als Beigabe — die Überschrift ist der Anker, die Zahl wandert) und
der Satz, der als **letzte Zeile des Abschnitts** eingetragen wird. Alle Status sind am 2026-09-02
im Speicher gemessen.

| § | Anker in `docs/POST_V2_WISHLIST.md` | einzutragender Satz |
|---|---|---|
| 1b | `### 1b. Claude Design — nicht einbetten, aber anschlussfähig bleiben (2026-07-27)` (Z. 65) | `**Erledigt:** → FR-0045 (MERGED) — in der ersten Strom-Generation geliefert (DEC-0060, TSK-0100).` |
| 1c | `### 1c. Was als ANLEITUNG eingebaut wurde — und welche Gates dabei bewusst nicht entstanden (2026-08-03)` (Z. 86) | `**Item:** → (dünnes FR anlegen) — die mechanisch prüfbaren Hälften C1/C2/C3 und B2/B3; der Abschnitt sagt selbst „NICHT gebaut".` |
| 1 + 1a | `## 1. Skills der Rollen gegen anerkannte Standards härten` (Z. 7) / `### 1a. Führung und Rangfolge — vom User nachgereicht (2026-07-27)` (Z. 36) | `**Item:** → (dünnes FR anlegen) — ein Gate auf genau EIN primäres Ziel je View, plus die SKILL-Zeile mit Verfahren statt Adjektiv.` |
| 2 | `## 2. Board- und Backlog-Ansichten` (Z. 191) | `**Item:** → FR-0024 (TRIAGED) — deckt diesen Abschnitt und sagt es selbst; geliefert dagegen: FR-0030, FR-0053 (beide MERGED), offen daneben FR-0017 (TRIAGED). Rest ohne Item: Termine als eigener Vorgangstyp (MST).` |
| 3 | `## 3. Der Plan als Bild, nicht nur als Text` (Z. 221) | „**Item:** → (dünnes FR anlegen) — Plan und Mindmap als generiertes .drawio.svg; das Format ist für WFR/ARC bereits in Gebrauch, das FR erweitert es." |
| 4 | `## 4. Effort-Stufen pro Rolle statt pro Modell (2026-07-31, User)` (Z. 276) | „**Item:** → FR-0047 (TRIAGED); **Soll-Zustand entschieden in** → DEC-0034 (VALID, bewusst nicht gebaut), Besetzungsschicht → DEC-0059 (VALID). Der gebaute Stand (model_tiers.yaml) und DEC-0034 weichen absichtlich voneinander ab." |
| 5 | `## 5. Finanz-Vorlagen für das Office-Kit (2026-07-31, User)` (Z. 308) | `**Item:** → FR-0032 (TRIAGED) für die ANSICHT (Finanz-Dashboard). Rest ohne Item: Kontenrahmen SKR03/SKR04 + Konto→EÜR-Abbildung, jahresversioniert und mit benanntem Rechtsraum (FR-0002, TRIAGED, deckt Ablage/Aufbewahrung, nicht den Kontenrahmen).` |
| 6 | `## 6. Mehrere Spezialisten derselben Rolle parallel (2026-07-31, User)` (Z. 343) | `**Item:** → FR-0021 (TRIAGED) — nennt diesen Abschnitt selbst.` |
| 7 | Überschrift „## 7. Ein dritter Evidence-Ausgang: blocked (2026-08-01, aus der Paritätsmatrix Zeile 99)" (Z. 361) | „**Item:** → (dünnes FR anlegen) — EVIDENCE_RESULTS += blocked, gate_git schliesst darauf wie auf fail, und der Ehrlichkeitssatz wird mitgebaut. Nachbar, nicht dasselbe: FR-0040 (TRIAGED)." |
| 8 | `## 8. Ein Projekt vollautonom von Anfang bis Ende (2026-08-03, User)` (Z. 386) | `**Item:** → FR-0074 (TRIAGED); **entschieden in** → DEC-0058 (VALID).` |
| 9 | `## 9. Der Masterplan braucht einen Zustand (2026-08-03, User)` (Z. 449) | `**Teilweise erledigt:** die scope-Freigabe bei offenen Planfragen → DEC-0058 (VALID) / FR-0074 (TRIAGED). **Offen bleibt die andere Hälfte:** der Masterplan hat nach der Installation keinen Schreiber — das ist L1 dieser Liste und wird dort geführt.` |
| 10 | `## 10. Die Freigabe programmatisch erteilen — und was das verschiebt (2026-08-03)` (Z. 492) | „**Item:** → (dünnes FR anlegen) — Freigabe über das Agent SDK (canUseTool), und ein programmatisch geprägter Token muss von einem menschlich geprägten unterscheidbar bleiben. Die headless-unerreichbar-Prämisse ist seit TSK-0097 widerlegt (H80)." |

Die sieben Zeilen mit „(dünnes FR anlegen)" bekommen ihre Nummer erst, wenn der Lead das Item
schreibt; dieser Strom schreibt keine Items.
