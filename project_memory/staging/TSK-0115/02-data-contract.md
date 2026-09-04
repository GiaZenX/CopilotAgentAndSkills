# 02 — Datenvertrag: woher jede Zahl kommt, und dass keine neu ist

Alles, was die Seite zeigt, kommt aus dem, was der Kernel heute schon schreibt oder liest. **Kein
neuer Schreiber, kein neues Feld.** Die eine Quelle, die die Tafel heute noch nicht liest, ist
`approvals/pending/` — und die liest der Sitzungsbrief seit FR-0030 mit genau der Regel, die hier
übernommen wird.

| Größe auf der Seite | Quelle | Regel, mit Ort |
|---|---|---|
| Karten, Spalten, Sektionen | `entries` = (Index-Zeile, Item-Body), wie `state._regenerate_index_locked` sie baut und `board.render` sie bekommt | unverändert |
| Spaltenreihenfolge | `board.status_columns(type)` | Kette, dann Seitenzustände, dann Endzustände — unverändert |
| **Bahn** eines Items (new / in flight / done / record) | `AUTOMATA[type]` | `status == initial` → new; `status in terminals` → done (noch in `active/`); sonst registrierter Zustand → in flight; Typ ohne Automat → record. Prototyp `make_mockups.lane`. Auf dem echten Zustand: record 144, in flight 77, new 63, done 0 |
| **blocked** | `row["blocked_by"]` (steht in der Index-Zeile, `_regenerate_index_locked` schreibt es) | jede Zeile mit dem Feld; der Wert wird als Id(s) genannt. Echt heute: 0 |
| **waiting on you** | `approvals/pending/*.yaml`, Felder `request_id`, `kind`, `item`, `expires_at_epoch` | `report.generate_session_brief`: eine Anfrage nach `expires_at_epoch` kann nie mehr prägen und gilt nicht als offen. Karte = das Item, das `item` nennt; eine Anfrage ohne Item (`push`, `preset` …) zählt in der Zahl und steht in der Liste ohne Karte. Echt heute: 1 (BUG-0083, scope, bis 2026-09-04 04:06) |
| **in flight** | Bahn `flight` über alle Typen mit Automat | `READY` einer TSK zählt mit (nicht initial, nicht terminal) — Frage 3 in `user-feedback.md` |
| finished, not yet archived | Bahn `done` | derselbe Befund, den `report.validate_state` als „terminal item awaiting archive" warnt |
| Titel einer Karte | `row["title"]`, sonst `body["title"]` (`board._face_title`) | für `TSK` ohne Titel: `type` + `derives_from`/`product_requirement` + `assigned_role` — alle drei sind Pflichtfelder des TSK-Vertrags (`REQUIRED_FIELDS["TSK"]`) |
| Reiterzahlen, Unassigned, Warnungen | `backlog_tree.arrange`, `board._section` | unverändert |
| archived, not on this board | `board.archived_counts(state)` | unverändert (Id des Typs unter `archive/<TYPE>/<year>/`) |
| Projektname | `project_config.yaml` → `project.name` | leer → „Project without a name"; in diesem Repo ist er leer |
| Stand | `generated/index.yaml` → `generated_at` | eine Uhr für Index und Board |
| Timeline (FR-0079, Option TYP) | `MST`-Zeilen: `due`, `derives_from`, `status`; darunter `backlog_tree.arrange(system)` | Position = `(due − from) / (to − from)`; „late" = `due < today` und Bahn ≠ done; Zahlen je Bahn über die Nachkommen der genannten Wurzeln im Systembaum — **kein** Prozentsatz (Archiviertes fehlt) |

## Was der Prototyp NICHT liest, benannt

- `generated/session_brief.yaml` — dieselben Zahlen, aber mit eigenem Auslöser (`generate-session-brief`
  beim Sitzungsstart); die Tafel liest die Quellen, nicht den Bericht, sonst wäre ihr Stand ein anderer als
  der des Index daneben.
- `dispatch`-Leases — „in flight" ist ein Automatenzustand, keine Lease; eine Lease, die nichts durchsetzt,
  gibt es in diesem Repo nicht (CLAUDE.md), und die Kits zeigen sie über den Status `LEASED` ohnehin.
- `approvals/consumed/`, `revoked/` — Geschichte, keine offene Frage.
- Item-Felder außer den genannten — sie erscheinen in der Akte (`board._fields`), nicht auf der Fläche.

## Die Parität der beiden heutigen Renderer (die Messung, die das FR verlangt)

Vollständig in `parity.md`. Kurz: `kernel/board.py` und `scripts/generate_dashboard.py` gegen dieselbe
Kopie dieses Repos gefahren — **alle Summen gleich** (126 / 6 / 8 / 144 je Dashboard-Ansicht,
Archiv 166, aktive 284). Sie weichen ab in (1) der Schreibweise eines fehlenden Status (`(no status)` gegen
`""`), (2) dem Zeitstempel (zwei Uhren, zwei Auslöser), und (3) der **Archivzählung unter Störung**: das
Dashboard zählt jede `.yaml` unter `archive/<T>/<Jahr>/`, der Kernel nur eine, deren Dateiname als Id
dieses Typs parst — eine `notes.yaml` und eine `BUG-0999.yaml` unter `archive/TSK/2026/` machten
166 gegen 167 gegen 168.
