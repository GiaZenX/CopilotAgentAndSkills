# 01 — Informationsarchitektur: das Board, das zuerst antwortet

Gegenstand: die Backlog-Tafel der Kits, `generated/board.html` (`kernel/board.py`, FR-0030/FR-0053).
Leser: **der Inhaber des Projekts**, der kein Entwickler ist, und zwar in dem Moment, in dem er die
Datei öffnet, um zu wissen, ob er etwas tun muss. Der PM-Agent liest sie **nicht**: seine Sicht ist
`generated/session_brief.yaml` (`report.generate_session_brief`), und die trägt dieselben Zahlen
maschinenlesbar. Daraus folgt die eine Aufgabe der Seite: **Was hängt, was wartet auf mich, was
läuft — beantwortet, bevor gescrollt wird.** Alles andere (Spalten, Bäume, Akten) ist die zweite
Ebene und bleibt, was FR-0030/FR-0053 geliefert haben.

Sprache der Seite: **Englisch**, per Nutzerentscheid `DEC-0049` (2026-08-22). Der erste Entwurf
dieses Passes war deutsch beschriftet und wurde in Sichtrunde 1 gegen die Entscheidung gedreht
(README, Sichtprotokoll). Kernel-Vokabular (Status-Werte, Ids, Typkürzel) bleibt ohnehin unübersetzt.

## Was der heutige Stand tut (gemessen an `board-current.html`, 284 Items, 2026-09-03)

| Befund | Zahl | Folge für den Leser |
|---|---|---|
| Typ-Sektionen, alphabetisch | 14; die erste ist `APR` mit 4 Karten in einer Spalte `(no status)` | Das Erste, was man sieht, ist ein Aktenvermerk |
| Spalten insgesamt | 45, davon **32 leer** und 13 belegt | Die Tafel ist zu 70 % leere Rahmen |
| Karten von `TSK` | 6, **alle ohne Titel** (`TSK` hat kein `title` im Vertrag, `REQUIRED_FIELDS`) | Eine Aufgabe ist nur eine Nummer |
| `EVD`-Karten | 79 in einer Spalte, `DEC` 61 | Belege verdrängen Arbeit |
| Merkmal „blockiert" auf der Kartenfläche | keins (`board._card` schreibt keins; `blocked_by` steht nur im Feldkatalog der Akte) | Die erste Frage des Briefs hat auf der Tafel keine Antwort |
| Merkmal „wartet auf den Nutzer" | keins (die offene Freigabe-Anfrage in `approvals/pending/` liest nur der Sitzungsbrief) | Die zweite auch nicht |

## Die Seite, von oben

1. **Kopf.** Projektname (aus `project_config.yaml`, `project.name`; in diesem Repo leer, darum
   „Project without a name" im Leer-Mockup), Stand = der Zeitstempel des Index (der Kernel schreibt
   Board und Index mit einer Uhr, `state._regenerate_index_locked`), ein Satz, was die Seite ist.
2. **First** — die Signatur der Seite: drei Zahlen auf einer Zeile, keine Kacheln.
   `blocked` (rot), `waiting on you` (blau), `in flight` (Tinte), je mit dem ersten Beispiel in einer
   Zeile darunter („BUG-0088 waits for TSK-0116", „BUG-0083: scope approval, open until 2026-09-04
   04:06"). Jede Zahl ist ein Schalter: gedrückt öffnet sich **darunter die Liste** genau dieser
   Karten (kompakte Zeilen, Id in der Farbe der Zahl, Status, Grund) und die Tafel dahinter wird
   abgeblendet. Gemessen in Sichtrunde 1: ohne diese Liste stand die erste blockierte Karte auf der
   vollen Tafel außerhalb des Bildschirms — die Zahl „3" war da, die drei Karten nicht.
   Bei null ist die Zahl grau, die Zeile sagt es („nothing is stuck", „no open question for you").
   `n finished, not yet archived` erscheint nur, wenn n > 0.
3. **Reiter.** Board · Product backlog · System backlog (· Timeline, wenn es Meilensteine gibt —
   FR-0079), rechts „archived, not on this board: 166 (BUG 2, …)".
4. **Board.** Eine Zeile je Typ, **lebende Typen zuerst**: die Wurzeltypen des Kits
   (`backlog_tree.ROOT_TYPES`), dann die übrigen Typen mit Automaten alphabetisch, zuletzt — als
   zugeklappter Block „Records" — die Typen ohne Automaten (APR, ARC, DEC, DSN, EVD, INV, WFR) als
   Listen, nicht als Spalten. Ein Typ ohne Einträge bekommt keine Zeile, sondern steht in einem Satz
   am Ende („No entries: change requests (CR)"). Innerhalb einer Zeile: **Slots** in Kettenreihenfolge
   (`board.status_columns`); ein leerer Slot auf der Kette bleibt schmal stehen, damit der Fluss lesbar
   bleibt; ein leerer **Endzustand** wird nicht gezeichnet, sondern in der Zeile „no cards in
   REJECTED · SUPERSEDED" genannt. Am Telefon fallen alle leeren Slots weg, und dieselbe Zeile nennt
   sie alle.
5. **Karte = T-Karte.** Kopfleiste (Id in Festbreite, überragt den Körper) + Titel. Blockiert: Kopf
   rot mit „blocked by TSK-0115". Wartet auf dich: Kopf blau mit „waiting on you: scope approval".
   Eine `TSK` ohne Titel zeigt, was sie ist: „ui for SR-0009 · harness-implementer" (Typ der Arbeit,
   wofür, wer). Sonst nur der Titel (Wunschliste §2: „Karten zeigen nur den Titel").
6. **Akte.** Der Klick öffnet die Karteikarte (FR-0053, `board._detail` unverändert): Kopf mit Id,
   Titel, Typ, Status, dann jedes Feld als Zeile; jede Id darin, die auf der Tafel liegt, ist ein Knopf.
7. **Bäume.** Markup und Regeln von `backlog_tree` unverändert; nur die Gestaltung: Knoten als
   flache Zeilen mit Führungslinie, Gruppenköpfe in Versalien, Unassigned mit rotem Strich.

## Die drei Zustände

| Mockup | Daten | Was er zeigt |
|---|---|---|
| `mockup-empty.html` | die `templates/project_memory/` des dev-team-Kits, kein Item | drei graue Nullen mit ihrer Antwort, ein Satz mit dem ersten Befehl, ein Satz, welche Typen leer sind — keine 45 leeren Rahmen |
| `mockup-healthy.html` | **17 echte Items dieses Repos** als Teilmenge (2 PR, 2 SR, 3 FR, 4 BUG, 3 TSK, 3 DEC; `fixtures.py` `HEALTHY_IDS`), 4 echte archivierte TSK; zwei Status und die Bindungen der Kopie bearbeitet, damit die Bäume sie platzieren (`HEALTHY_EDITS`, alle genannt) | 0 / 0 / 7, eine Tafel ohne Alarm |
| `mockup-blocked.html` | **die vollständige Kopie dieses Repos** (284 Items) plus eine Auflage, die der echte Zustand nicht hat: `blocked_by` auf TSK-0117, TSK-0118, BUG-0088 (`BLOCKED_OVERLAY`). Gemessen 2026-09-03: **0** Zeilen des echten Index tragen `blocked_by`; die offene scope-Anfrage auf BUG-0083 ist **echt** | 3 / 1 / 77; die Fokus-Listen; die Records-Sektion mit 144 Einträgen |
| `mockup-timeline.html` | die gesunde Teilmenge plus vier erfundene `MST`-Items (`milestones.yaml`), die echte Wurzeln nennen | FR-0079, Option TYP: Reiter Timeline, Sektion Milestones auf der Tafel |

## Was bewusst nicht auf der Seite steht

- **Kein Filter über Freitext, keine Suche.** Die Seite ist ein Bericht ohne Server; die Fokus-Schalter
  sind die drei Filter, die der Brief verlangt, und sonst keiner.
- **Kein Prozent „fertig".** Archiviertes liegt nicht auf der Tafel (Kernel-Regel: `active/` only);
  ein Anteil würde die sichtbare Hälfte zählen. Die Timeline sagt darum Zahlen je Bahn, keinen Prozentsatz.
- **Kein zweiter Zeitstempel.** Der Stand ist der des Index; die Seite behauptet keine eigene Uhr.
- **Keine Kacheln, kein Schatten, kein Farbverlauf, keine Pills** — siehe `03-tokens.md`.
