# 06 — Drei Richtungen für die visuelle Sprache des Boards (Phase 1b, DEC-0065 (6))

**Zum Anschauen** (alle unter `review/directions/`, Zustand „blockiert" = die vollständige Kopie dieses
Repos, 284 Items, drei gesetzte `blocked_by`, eine echte offene Freigabe-Anfrage):

| Richtung | 1280 hell | 1280 dunkel | 390 hell | 390 dunkel | Fokus blockiert | Fokus wartet auf dich | Akte |
|---|---|---|---|---|---|---|---|
| **A — Werkstatt** | `a-1280.png` | `a-1280-dark.png` | `a-390.png` | `a-390-dark.png` | `a-1280-focus-blocked.png` | `a-1280-focus-you.png` | `a-1280-record.png` |
| **B — Blueprint** | `b-1280.png` | `b-1280-dark.png` | `b-390.png` | `b-390-dark.png` | `b-1280-focus-blocked.png` | `b-1280-focus-you.png` | `b-1280-record.png` |
| **C — Leitsystem** | `c-1280.png` | `c-1280-dark.png` | `c-390.png` | `c-390-dark.png` | `c-1280-focus-blocked.png` | `c-1280-focus-you.png` | `c-1280-record.png` |

Dazu die dunklen Fokus-Bilder (`*-1280-dark-focus-*.png`), die Seiten selbst
(`direction-a.html`, `direction-b.html`, `direction-c.html`) und `review/directions/render.json`
(27 Bilder, an die SHA-256 der drei Seiten gebunden, `errors: []` bei allen dreien).

Unverändert aus Phase 1: Informationsarchitektur (`01`), Datenvertrag (`02`), Rig, Fixtures,
Messungen. Die drei Richtungen sind **drei Token-Blätter** (`03-tokens-a.md`, `-b.md`, `-c.md`) plus je
eine Handvoll Charakterregeln (`directions.py`) über demselben Markup — `make_mockups.py --style a|b|c`.
Das ist die Trennung, die DEC-0065 verlangt: keine Zahl und kein Test von Phase 1 ändert sich.

## Der Abstand zum Finanz-Dashboard (TSK-0109), gemessen an den Token

`finance-dashboard.template.html` `:root` gegen das Phase-1-Blatt: **sieben Werte wären gleich oder
derselben Familie** — und darum las der Nutzer die Seite als Kopie. Jede Richtung ändert alle sieben.

| Token | TSK-0109 (Finanz) | Phase 1 (Board) — gleich in der Sache | A Werkstatt | B Blueprint | C Leitsystem |
|---|---|---|---|---|---|
| Display-/Kopfschrift | `Bahnschrift` | `Bahnschrift SemiCondensed` | `Franklin Gothic Medium` / `Gill Sans` | `Candara` / `Corbel` | `Verdana` / `Tahoma` |
| Fließtext | `Segoe UI` | `Segoe UI` | `Trebuchet MS` / `Gill Sans` | `Candara` / `Corbel` | `Verdana` / `Tahoma` |
| Festbreite | `Consolas` | `Cascadia Mono`, `Consolas` | `Courier New` (Schreibmaschine) | `Lucida Console` | **keine** — Ids in der Textschrift mit Tabellenziffern |
| Der eine Akzent (Klick / „du") | Stempelblau `#1E4FCB` | Blau `#1a56c4` | gelber Karton `#f3d67a` / Kopf `#6a5300` | Revisions-Ocker `#f2c14e` | Warngelb `#f2c200` |
| Alarm | Rot `#C8102E` | Rot `#b4121b` | roter Karton `#f0b3ad` / Kopf `#a1281f` | Rotstift `#a8321c` | Stoppfeld `#b3261e` |
| Grund | Papier `#FBFBF9` (fast weiß) | Tafel `#eceef1` (fast weiß) | Emaille `#33423e` (**dunkel, auch hell**) | Zeichenpapier `#f4f7fa` (kühl, fast weiß — der eine Wert, der der Finanzseite nahe bleibt; unten als Preis genannt) | Wand `#e6e3dc` (warmes Mittelgrau) |
| Tinte | `#191C1F` | `#16181c` | Kreide `#e8e3d8` auf der Tafel, `#241d14` auf dem Karton | Preußischblau `#143a66` | `#111111` (schwarz — derselben Klasse; der Charakter kommt aus den Feldern, nicht aus der Tinte) |
| Signatur | Doppelstrich unter Summen, Stempel | überstehender T-Kartenkopf in Tinte | Karton in drei Farben, Kopf als Etikett | Rahmen statt Flächen, Schraffur für „blockiert" | Farbfelder mit weißer/schwarzer Schrift, schwarze Kopfbänder |
| Radius / Schatten / Verlauf / Pill | 3 px Stempel, keine | 2–3 px, keine | **0**, keine | **0**, keine | **0**, keine |

Was in allen dreien bleibt und **Konvention, nicht Optik** ist: Rot heißt „hängt". Der Wert ist je
Richtung ein anderer, der Sinn nicht — ein Board, auf dem Blockiertes grün wäre, wäre eine Falle.

## A — Werkstatt

**Charakter, ein Satz:** Die Plantafel aus der Werkstatt: dunkle Emaille, Karten aus Karton in drei
Farben, Ids wie von der Schreibmaschine — was zählt, ist die Farbe des Kartons, nicht ein Zeichen darauf.

**Vorbild aus der realen Welt:** die T-Karten-Plantafel in Werkstatt und Disposition (Steckleisten,
farbiger Karton für Auftragsarten, getippte Laufkarten). Nicht kopiert wird ein Produkt; genommen wird das
Material: Emaille, Manila, Rot- und Gelbkarton.

**Was sie kostet:** (1) Die Seite ist **auch im hellen Modus dunkel** — eine Tafel ist dunkel; wer eine
helle Seite erwartet, bekommt keine (der Dunkelmodus ist dann nur eine Stufe dunkler, `a-1280-dark.png`).
(2) `Courier New` fett für die drei Zahlen ist dünner als eine Grotesk (`a-1280.png`, die „77"). (3) Bei
390 px stapeln sich die Karten in voller Breite; der Karton trägt, die Tafel dahinter verschwindet fast
(`a-390.png`). Kontrast gemessen (`contrast.py`, alle Paare ≥ 4,5:1 bzw. ≥ 3:1 groß): Text auf Tafel 8,2 /
12,4; Titel auf Karton 12,0 / 8,5; Titel auf rotem Karton 9,3 / 8,8; Weiß auf rotem Kopf 7,4 / 6,4 (dunkel
nach Korrektur von 4,0); Titel auf gelbem Karton 11,7 / 6,7; die rote Zahl 4,9 / 7,3; die gelbe 7,5 / 11,2;
Ids in den Fokus-Listen 5,3 / 4,8 und 5,3 / 7,3 (nach Korrektur: lachs auf Manila war 1b-2 unlesbar).

**Verworfener Brief:** die Andon-Tafel aus der Fabrik (rot/gelb/grün leuchtende Zähler auf Schwarz) —
verworfen, weil dunkler Grund mit Leuchtfarbe der KI-Standard 2 ist und „77 in flight" wie eine Störzahl
läse.

## B — Blueprint

**Charakter, ein Satz:** Eine Bauzeichnung: eine Tinte, gezogene Rahmen statt Flächen, Versalien wie
Zeichenbeschriftung, Schraffur, wo etwas hängt; im Dunkeln die Blaupause selbst.

**Vorbild aus der realen Welt:** die technische Zeichnung mit Schriftfeld — Preußischblau auf
Zeichenpapier, Linienstärken statt Farben, Rotstift für Änderungen, Ocker für Revisionswolken; dunkel die
Cyanotypie (weiß auf Blau).

**Was sie kostet:** (1) Der Grund ist fast weiß und damit der eine Wert, der der Finanzseite nahe bleibt
(`#f4f7fa` gegen `#FBFBF9`); der Abstand entsteht aus Tinte, Schrift und Rahmen, nicht aus dem Papier.
(2) Rahmen statt Flächen heißt bei 390 px viele Linien untereinander (`b-390.png`); „WAITING ON YOU" bricht
in Versalien auf zwei Zeilen. (3) Versalien in Kopfzeilen und Zahlen lesen langsamer als gemischte Schrift.
(4) Die Nähe zum Broadsheet-Standard (Haarlinien, Null-Radius) ist real; was trennt: eine farbige Tinte,
Schraffur, kein Spaltensatz. Kontrast: Tinte auf Papier 10,7 / 12,6; gedämpft 5,2 / 7,5; Weiß auf Rotstift
6,7 / 7,9; Schwarz auf Ocker 10,4 / 10,4; rote Zahl 6,2 / 6,3; Ocker-Zahl 5,5 (hell mit `#8a5a00`) / 8,6.

**Verworfener Brief:** das Ingenieur-Notizbuch (Rasterpapier, handschriftliche Schrift) — verworfen, weil
es keine handschriftliche Systemschrift gibt und ein Raster im Grund gegen die Slot-Rahmen läuft.

## C — Leitsystem

**Charakter, ein Satz:** Wegweisung wie am Bahnhof: große humanistische Schrift, drei Farbfelder mit
weißer oder schwarzer Schrift, schwarze Kopfbänder, breite Kanten — aus zehn Metern lesbar.

**Vorbild aus der realen Welt:** Leitsysteme in Bahnhöfen und Flughäfen (Feld, Farbe, Schrift, kein
Piktogramm nötig): Rot = Halt, Gelb = Achtung mit schwarzer Schrift, Grün = Richtung. Verdana/Tahoma stehen
hier für die humanistische Beschilderungsschrift, die kein System mitbringt.

**Was sie kostet:** (1) Drei farbige Felder oben sind das, was einer Kachelwand am nächsten kommt — was
trennt: kein Radius, kein Schatten, kein Verlauf, Felder bis an den Rand, und ein leeres Feld ist grau statt
grün (`c-1280.png`; bei null wäre kein Feld farbig). (2) Bei 390 px stapeln sich die Felder zu drei Bändern
(`c-390.png`, nach Korrektur: dreispaltig liefen sie über). (3) Farbe trägt hier viel; der Fokus-Zustand
braucht darum einen dicken schwarzen Rahmen statt einer Füllung. Kontrast: Text auf Wand 14,7 / 15,2;
Weiß auf Stoppfeld 6,5 / 5,4 (dunkel nach Korrektur von 4,3); Schwarz auf Warngelb 11,2 / 11,2; Weiß auf
Grün 6,3 / 5,3 (nach Korrektur von 3,6); Kopfband 14,7 / 15,2. Die Ids in den Fokus-Listen tragen das Feld
(gelb auf grauer Wand war 1b-2 unlesbar).

**Verworfener Brief:** die Abfahrtstafel (Fallblatt, bernstein auf schwarz) — verworfen, weil es KI-Standard
2 ist und Fahrpläne verspricht, die der Kernel nicht hat.

## Sichtprotokoll 1b

1. **1b-1** (9 Bilder): A und B tragen; in C waren **die Zahlen 3 und 1 unsichtbar** — das Phase-1-Blatt färbt
   die rote und gelbe Zahl, auf rotem und gelbem Feld verschwand sie (gleiche Spezifität, spätere Regel
   gewinnt); bei 390 px liefen Cs drei Spalten über. Kontrast dunkel: A roter Kopf 4,0, C Stoppfeld 4,3,
   C Grünfeld 3,6 — drei Werte angehoben.
2. **1b-2** (6 Bilder): C korrigiert; A: Ids der Fokus-Liste lachs auf Manila unlesbar; C: gelbe Id auf
   grauer Wand unlesbar — beide auf Kopf- bzw. Feldfarbe gesetzt, gemessen 5,3 / 4,8 / 7,3.
3. **1b-3**: die beiden Stellen nachgesehen, sauber.

## Empfehlung

**A — Werkstatt.** Sie ist am weitesten von beiden Referenzen entfernt (kein Wert der Finanzseite bleibt,
keine Kachel, kein Radius, keine helle Fläche mit Blauakzent), sie gibt der T-Karten-Struktur aus Phase 1
ihr eigenes Material, und die Antwort auf die drei Fragen des Briefs steht in der Farbe des Kartons — das
liest man, bevor man liest. Der Preis ist benannt: eine dunkle Seite auch im hellen Modus. Wer eine helle
Seite will, nimmt **C** (lesbarste, größte Signale, 390 px am besten) und bezahlt mit der Nähe der drei
Felder zur Kachel. **B** ist die schönste in Ruhe und die schwächste im Alarm: Schraffur und Rotstift sind
leiser als Karton oder Feld, und ihr Papier bleibt der Finanzseite am nächsten.

Der Nutzer entscheidet; Phase 2 trägt das gewählte Blatt nach `board._STYLE`, und das Blatt ist der eine
Ort der Werte.
