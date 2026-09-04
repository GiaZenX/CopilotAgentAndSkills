# FR-0079 — Termine für die Timeline: eigener Typ `MST` oder ein Feld? (Entscheidungsvorlage)

Die Entscheidung ist deine (FR-0079: „the DEC is the USER decision, captured by the lead before
phase 2 starts"). Hier stehen beide Wege mit dem, was sie im Kernel kosten, gemessen an den Stellen,
die eine Änderung heute berührt — und meine Empfehlung mit Grund. Wie es aussähe, zeigt
`mockup-timeline.html` (Reiter **Timeline** und Sektion **Milestones**; Bilder
`review/timeline-*.png`), gerendert mit vier erfundenen Meilensteinen (`milestones.yaml`) über echten
Wurzeln dieses Repos. Der Prototyp simuliert dafür die Kernel-Zeilen aus Option A zur Laufzeit
(`make_mockups.simulate_mst_type`) — nichts am Kernel ist angefasst.

## Worum es geht, in einem Satz

Ein Meilenstein ist **ein Datum, das für mehrere Dinge gilt** („Release 2026.10 am 15.10., dafür
PR-0002 und PR-0003"), mit eigenem Namen und eigenem Ausgang (erreicht / verfehlt / gestrichen).

## Option A — eigener Typ `MST` (Empfehlung)

Ein Item wie jedes andere: `milestones/active/MST-0001.yaml` mit `title`, `due` (ISO-Datum) und
`derives_from` (die Wurzeln, für die das Datum gilt — dieselbe Bindungsrichtung wie `WFR`/`HYP`/`EXP`,
darum hängt es im Baum automatisch unter seiner Wurzel: `PARENT_FIELDS` wird aus den Feldverträgen
abgeleitet, `backlog_types._parent_fields`). Automat: `PLANNED → REACHED`; Endzustände `REACHED`,
`MISSED`, `DROPPED`, beide letzten nur aus `PLANNED`. Keine Freigabe nötig (kein Eintrag in
`APPROVAL_TRANSITIONS`, damit `required_approval_kinds` leer bleibt — wie bei `TSK` und `SR`).

**Was es im Kernel kostet (Strom C, wörtlich als Seam im Protokoll zu übergeben):**

| Stelle | Zeile(n) | Test, der sie trägt |
|---|---|---|
| `backlog_types.AUTOMATA` | `"MST": _Automaton(chain=("PLANNED", "REACHED"), terminals=("REACHED", "MISSED", "DROPPED"), terminal_from={"MISSED": ("PLANNED",), "DROPPED": ("PLANNED",)})` | `test_backlog_types` — die Konstruktions-Selbstprüfung des Automaten läuft beim Import |
| `backlog_types.ACTIVE_DIRS` | `"MST": "milestones/active"` | `test_hooks.test_no_adhoc_covers_every_item_type` wird **rot**, bis `guard_no_adhoc.ITEM_TYPES` in allen drei Kits `"mst"` trägt (Hooks: nicht unser Scope → C oder Merge) |
| `backlog_types.REQUIRED_FIELDS` | `"MST": ("title", "due", "derives_from")` | `test_schemas` / `test_state` Feldvertrag; ob `due` ein Datum ist, prüft heute **niemand** — Vorschlag: `state.capture_preflight` weist ein `due` ab, das `date.fromisoformat` nicht liest (C), sonst zeigt die Timeline „no date" und sagt es |
| `backlog_types.INVALIDATION_TARGET` | kein Eintrag (kein `approval_ref`) | — |
| `backlog_tree.VIEWS[0].children` | `("FR", "CR", "MST")` — Kundensprache, darum Produkt-Sicht | `test_board.test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view` wird sonst **rot** (der Stolperdraht misst beide Enden) |
| `backlog_tree._LABELS` | `"MST": ("milestone", "milestones")` | — |
| Templates aller drei Kits | `templates/project_memory/milestones/active/.gitkeep` | `test_board.test_each_kit_renders_the_types_its_own_template_ships` |
| Verfassungen (Typtabelle) | eine Zeile je Kit | Strom D |
| `generate_dashboard.VIEWS` | nur, wenn das Dashboard weiter Items rendert (Empfehlung in `parity.md`: nein) | sonst landet `MST` unter „Other" mit Warnung — das ist der gebaute Rückfall |
| Index, Board-Sektion, Spalten, Karte, Bahn, Akte | **nichts** — alles abgeleitet (`ACTIVE_DIRS`-Walk, `status_columns`, `lane`) | gemessen: der Prototyp zeigt die Sektion Milestones ohne eine Zeile Board-Code je Typ |

Gemessene Referenz für diese Kostenart: FR-0017 (`area`) hat genau diese Liste für einen neuen Typ
ausgemessen und sich **dagegen** entschieden — dort ging es um eine reine Gliederung ohne eigenen Zustand
(`backlog_types.py`, Kommentar über `AREA_FIELD`). Ein Meilenstein **hat** einen Zustand (erreicht oder
nicht) und eine Identität, die mehrere Items teilen; das ist der Unterschied.

**Was Phase 2 in unserem Strom baut, wenn A gewählt wird:** die Timeline (Reiter, Lineal, Karten je
Meilenstein, „late", Zahlen je Bahn) in `kernel/board.py`, gerendert **aus einer Fixture** (Entries mit
Typ `MST`, dem Renderer direkt übergeben — so testet `test_board` heute schon Formen, die kein Store
erzeugt), plus die Sektion auf der Tafel, die von selbst entsteht. Die Zeilen oben gehen an C.

## Option B — ein Feld `due` an bestehenden Items

`due` als universelles optionales Feld (`UNIVERSAL_OPTIONAL_FIELDS = (AREA_FIELD, "due")`), ein
Datum je Item. Die Timeline zeigt jedes Item mit `due` als Marke; „late" = `due` vorbei und nicht
terminal.

**Kosten:** eine Tupel-Zeile in `backlog_types` (C), dieselbe Datumsprüfung (C), Timeline in `board.py`
(wir). Kein Verzeichnis, kein Automat, keine Hook-Liste, keine Template-Zeile, keine Verfassungszeile.

**Was fehlt:** (1) ein Termin, der für mehrere Items gilt, steht n-mal — und Items sind praktisch
unveränderlich (Wunschliste L2: jede „korrigiere Feld X"-Abhilfe ist unausführbar), also ist eine
Terminverschiebung n Kernel-Edits mit n Revisionssprüngen; (2) kein Name, kein eigener Ausgang: „Release
2026.10" existiert nirgends als Ding, nur als Datum, das zufällig übereinstimmt; (3) „verfehlt" ist
nicht erfassbar, nur ableitbar — die Wunschliste §2 nennt genau das als Grund, warum V2 die Meilensteine aus
`progress.yaml` abgeschafft hat: doppelt geführt, ohne eigenen Datensatz.

## Empfehlung

**A — der Typ.** Der Preis ist die bekannte Liste (Hook-Tupel dreimal, Template dreimal, Verfassung dreimal,
eine Baumzeile), und jede Zeile davon hat einen Stolperdraht, der rot wird, wenn sie fehlt. Der Preis von B ist
still: ein Datum, das in fünf Items steht, und kein Test, der merkt, wenn eines davon nicht mitgezogen wurde.

Was die Entscheidung **nicht** ändert: die Timeline als Reiter, das Lineal mit Heute-Marke, die
Zahlen je Bahn statt Prozent (Archiviertes liegt nicht auf der Tafel). Was sie ändert: ob eine Marke
ein Meilenstein mit Zielen ist (A) oder ein Item mit Datum (B).

## Offen gelassen, benannt

- Der Bezug **von** einem Item **auf** einen Meilenstein (`TSK` → „gehört zu Release 2026.10") ist in A
  nicht vorgesehen: Zugehörigkeit läuft über die Wurzeln, die der Meilenstein nennt. Ein Feld
  `milestone` an TSK wäre eine zweite Bindungsrichtung, die den Baum umstülpt (`arrange` hängt Kinder
  unter das tiefste genannte Elternteil) — erst, wenn jemand es braucht.
- Zwei Marken einen Tag auseinander: die Beschriftungen wechseln die Ebene (gesichtet, Runde 4→5); die
  Heute-Marke nimmt daran nicht teil und kann eine hochgesetzte Beschriftung berühren
  (`review/timeline-timeline-1280.png`, MST-0001) — Phase 2 lässt die Heute-Marke dieselbe Regel nehmen.
