# 08 — Die Endfassung: E über alle Zustände, mit den vier Behebungen (Phase 1d)

**Zum Anschauen** (alle unter `review/final/`, 101 Bilder, `render.json` mit `errors: []` bei allen
vier Seiten; die Seiten selbst: `final-empty.html`, `final-healthy.html`, `final-blocked.html`,
`final-timeline.html`, alle mit `make_mockups.py --style e`):

| Zustand | 1280 hell / dunkel | 1920 hell / dunkel | 390 hell / dunkel | dazu (1280 hell) |
|---|---|---|---|---|
| leer | `empty-board-1280.png`, `-dark` | `empty-board-1920.png`, `-dark` | `empty-board-390.png`, `-dark` | `empty-product-1280.png`, `empty-system-1280.png` |
| gesund | `healthy-board-1280.png`, `-dark` | `healthy-board-1920.png`, `-dark` | `healthy-board-390.png`, `-dark` | `healthy-system-1280.png` (Standard: Wurzeln offen, darunter zu), `-expanded`, `-collapsed`, `-keyboard-open`, `healthy-record-1280.png`, `healthy-records-1280.png` |
| blockiert | `blocked-board-1280.png`, `-dark` | `blocked-board-1920.png`, `-dark` | `blocked-board-390.png`, `-dark` | `blocked-board-1280-focus-blocked.png`, `-focus-you`, `blocked-system-1280*.png`, `blocked-product-1280.png`, `blocked-record-1280.png`, `blocked-records-1280.png` |
| Zeitleiste | `timeline-timeline-1280.png`, `-dark` | `timeline-timeline-1920.png`, `-dark` | `timeline-timeline-390.png`, `-dark` | `timeline-board-1280.png` (Sektion Milestones), `timeline-system-1280*.png` |

Token: `03-tokens-final.md` (= E aus `03-tokens-e.md` plus die Layoutregeln unten). Messungen:
`layout-before.md`/`.json` (E vor Phase 1d und die Phase-1-Zeitleiste) und `layout-after.md`/`.json`
(die vier Endseiten) aus `measure_layout.py` — Bounding-Boxes in Chromium, keine Augenmessung.
Kontrast: die Token sind die von E (`contrast-result.md`, Abschnitt E); die neuen Bedienelemente
(Falt-Knopf, „Expand all") stehen in Tinte bzw. gedämpfter Tinte auf Grund oder Karte — Paare, die dort
schon gemessen sind (17,4 / 17,2 und 5,7 / 7,3; 6,2 / 6,7 auf der Karte).

## Die vier Behebungen, je mit Messung vorher / nachher

### 1. Volle Breite und keine Überlappung

**Vorher** (`layout-before.md`, `direction-e.html`): auf der Tafel **110 überlappende Kartenpaare** bei
1280 **und** 1920 px (z. B. BUG-0022 in OPEN gegen BUG-0001 in TRIAGED, 18 px breit über die volle
Kartenhöhe), **333 Paare** bei 390 px (gestapelt, 36 px hoch); rechter Rand der Tafel leer:
**115 px bei 1280, 752 px bei 1920** (die PR-Zeile: ein Slot mit Karten plus drei leere, alle mit fester
Breite 15 rem).

**Ursache, im Code:** `.card` beginnt mit `all: unset` — das setzt `box-sizing` auf `content-box`
zurück, unter der globalen `border-box`-Regel hindurch. Phase 1 hatte keinen horizontalen Innenabstand
am Knopf, darum fiel es nicht auf; die modernen Regeln gaben der Karte `.75rem` Innenabstand und 1 px
Rand, also war jede Karte 26 px breiter als ihr Slot und ragte 18 px (26 minus 8 px Slot-Abstand) in den
Nachbar-Slot. Zweite Ursache bei 390 px: `flex: 1 1 15rem` wird in der gestapelten Spaltenanordnung zur
**Höhen**-Basis, der Slot schrumpft unter seine Karten, die Karten des nächsten Slots liegen darüber.

**Behebung:** `box-sizing: border-box` auf jedem Element, das mit `all: unset` beginnt (`.card`,
`.figure`, `.rec`, `.node-face`, `.ms-face`, `.fold`, `.tree-tools button`); Slots mit Karten
`flex: 1 1 15rem; min-width: 15rem` (wachsen in die Fensterbreite), leere Kettenslots `flex: 0 0 7rem`;
gestapelt (≤ 720 px) `flex: 0 0 auto; width: 100%`. Zeilen mit mehr Slots, als passen, scrollen weiter
horizontal (die Mindestbreite hält die Spalte lesbar).

**Nachher** (`layout-after.md`, alle vier Seiten, alle Reiter, 1280 / 1920 / 390): **0 überlappende
Paare** in allen sieben Elementgruppen, **0 Textüberläufe**, rechter Rand der Tafel **0 px** bei 1280,
1920 und 390, keine scrollende Zeile auf diesen Fixtures. Gesichtet: `blocked-board-1920.png`
(Karten füllen die Breite), `blocked-board-390.png`.

**Nebenbefund derselben Sicht:** mit wachsenden Slots stand die rechtsbündige Slot-Zahl neben dem Kopf
der **nächsten** Spalte („3 APPROVED"); die Zahl steht jetzt neben ihrem Namen (`blocked-board-1280.png`).

### 2. Einklappbare Hierarchie

**Spezifikation** (gebaut im Prototyp, `make_mockups._branches`, Skriptzusatz in `SCRIPT`):

- Jeder Knoten mit Kindern trägt vor seiner Zeile einen `<button class="fold" data-fold="<id>"
  aria-expanded="true|false" aria-label="children of <id>">`; ein Knoten ohne Kinder einen gleich
  breiten Platzhalter, damit die Zeilen fluchten. Der Klick setzt `hidden` auf die `.group`-Kinder des
  Knotens und dreht `aria-expanded`; der Pfeil ist CSS aus `aria-expanded`, das Skript bleibt eine
  Konstante ohne Item-Inhalt. Über jeder Baum-Sicht „Expand all" / „Collapse all" (`data-fold-all`),
  wirksam nur in der eigenen Sicht.
- **Reine Zustandsfunktion:** kein Netz, kein Schreiben, kein `localStorage` — Zustand über Reload ist nicht
  gefordert und wird nicht gehalten; die Seite ist nach jedem Zustandsschreiben ohnehin neu.
- **Warum nicht `<details>/<summary>`:** die Zeile eines Knotens **ist** schon ein Knopf (`data-open`
  öffnet die Akte); eine `summary`, die einen Knopf enthält, ist ungültiges HTML und zwei konkurrierende
  Klickziele in einer Zeile. `hidden` per Klick ist außerdem genau der Mechanismus, den die Seite für Reiter
  und Akten schon hat (`board._SCRIPT`), und die `noscript`-Regel (`[hidden] { display: block !important }`)
  macht ohne Skript alles sichtbar und blendet die Falt-Knöpfe aus — dieselbe Ehrlichkeit wie bei den Reitern.
- **Tastaturpfad:** der Falt-Knopf ist ein natives `<button>` — Tab erreicht ihn, Enter/Leertaste falten,
  `:focus-visible` zeichnet einen 2-px-Ring in Tinte (`healthy-system-1280-keyboard-open.png`:
  Fokus per `focus()` gesetzt, Enter gedrückt, Gruppe offen, Ring sichtbar).
- **Standard: Wurzeln offen, ab Tiefe 1 zu** (`FOLD_DEPTH = 1`). Grund: eine Seite, deren erster Blick
  eine Liste geschlossener Wurzeln ist, beantwortet nichts; eine ganz offene Systemsicht dieses Repos ist
  105 Zeilen lang. So sieht der Leser jede Wurzel mit dem, was direkt darunter hängt (SR, BUG, TSK als
  Gruppen), und ein Klick öffnet die Aufgaben unter einer SR. Gesichtet: `healthy-system-1280.png`
  (Standard), `-expanded`, `-collapsed`.

### 3. Zeitleiste in E

`final-timeline.html` = die gesunde Teilmenge plus `milestones.yaml`, `--style e`, mit dem Reiter
**Timeline** und der Sektion **Milestones** auf der Tafel (`timeline-board-1280.png`). Die
Heute-Marke-Regel aus dem MST-Vorschlag ist gebaut: das Lineal hat **drei Bänder** — die Heute-Marke
besitzt das obere allein, Marken-Beschriftungen wechseln zwischen unterem und mittlerem Band, wenn sie
näher als 9 % beieinander stünden. **Vorher** (`mockup-timeline.html`, Phase 1): 1 Überlappung bei 390 px
(`today 2026-09-03` gegen `MST-0001`, 37 × 8 px). **Nachher:** 0 bei 1280, 1920 und 390
(`timeline-timeline-1280.png`, `-dark`, `-390`). Der Nutzer hat den Reiter in D/E vermisst, weil dort nur
der Zustand „blockiert" gerendert war — die Fixture ohne Meilensteine zeigt keinen Reiter, und das ist
richtig so: ein Reiter für null Meilensteine wäre eine leere Zusage. Grenze, benannt: drei Marken innerhalb
von 9 % teilen sich zwei Bänder; die dritte kann die erste berühren.

### 4. Vollständigkeit

Vier Zustände × drei Breiten × hell/dunkel × jeder Reiter, dazu Fokus blockiert / wartet, Akte offen,
Records offen, Baum Standard / auf / zu / Tastatur — 101 Bilder, `errors: []` bei allen vier Seiten,
SHA-256 der vier Seiten im Record gleich den beiliegenden Dateien. `layout-after` misst dieselben Seiten
in allen Reitern und Breiten: 0 Überlappungen, 0 Überläufe.

## Sichtprotokoll 1d

1. **1d-1** (8 Bilder nach dem ersten Bau): Breite und Überlappung behoben (Messung 0/0/0), Zeitleiste in E
   sauber, Tastaturpfad sichtbar. Befunde: die Slot-Zahl stand neben dem Kopf der nächsten Spalte; der
   Falt-Pfeil kam als Kästchen + „BE" an (die CSS-Escape-Sequenz erreichte die Seite mit doppeltem
   Backslash) — beides behoben, die Pfeile stehen jetzt als Zeichen im UTF-8-Blatt.
2. **1d-2** (3 Bilder): Zahl neben Namen, Pfeile ▾/▸, leere Seite bei 1920 nutzt die Breite.

## Was Phase 2 aus diesem Blatt baut

`04-build-spec.md` zeigt auf `03-tokens-final.md` und trägt unter §5 die drei neuen Tests: volle Breite
über Bounding-Box, keine Überlappung über Bounding-Box, Einklappen als DOM-Test plus Tastaturpfad im
Browser. Die Prototyp-Regeln stehen in `make_mockups.py` (Markup, `SCRIPT`, Basis-CSS) und
`directions.py` (`M_TOKENS_*`, `M_FONTS`, `M_RULES`, `E_RULES`) — das ist der Stoff für `board._STYLE`,
`board._SCRIPT` und die Baum-Funktionen.
