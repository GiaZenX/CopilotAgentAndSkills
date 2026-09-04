# TSK-0115 — Fragen an den Nutzer (Geschmack bleibt seine Sache)

Zum Ansehen zuerst: `review/blocked-board-1280-focus-blocked.png` (die volle Tafel dieses Repos mit
drei blockierten Karten und der geöffneten Liste), `review/healthy-board-1280.png` (eine ruhige
Tafel), `review/healthy-board-390.png` (Telefon), `review/blocked-board-1280-dark.png` (dunkel),
`review/timeline-timeline-1280.png` (Meilensteine, FR-0079), `review/diagram-plan.png` und
`review/diagram-mindmap.png` (FR-0080).

1. **Gefällt die Richtung „Plantafel mit T-Karten"?** Kartenkopf in Tinte, rot nur für blockiert, blau nur
   für „wartet auf dich", keine Kacheln, keine Farbverläufe, schmale Etikettenschrift in den Köpfen. Die
   Alternativen, die ich verworfen habe, stehen in `03-tokens.md`; wenn dir eine davon lieber ist, ist das eine
   Zeile für Phase 2, kein neuer Pass.

2. **Die drei Zahlen oben: sind es die richtigen drei?** `blocked` · `waiting on you` · `in flight`, so wie
   FR-0075 sie nennt. Ein vierter Kandidat wäre „neu, noch nicht begonnen" (heute 63 Items in diesem Repo) —
   ich habe ihn weggelassen, weil er nichts von dir verlangt; die Zeile „n finished, not yet archived" erscheint
   nur, wenn n > 0.

3. **Zählt eine Aufgabe in `READY` als „in flight"?** Meine Regel ist die des Automaten: nicht Anfang, nicht
   Ende → in Arbeit. `READY` heißt „freigegeben, wartet auf Zuteilung"; dass das Team sie hat, stimmt, dass
   jemand daran arbeitet, noch nicht. Wenn du „in flight" enger willst (erst ab `LEASED`), ist das eine
   Regel, die nur für `TSK` gilt — dann sage ich es auf der Seite dazu.

4. **FR-0079 — Meilenstein als eigener Typ (meine Empfehlung) oder als Datumsfeld?** Vorlage mit Kosten in
   `mst-decision-proposal.md`; das Bild dazu ist `mockup-timeline.html`. Deine Antwort ist die
   Entscheidung, die der Lead vor Phase 2 als DEC festhält.

5. **FR-0080 — wo sollen Plan und Mindmap liegen?** (a) `generated/`, neben dem Board, nie committet, immer
   frisch, in einem frischen Clone erst nach dem ersten Lauf da — das baut der Prototyp; (b) committet mit
   einer Frischeprüfung, wie Wunschliste §3a es sich wünscht — sofort sichtbar, aber ein Gate mehr und ein
   Verzeichnis, das heute jedes Kit ignoriert. Meine Empfehlung: (a), weil das Board dieselbe Antwort schon
   hat und zwei Regeln für zwei Dateien nebeneinander die Sorte Naht sind, die hier Runden kostet.

6. **Die Records (Belege, Entscheidungen, Freigaben) sind zugeklappt.** 144 der 284 Items dieses Repos sind
   solche Aufzeichnungen; heute stehen sie als Spalten zwischen der Arbeit. Ist zugeklappt-mit-Zahl richtig, oder
   willst du eine davon (die Entscheidungen?) offen sehen?

7. **Die Sprache der Seite ist Englisch — per deiner Entscheidung DEC-0049 (2026-08-22).** Ich habe den ersten
   Entwurf, der deutsch beschriftet war, deshalb gedreht. Wenn du das heute anders siehst, ist das ein neues FR
   (so steht es in der Entscheidung), nicht diese Runde.

Was **kein** Geschmack ist und nicht gefragt wird: dass die Seite eine reine Funktion des Zustands bleibt,
keine Netzanfrage macht, kein Item verschwinden lässt und nichts schreibt — das sind die Eigenschaften, die
FR-0030/FR-0053 gemessen haben und die Phase 2 mit den bestehenden Tests weiterträgt.
