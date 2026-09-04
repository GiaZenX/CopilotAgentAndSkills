# Parität: stimmen `kernel/board.py` und `generate_dashboard.py` bei denselben Zahlen überein?

Die Messung, die FR-0075 verlangt, **ausgeführt, nicht gelesen**: `parity.py` (beiliegend) baut aus
einer Kopie von `project_memory/` dieses Repos ein Projekt, in dem beide Erzeuger laufen können
(`rig.py`: Hook-Brücke `_kernel.py` samt Import-Hülle über `conftest.sibling_import_closure`,
`scripts/generate_dashboard.py` + Vorlage + `kit_checks.py` aus dem Worktree), fährt
`ProjectState.generate_index()` (schreibt Index **und** Board, eine Uhr) und danach den
Dashboard-Generator als Prozess, und liest beide Seiten so, wie sie gelesen werden: das Board als DOM
(`data-items`, `data-count`, Reiterzahlen, `data-archived`), das Dashboard über den JSON-Block, den sein
Seitenskript liest. Danach drei Störungen am Archiv, kumulativ. Lauf 2026-09-03 07:34, Code
`g3-board` @ e45c0ca, Kopie mit 284 aktiven Items.

## Ergebnis auf dem unveränderten Zustand

| Größe | kernel/board.py | generate_dashboard.py | gleich? |
|---|---|---|---|
| Summe Ansicht `Product` (PR+RQ+FR+CR+BUG) | 126 | 126 | ja |
| Summe Ansicht `Delivery` (TSK+PROC+HYP+EXP, ohne terminale) | 6 | 6 | ja |
| Summe Ansicht `System` (SR+INV+ARC+WFR+DSN) | 8 | 8 | ja |
| Summe Ansicht `Decisions` (DEC+APR+EVD) | 144 | 144 | ja |
| Status je Item (114 Items, die das Dashboard trägt — es kappt bei 50 je Ansicht) | `(no status)` | `""` | **nein**, bei den 4 `APR`: dieselbe Tatsache, zwei Schreibweisen |
| Items mit `blocked_by` | kein Merkmal auf der Karte (`board._card` schreibt keins) | 0 im Payload, Pill `blocked` wäre da | Board zeigt es nur im Feldkatalog der Akte |
| Archiv gesamt | 166 | 166 | ja |
| Archiv je Typ | BUG 2, DEC 1, FR 49, SR 1, TSK 113 | dieselben | ja |
| Aktive Items gesamt | Reiter 284, Sektionen 284 | Summe der Ansichten 284 | ja |
| Zeitstempel | 2026-09-03T07:34:04 (eine Uhr für Index+Board) | 2026-09-03T07:34:05 (eigene Uhr) | **nein** — zwei Auslöser |

## Unter Störung (kumulativ)

| Störung | Board Archiv gesamt / TSK | Dashboard Archiv gesamt / TSK |
|---|---|---|
| `archive/staging/2026/TSK-0999/proposal.yaml` (die Form, die `staging.clear_staging(mode="rejected")` schreibt) | 166 / 113 | 166 / 113 — das Dashboard zählt nur zwei Ebenen tief, die Datei liegt auf der dritten |
| `archive/TSK/2026/notes.yaml` (keine Id) | 166 / 113 | **167 / 114** |
| `archive/TSK/2026/BUG-0999.yaml` (fremde Id unter dem falschen Typ) | 166 / 113 | **168 / 115** |

Der Kernel parst den Dateistamm als Id **dieses** Typs (`board.archived_counts`); der Generator zählt
jede `.yaml` unter `archive/<T>/<Jahr>/` (`generate_dashboard.archive_summary`). Auf einem sauberen
Archiv stimmen sie überein; ein Archiv ist aber ein Verzeichnis, das niemand bewacht (so steht es im
Docstring von `archived_counts`), und dort laufen sie auseinander.

## Lesung und Empfehlung: **ein Renderer, zwei Ausgaben — und die zweite trägt keine Zahl der ersten**

1. Die Zahlen, die beide ausdrücken, stimmen heute überein, weil beide denselben Index lesen; sie
   **können** auseinanderlaufen, wo einer eine eigene Regel hat (Archiv), und sie **tun** es beim
   Zeitstempel, weil das Dashboard keinen Auslöser hat (Hand-Schritt der Checkliste,
   `dev-team/constitution/AGENTS.md` §2.3 und Phase 8) und das Board bei jedem Zustandsschreiben entsteht.
2. Das Dashboard hat genau **eine** Größe, die das Board nicht hat und nicht haben kann: die Repo-Vitalwerte
   (`compute_repo_vitals`, aus `kit_checks.source_files` — das ist Dev-Kit-Wissen über den Quellbaum, nicht
   Zustandswissen). Alles andere ist eine zweite Darstellung derselben Items mit einer schwächeren Ableitung
   (`VIEWS`-Kuration, Kappung bei 50, keine Bäume, keine Akte).
3. Empfehlung für Phase 2: **`kernel/board.py` ist der eine Renderer der Items** (neue Gestaltung, alle Kits,
   auto-frisch). **`scripts/generate_dashboard.py` bleibt der Erzeuger von `generated/dashboard.html`**,
   rendert aber **keine Items mehr**: die Seite trägt die Vitalwerte und einen Verweis auf `board.html`
   (relativer Link im selben Verzeichnis). Dann gibt es keine Zahl, in der die beiden abweichen können, weil
   nur einer sie hat; der Befehl der Checkliste bleibt gültig (kein D-Seam), die Datei bleibt die eine, die
   „einen eigenen Erzeuger hat" (Verfassung §2.3, wörtlich weiter wahr), Kit-Eigentum und Ein-Datei-Eigenschaft
   bleiben (FR-0030). Kosten: die Dashboard-Tests in `tools/test_hooks.py` (`_dashboard_data`, `views`,
   `archive`) werden zu Tests über Vitalwerte und Verweis umgeschrieben — `tools/**` ist in unserem Scope, die
   Datei ist mit Strom B geteilt (Seam-Tabelle).
4. Verworfene Alternative, in einer Zeile: das Dashboard bettet das vom Kernel gerenderte Board-Fragment ein
   (ein Renderer, wörtlich zwei Ausgaben) — verworfen, weil dann zwei Dateien mit zwei Uhren dieselbe Tafel
   zeigen und die ältere immer die ist, die jemand offen hat.
5. Zweite verworfene Alternative: zwei Renderer behalten und die Archivregel angleichen — verworfen, weil die
   Angleichung die dritte Kopie einer Regel wäre und der Zeitstempel trotzdem auseinanderliefe.

Rohausgabe des Laufs: `parity-result.md` (beiliegend), erzeugte Seiten `board-current.html` und
`dashboard-current.html` im Scratch unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0115\`.
