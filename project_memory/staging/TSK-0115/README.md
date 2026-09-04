# TSK-0115 — Design-Paket Backlog-Board, Meilensteine, Plan-Diagramme (Phase 1 von 2, Fable)

Strom A „Board & Plan", Generation 3 (DEC-0062), FR-0075 primär, gebündelt mit FR-0079 und FR-0080.
Phase 1 schreibt **nur** in dieses Verzeichnis und in `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0115\`;
der Worktree `g3-board` ist unberührt (Lese-Kopie des Codes, Stand e45c0ca). Kein Kit-File wurde
angefasst, kein Stempel, kein Commit.

## Inhalt

| Datei | Was |
|---|---|
| `01-information-architecture.md` | wer liest, was zuerst; der heutige Stand in Zahlen; die Seite von oben; die drei Zustände |
| `02-data-contract.md` | jede Zahl mit Quelle und Regel; was nicht gelesen wird; Kurzfassung der Parität |
| `03-tokens.md` | Richtung „Plantafel", Signatur T-Kartenkopf, Token mit Rolle und Grund, Verworfenes |
| `04-build-spec.md` | Dateien, der eine Renderer, Renderer Stück für Stück, Tests (rot ohne Fix, je FR), Lochkandidaten H126–H128, Seams, Suiten |
| `05-diagrams.md` | FR-0080: welche Sicht Plan, welche Mindmap, Quelle, Auslöser-Seam, Handänderung erkannt (gemessen), Ablagefrage |
| `mst-decision-proposal.md` | FR-0079: Typ oder Feld, Kernel-Folgen je Zeile mit Test, Empfehlung |
| `parity.md`, `parity-result.md` | die Messung Board gegen Dashboard, mit Störungen; Empfehlung ein Renderer / zwei Ausgaben |
| `user-feedback.md` | sieben Fragen an den Nutzer |
| `make_mockups.py` | Prototyp des Renderers: liest eine Kopie von `project_memory/` wie der Kernel, baut auf `board`/`backlog_tree` auf; `--milestones` simuliert den MST-Seam zur Laufzeit |
| `make_diagrams.py` | Prototyp `plan_diagram`: Plan + Mindmap als `.drawio.svg`, Digest, `is_pristine` mit den drei Urteilen |
| `fixtures.py`, `rig.py`, `parity.py`, `stats.py`, `measure_wellformed.py` | Fixtures (empty/healthy/blocked), das Rig für beide Erzeuger, die Paritätsmessung, die Zählung des echten Zustands, die Wohlgeformtheitsmessung |
| `milestones.yaml` | vier erfundene `MST` über echten Wurzeln, für `mockup-timeline.html` |
| `mockup-empty.html`, `mockup-healthy.html`, `mockup-blocked.html`, `mockup-timeline.html` | die Zustände, aus einem Prototyp |
| `render_mockups.py`, `render_diagrams.py` | Sicht-Schleife: Playwright, 1280 und 390 px, jeder Reiter, dunkel bei 1280, drei Fokus-Zustände, Akte offen, Records offen; Diagramme als PNG |
| `review/*.png`, `review/render.json` | 69 Board-Bilder + 3 Diagramm-Bilder, an die SHA-256 der gerenderten HTML gebunden; `errors: []` bei allen vier Entwürfen |
| `diagrams/*.drawio.svg` | Plan, Mindmap, und die von Hand geänderte Kopie, an der die Erkennung gemessen ist |

## Sichtprotokoll (BUG-0076: nichts steht hier, was niemand gerendert hat)

Fünf Render-Durchgänge, jeder mit Befund und Korrektur:

1. **Durchgang 1** (9 Bilder gesichtet): Streifen, T-Karten, Slots, dunkel, Akte, Bäume, Records — trägt.
   Befunde: **die Seite war deutsch beschriftet, und DEC-0049 (Nutzerentscheid 2026-08-22) hält die
   Board-Seite englisch** — auf der Records-Liste stand die Entscheidung selbst im Bild; gedreht.
   Der Fokus „in flight" blendete alles ab (kein Bahn-Merkmal auf den Karten). Der Fokus „blocked" auf der
   vollen Tafel zeigte die Zahl 3 und keine der drei Karten im Bildschirm — daraus die Fokus-Listen unter dem
   Streifen. Leere Endzustände als Slots; Records mit `(no status)`-Kopf; TSK-Zeile lief rechts an.
2. **Durchgang 2**: Fokus-Listen tragen (3 blockierte mit Blocker, die Anfrage auf BUG-0083, 77 in Arbeit
   zweispaltig); 390 px trägt; leer trägt. Befunde: Sektionstitel klein geschrieben
   (`backlog_tree._LABELS`), Status-Badge in der Liste ohne Rahmen, Zeile „no cards in" nannte auch
   gezeichnete Slots.
3. **Durchgang 3**: Titel, Badge, Zeile korrigiert; Timeline erstmals: zwei Marken einen Tag auseinander
   (MST-0003, MST-0001) überschrieben sich. Diagramme: Blätter der Mindmap trugen die Bahn nur als Farbe.
4. **Durchgang 4**: Ebenenwechsel eingebaut, aber die Beschriftung blieb unten verankert — weiter überlappt;
   SVG-Screenshot hing als Top-Level-Dokument (30 s), dann als `<img>` aus `about:blank` nicht geladen.
5. **Durchgang 5**: Beschriftung oben verankert, Wrapper-HTML neben dem SVG — beides gesichtet und sauber.
   Rest, benannt: die Heute-Marke nimmt am Ebenenwechsel nicht teil und kann eine hochgesetzte Beschriftung
   berühren (`review/timeline-timeline-1280.png`).

## Messungen, die das Paket tragen

| Messung | Ergebnis |
|---|---|
| Parität `kernel/board.py` gegen `generate_dashboard.py` (`parity.py`, beide gegen dieselbe Kopie, 284 Items) | alle Summen gleich (126/6/8/144, Archiv 166, aktiv 284); Abweichungen: `(no status)` gegen `""`, Zeitstempel 07:34:04 gegen 07:34:05 (zwei Auslöser), Archiv unter Störung 166 gegen 167 gegen 168 |
| Heutiges Board dieser Kopie (`board-current.html`) | 14 Sektionen alphabetisch (`APR` zuerst), 32 leere gegen 13 belegte Spalten, alle 6 TSK-Karten ohne Titel, kein Blockiert-Merkmal auf der Fläche |
| Echter Zustand (`stats.py`) | Bahnen: record 144, in flight 77, new 63, done 0; `blocked_by`: 0 Zeilen; offene Anfragen: 1 (BUG-0083, scope, bis 2026-09-04 04:06); Archiv 166 |
| Render (`render.json`) | 4 Entwürfe, 69 Bilder, `errors: []` überall; SHA-256 je Entwurf im Record |
| Diagramme (`make_diagrams.py`) | Plan 34 SVG-Elemente / 21 Zellen, Mindmap 42 / 29; zwei Läufe gleiche Bytes; Urteile `pristine` / `hand-edited` / `stale` je hergestellt und getroffen |
| Wohlgeformtheit (`measure_wellformed.py`, `staging._assert_xml_wellformed`) | besteht für die drei erzeugten Dateien und für die Pilot-Datei `ARC-0001.drawio.svg` — die kein `content`-Attribut trägt |
| Determinismus des Prototyps (`determinism.py` im Scratch: jeder Zustand zweimal erzeugt) | alle vier Mockups Byte für Byte gleich; die SHA-256 in `review/render.json` sind die der beiliegenden Dateien |
| `ruff check` über alle beiliegenden Skripte | sauber (nach drei Befunden: ungenutzte Variable, ungenutzter Import) |
| Seiten-Anfragen | keine Messung in dieser Phase (kein `page.on("request")`-Lauf); die Seite lädt keine Schrift und kein Skript von außen (Systemschriften, Inline-Skript) — Phase 2 misst es wie TSK-0079 |

## Was frontend-design an den Entscheidungen geändert hat

- **Erster Entwurf wäre die Kachelwand gewesen** — sie ist `progress.dashboard.template.html`. Ersetzt durch
  drei Zahlen auf einer Linie und eine Tafel aus Slots und T-Karten, deren Kopf die einzige Farbe trägt.
- **Farbe nur, wo sie eine Handlung des Lesers bedeutet**: rot = hängt, blau = du. Kein Grün, keine Ampel je
  Status, kein Verlauf.
- **Die Schrift aus dem Gegenstand**: die schmale Etikettenschrift der T-Karte in den Köpfen, Festbreite für
  alles, was man abtippt, sonst Systemschrift.
- Die Selbstprüfung gegen die drei KI-Standardlooks steht in `03-tokens.md` unter „Verworfen".

Was der Skill NICHT geändert hat: die Inhalte. Zahlen, Bahnen, Spalten und Bäume kommen aus FR-0075,
`AUTOMATA`, `backlog_tree` und den Item-Feldern, nicht aus der Gestaltung.

## Der verworfene Alternativ-Brief (FR-0084-Form)

Ein Brief **für den PM-Agenten als Leser** — dicht, jedes Feld, jeder Typ gleich, Kernel-Vokabular
vorn — verworfen, weil der PM den Sitzungsbrief liest und nicht die HTML; der einzige menschliche Leser der
Tafel ist der Inhaber, und der fragt zuerst, ob er etwas tun muss.

## Offene Fragen an den Lead

1. **Die Fragen 1–7 aus `user-feedback.md`** — vor allem 4 (FR-0079 Typ/Feld: das DEC) und 5 (Ablage der
   Diagramme). Ohne 4 baut Phase 2 die Timeline aus einer Fixture nach Option A und die Feld-Variante nicht.
2. **Empfehlung Renderer** (`parity.md`): ein Renderer, das Dashboard trägt keine Items mehr. Wenn der Lead
   das anders will, ändert sich `04-build-spec.md` §1 und der Dashboard-Abschnitt in `tools/test_hooks.py`
   bleibt, wie er ist.
3. **Seam-Reihenfolge**: die C-Zeilen (`state._write_board`, `cli.py`, `approvals.open_requests`,
   ggf. `backlog_types` für MST) stehen in `04-build-spec.md` §7 und `05-diagrams.md`; ob C sie in der
   Runde oder der Merge übernimmt, ist die Frage des Lead.

## Was bewusst nicht geschlossen, aber benannt ist

- Kein Kit-File geändert, kein Test im Repo, kein Auslöser für die Diagramme — Phase 2 und C-Seam.
- Der echte Zustand hat **keine** blockierte Zeile; der Zustand „blockiert" ist die volle Kopie plus drei
  gesetzte `blocked_by` (`fixtures.BLOCKED_OVERLAY`), die offene Anfrage ist echt. Die gesunde Teilmenge trägt
  bearbeitete Status und Bindungen (`fixtures.HEALTHY_EDITS`), damit die Bäume sie platzieren.
- `READY` zählt als „in flight" (Frage 3).
- Die Diagramme haben kein Größenbudget und kappen Texte bei 58 Zeichen; die Wurzelzelle des Plans trägt
  ihre Bahn nicht.
- Keine `page.on("request")`-Messung in dieser Phase.
- Die Heute-Marke der Timeline kann eine hochgesetzte Beschriftung berühren.
- Die Prototypen fahren gegen den Worktree-Pfad (`HARNESS_KERNEL_PATH` sonst); sie sind Vorbild, nicht Kit-Code.

## Phase 1b — drei Richtungen zur Wahl (DEC-0064, DEC-0065)

Der Nutzer hat entschieden: `DEC-0064` Meilenstein = eigener Typ; `DEC-0065` ein Renderer mit zwei
Ausgaben, Diagramme in `generated/`, Records zugeklappt, drei Zahlen, `READY` zählt als in flight,
Englisch — **und** die visuelle Sprache neu, weil das Phase-1-Blatt der Finanzseite zu nahe war (die
sieben Token, die gleich waren, stehen in `06-directions.md`). Unverändert: `01`, `02`, Rig, Fixtures,
Messungen. Neu:

| Datei | Was |
|---|---|
| `06-directions.md` | die drei Richtungen mit Bildpfaden oben, Abstandsmessung zu TSK-0109, je Charakter, Vorbild, Kosten (390, dunkel, Kontrast gemessen), verworfener Brief; Sichtprotokoll 1b; Empfehlung |
| `03-tokens-a.md`, `03-tokens-b.md`, `03-tokens-c.md` | ein Token-Blatt je Richtung — das gewählte wird das Blatt von Phase 2; `03-tokens.md` (Phase 1) bleibt als Vergleich liegen |
| `directions.py` | die drei Blätter als Code über demselben Markup (`make_mockups.py --style a\|b\|c`) |
| `direction-a.html`, `-b.html`, `-c.html` | der Zustand „blockiert" in jeder Richtung |
| `contrast.py`, `contrast-result.md` | WCAG-Kontraste aller Text/Grund-Paare je Richtung, hell und dunkel, aus denselben Token-Strings gelesen |
| `render_directions.py`, `review/directions/` | 27 Bilder (1280/390 × hell/dunkel, Fokus blockiert / wartet auf dich hell und dunkel, Akte), `render.json` mit `errors: []` bei allen dreien |

## Phase 1c — zwei moderne Fassungen (Rückmeldung des Nutzers zu A/B/C)

Der Nutzer: C's starke Farbe gefällt, alles wirkt retro, er will es modern. Neu: `07-modern.md`
(Bildpfade oben, die drei Sätze zur Grenze modern / KI-Standard, Abstandsmessung, D und E mit Charakter,
Kosten, verworfenem Brief, Sichtprotokoll, Empfehlung), `03-tokens-d.md`, `03-tokens-e.md`,
`direction-d.html`, `direction-e.html`, `review/directions/d-*.png`, `e-*.png` (je 9), `directions.py`
und `contrast.py` erweitert, `contrast-result.md` aktualisiert. A/B/C bleiben als Vergleich liegen.

## Phase 1d — E übernommen, vier Mängel behoben

Der Nutzer übernimmt E und nennt: volle Breite, Karten überlappen, Hierarchie einklappen, Zeitleiste
fehlt. Neu: `08-final.md` (Bildpfade oben, vier Behebungen mit Messung vorher/nachher — Bounding-Boxes
aus `measure_layout.py`, `layout-before.md`/`layout-after.md`), `03-tokens-final.md` (= E +
Layoutregeln; **das Blatt für Phase 2**), `04-build-spec.md` §0 und die 1d-Tests in §5, die vier Endseiten
`final-*.html`, `review/final/` (101 Bilder über leer/gesund/blockiert/Zeitleiste × 1280/1920/390 ×
hell/dunkel, Fokus, Akte, Records, Baum Standard/auf/zu/Tastatur; `render.json` mit `errors: []`),
`render_final.py`, `make_mockups.py` und `directions.py` erweitert (Falten, fließende Slots, drei
Lineal-Bänder). Ursache der Überlappung: `all: unset` setzt `box-sizing` zurück — 26 px zu breite Karten,
gemessen 110 Paare bei 1280/1920; nachher 0.

## Wall-Clock und Modell

Beginn 2026-09-03 07:22 (erste Lesung des Items), Paket vollständig in Staging 08:10 (`publish.py`,
`date`). Davon Lesen und Ableiten ~13 min (bis 07:35), Rig und Paritätsmessung ~5 min (Lauf 07:34), Prototyp,
Fixtures und fünf Sicht-Fix-Schleifen ~22 min (Renders 07:39–07:58), Diagramme darin ~5 min, Dokumente
und Veröffentlichung ~12 min. Modell: Fable (DEC-0063 (3): Design-Pass-Stufe).

Phase 1b: Auftrag gelesen 08:24 (DEC-0064/0065), drei Richtungen gebaut, dreimal gesichtet und korrigiert,
veröffentlicht 08:34 (`publish2.py`, `date`) — ~11 min plus Bericht. Modell: Fable.

Phase 1c: Auftrag gelesen ~08:50, D und E gebaut, dreimal gesichtet und zweimal korrigiert, veröffentlicht
09:04 (`publish2.py`, `date`) — ~14 min plus Bericht. Modell: Fable.

Phase 1d: Auftrag gelesen ~09:40, Messrig für Überlappung/Breite gebaut und vorher gemessen (09:45),
vier Behebungen, zwei Sichtrunden, 101 Bilder gerendert, veröffentlicht 09:53 (`publish3.py`, `date`),
Dokumente bis 09:56 (`date`) — ~16 min plus Bericht. Modell: Fable.
