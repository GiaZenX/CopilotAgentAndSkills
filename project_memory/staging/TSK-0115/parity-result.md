# Parität kernel/board.py gegen generate_dashboard.py

Beide gegen dieselbe Kopie von `project_memory/` des Hauptrepos (Stand der Kopie: C:/Offline Repos/AgentAndSkills), Code aus dem Worktree g3-board.

Dashboard-stdout: `Dashboard generated: C:\Offline Repos\v2-testbed\_round-scratch\TSK-0115\rig\project_memory\generated\dashboard.html (284 active item(s) in 4 view(s), 114 rendered, 0 finished hidden, 166 archived)`
Board-Reiter: {'board': 284, 'product': 38, 'system': 105}; Archiv-Text: `archived, not on this board: 166 (BUG 2, DEC 1, FR 49, SR 1, TSK 113)`
Board-Sektionen (data-items): {'APR': 4, 'ARC': 0, 'BUG': 88, 'CR': 0, 'DEC': 61, 'DSN': 0, 'EVD': 79, 'FR': 35, 'INV': 0, 'PR': 3, 'PROC': 0, 'SR': 8, 'TSK': 6, 'WFR': 0}
Board-Warnungen: 6

### Unverändertes Archiv

| Größe | kernel/board.py | generate_dashboard.py | gleich? |
|---|---|---|---|
| Summe Ansicht `Product` (PR+RQ+FR+CR+BUG) | 126 | 126 | ja |
| Summe Ansicht `Delivery` (TSK+PROC+HYP+EXP, ohne terminale) | 6 | 6 | ja |
| Summe Ansicht `System` (SR+INV+ARC+WFR+DSN) | 8 | 8 | ja |
| Summe Ansicht `Decisions` (DEC+APR+EVD) | 144 | 144 | ja |
| Status je Item (114 Items, die das Dashboard trägt) | — | — | **NEIN** [('APR-0001', '(no status)', ''), ('APR-0002', '(no status)', ''), ('APR-0003', '(no status)', ''), ('APR-0004', '(no status)', '')] |
| Items mit `blocked_by` (Dashboard-Payload) | kein Merkmal auf der Karte (Klasse `card` trägt keins) | 0 [] | Board zeigt es nur im Detail-Feldkatalog |
| Archiv gesamt | 166 | 166 | ja |
| Archiv je Typ | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | ja |
| Aktive Items gesamt | Board-Reiter 284 (Sektionen 284) | Summe der Ansichten 284 (Delivery ohne terminale) | ja |
| Zeitstempel | 2026-09-03T07:34:04 (einer für Index+Board) | 2026-09-03T07:34:05 (eigene Uhr beim Lauf) | **NEIN** (zwei Auslöser) |

### Störung: archive/staging (kumulativ)

| Größe | kernel/board.py | generate_dashboard.py | gleich? |
|---|---|---|---|
| Summe Ansicht `Product` (PR+RQ+FR+CR+BUG) | 126 | 126 | ja |
| Summe Ansicht `Delivery` (TSK+PROC+HYP+EXP, ohne terminale) | 6 | 6 | ja |
| Summe Ansicht `System` (SR+INV+ARC+WFR+DSN) | 8 | 8 | ja |
| Summe Ansicht `Decisions` (DEC+APR+EVD) | 144 | 144 | ja |
| Status je Item (114 Items, die das Dashboard trägt) | — | — | **NEIN** [('APR-0001', '(no status)', ''), ('APR-0002', '(no status)', ''), ('APR-0003', '(no status)', ''), ('APR-0004', '(no status)', '')] |
| Items mit `blocked_by` (Dashboard-Payload) | kein Merkmal auf der Karte (Klasse `card` trägt keins) | 0 [] | Board zeigt es nur im Detail-Feldkatalog |
| Archiv gesamt | 166 | 166 | ja |
| Archiv je Typ | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | ja |
| Aktive Items gesamt | Board-Reiter 284 (Sektionen 284) | Summe der Ansichten 284 (Delivery ohne terminale) | ja |
| Zeitstempel | 2026-09-03T07:34:05 (einer für Index+Board) | 2026-09-03T07:34:06 (eigene Uhr beim Lauf) | **NEIN** (zwei Auslöser) |

### Störung: non-id yaml under TSK (kumulativ)

| Größe | kernel/board.py | generate_dashboard.py | gleich? |
|---|---|---|---|
| Summe Ansicht `Product` (PR+RQ+FR+CR+BUG) | 126 | 126 | ja |
| Summe Ansicht `Delivery` (TSK+PROC+HYP+EXP, ohne terminale) | 6 | 6 | ja |
| Summe Ansicht `System` (SR+INV+ARC+WFR+DSN) | 8 | 8 | ja |
| Summe Ansicht `Decisions` (DEC+APR+EVD) | 144 | 144 | ja |
| Status je Item (114 Items, die das Dashboard trägt) | — | — | **NEIN** [('APR-0001', '(no status)', ''), ('APR-0002', '(no status)', ''), ('APR-0003', '(no status)', ''), ('APR-0004', '(no status)', '')] |
| Items mit `blocked_by` (Dashboard-Payload) | kein Merkmal auf der Karte (Klasse `card` trägt keins) | 0 [] | Board zeigt es nur im Detail-Feldkatalog |
| Archiv gesamt | 166 | 167 | **NEIN** |
| Archiv je Typ | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 114} | **NEIN** |
| Aktive Items gesamt | Board-Reiter 284 (Sektionen 284) | Summe der Ansichten 284 (Delivery ohne terminale) | ja |
| Zeitstempel | 2026-09-03T07:34:06 (einer für Index+Board) | 2026-09-03T07:34:07 (eigene Uhr beim Lauf) | **NEIN** (zwei Auslöser) |

### Störung: BUG id under archive/TSK (kumulativ)

| Größe | kernel/board.py | generate_dashboard.py | gleich? |
|---|---|---|---|
| Summe Ansicht `Product` (PR+RQ+FR+CR+BUG) | 126 | 126 | ja |
| Summe Ansicht `Delivery` (TSK+PROC+HYP+EXP, ohne terminale) | 6 | 6 | ja |
| Summe Ansicht `System` (SR+INV+ARC+WFR+DSN) | 8 | 8 | ja |
| Summe Ansicht `Decisions` (DEC+APR+EVD) | 144 | 144 | ja |
| Status je Item (114 Items, die das Dashboard trägt) | — | — | **NEIN** [('APR-0001', '(no status)', ''), ('APR-0002', '(no status)', ''), ('APR-0003', '(no status)', ''), ('APR-0004', '(no status)', '')] |
| Items mit `blocked_by` (Dashboard-Payload) | kein Merkmal auf der Karte (Klasse `card` trägt keins) | 0 [] | Board zeigt es nur im Detail-Feldkatalog |
| Archiv gesamt | 166 | 168 | **NEIN** |
| Archiv je Typ | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 113} | {'BUG': 2, 'DEC': 1, 'FR': 49, 'SR': 1, 'TSK': 115} | **NEIN** |
| Aktive Items gesamt | Board-Reiter 284 (Sektionen 284) | Summe der Ansichten 284 (Delivery ohne terminale) | ja |
| Zeitstempel | 2026-09-03T07:34:07 (einer für Index+Board) | 2026-09-03T07:34:08 (eigene Uhr beim Lauf) | **NEIN** (zwei Auslöser) |
