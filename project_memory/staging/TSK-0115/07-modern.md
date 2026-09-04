# 07 — Zwei moderne Fassungen (Phase 1c): D „Kante" und E „Fläche"

**Zum Anschauen** (alle unter `review/directions/`, Zustand „blockiert" = die vollständige Kopie dieses
Repos, 284 Items, drei gesetzte `blocked_by`, eine echte offene Freigabe-Anfrage):

| Fassung | 1280 hell | 1280 dunkel | 390 hell | 390 dunkel | Fokus blockiert | Fokus wartet auf dich | Akte |
|---|---|---|---|---|---|---|---|
| **D — Modern, Kante** | `d-1280.png` | `d-1280-dark.png` | `d-390.png` | `d-390-dark.png` | `d-1280-focus-blocked.png` | `d-1280-focus-you.png` | `d-1280-record.png` |
| **E — Modern, Fläche** | `e-1280.png` | `e-1280-dark.png` | `e-390.png` | `e-390-dark.png` | `e-1280-focus-blocked.png` | `e-1280-focus-you.png` | `e-1280-record.png` |

Dazu die dunklen Fokus-Bilder (`d-1280-dark-focus-*.png`, `e-1280-dark-focus-*.png`), die Seiten
(`direction-d.html`, `direction-e.html`) und `review/directions/render.json` (`errors: []` bei beiden;
9 Bilder je Fassung, SHA-256 der Seiten im Record). Token: `03-tokens-d.md`, `03-tokens-e.md`; Code:
`directions.py` (`M_TOKENS_LIGHT`, `M_TOKENS_DARK`, `M_FONTS`, `M_RULES`, `D_RULES`, `E_RULES`),
`make_mockups.py --style d|e`. Unverändert: Informationsarchitektur, Datenvertrag, Rig, Fixtures,
Messungen aus Phase 1.

## Der Brief, wie ich ihn gelesen habe

Behalten aus C: **die starke Farbe als Signal** — blockiert, wartet auf dich, läuft sind an der Farbe
erkennbar, kräftig. Weg: jede Materialanmutung (Emaille, Karton, Schreibmaschine, Blaupause,
Wegweiser, Konsolen-Versalien, Schraffur). Modern: eine geometrisch-humanistische Sans als
Systemstapel (`Segoe UI Variable` / `Inter` / `SF Pro`), Weißraum, präzise Ausrichtung, flache Farbe,
ruhiger Neutralgrund hell **und** ein echter dunkler Modus, Hierarchie aus Typografie.

## Woran man in D und E „modern" von „KI-Standard" unterscheidet — drei Sätze

1. **Farbe ist nur Signal, nie Dekor:** die drei Signalfarben (Rot, Bernstein, Petrol) erscheinen
   ausschließlich dort, wo etwas blockiert ist, auf dich wartet oder läuft; Reiter, Links, Fokusringe,
   Kopfzeilen und Records sind Tinte auf Neutral, es gibt **keinen Akzent** für Klickbares, und eine Null
   ist grau — nichts auf der Seite ist farbig, weil es hübsch wäre.
2. **Eine Karte ist eine Zeile mit Kante, keine schwebende Kachel:** Haarlinie, kein Schatten, kein
   Verlauf, Radius 4 px (die Kante einer Zeile in einer UI von heute, an Karte, Zahl und Akte gleich —
   nirgends mehr), die Spalten sind Abstand, kein Rahmenraster, und ein Status ist ein Wort neben der Id,
   kein Pill.
3. **Hierarchie kommt aus Typografie und Abstand, nicht aus Kästen:** drei Größen (2,4 rem Zahlen, 1,75 rem
   Titel, 0,875–0,9 rem Text), zwei Gewichte (600 / 500), enge Laufweite an großen Graden, Tabellenziffern,
   ein Reiter-Unterstrich in Tinte — nichts ist gleich wichtig: die drei Zahlen sind das Größte, die
   Records das Kleinste und zugeklappt.

## Der Abstand zum Finanz-Dashboard (TSK-0109), an den sieben Token

| Token | TSK-0109 | Phase 1 (Board) | D / E |
|---|---|---|---|
| Kopf-/Displayschrift | `Bahnschrift` | `Bahnschrift SemiCondensed` | `Segoe UI Variable Display` / `Inter` |
| Fließtext | `Segoe UI` | `Segoe UI` | `Segoe UI Variable Text` / `Inter` — **dieselbe Familie, vom Brief so verlangt** |
| Festbreite | `Consolas` | `Cascadia Mono` | **keine**; Ids in der Textschrift, Gewicht 500, Tabellenziffern |
| Der eine Akzent | Stempelblau `#1E4FCB` | Blau `#1a56c4` | **keiner** — Chrom ist Tinte; Farbe ist Signal (Rot / Bernstein / Petrol) |
| Alarm | `#C8102E` | `#b4121b` | `#d92d20` Feld, `#b42318` Text (Konvention bleibt, Wert nicht) |
| Grund | `#FBFBF9` | `#eceef1` | `#f5f5f7` hell, `#0f1115` dunkel — **hell dieselbe Klasse „fast weiß"**: ein ruhiger Neutralgrund ist die Forderung des Briefs |
| Tinte | `#191C1F` | `#16181c` | `#0f1115` — dieselbe Klasse |
| Signatur | Doppelstrich, Stempel | überstehender Kartenkopf | D: 4-px-Leiste an der Kante; E: die Fläche selbst |
| Radius / Schatten / Verlauf / Pill | 3 px, keine | 2–3 px, keine | 4 px begründet, keine, keine, keine |

Drei der sieben bleiben in der Klasse (Textschriftfamilie, heller Neutralgrund, dunkle Tinte), und alle
drei sind genau die, die „modern und ruhig" verlangt; was die Seite von der Finanzseite trennt, ist das
Fehlen von Bahnschrift, Doppelstrich, Stempel, Blauakzent und Festbreite — und die drei Signalfarben,
die dort nicht existieren.

## D — Modern, Kante

**Charakter, ein Satz:** Eine neutrale Oberfläche, auf der nur eine 4-px-Leiste am linken Rand sagt,
was mit einer Zahl oder einer Karte ist — Rot, Bernstein, Petrol, sonst Tinte und Weißraum.

**Was sie kostet:** (1) Das Signal ist schmal: in der Spaltenansicht ist eine blockierte Karte an einer
4-px-Kante und einem farbigen Flaggentext zu erkennen (`d-1280-focus-blocked.png`: die Liste; `d-1280.png`
unten: BUG-0083 mit bernsteinfarbener Kante) — kräftig ist die **Zahl**, nicht die Karte; wer die Karte
aus zwei Metern erkennen will, nimmt E. (2) Neutrale Karten tragen eine graue Kante derselben Breite,
damit die farbige nicht springt — eine Kante mehr pro Karte. (3) Dunkler Modus: Signalfarben werden als
Text heller (`#f97066`, `#fdb022`, `#2ed3b7`), die Leisten behalten die Feldfarbe. Kontrast (hell /
dunkel, alle Paare ≥ 4,5:1 bzw. ≥ 3:1 groß): Text auf Grund 17,4 / 17,2; gedämpft 5,7 / 7,3; blockiert als
Text 6,6 / 6,3; wartet als Text 5,4 / 9,5; in flight als Text 5,6 / 9,2; Zahlen 6,0 / 6,8, 5,0 / 10,3,
5,1 / 10,0. Bei 390 px: drei Zeilen mit Kante untereinander (`d-390.png`).

**Verworfener Brief:** ein Status-Punkt-System (farbiger 8-px-Punkt vor der Id, wie in vielen
Issue-Trackern) — verworfen, weil ein Punkt auf einer Tafel mit 284 Karten kein kräftiges Signal ist und
der Nutzer genau das behalten wollte.

## E — Modern, Fläche

**Charakter, ein Satz:** Dieselbe Oberfläche, aber das Signal ist die Fläche: die drei Zahlen sind volle
Farbfelder mit weißer Schrift, eine blockierte oder wartende Karte ist getönt und trägt ein kleines
gefülltes Etikett.

**Was sie kostet:** (1) Drei volle Felder oben sind der Punkt, an dem E einer Kachelwand am nächsten kommt;
was trennt, steht in den drei Sätzen oben (eine Null ist grau, unter den Zahlen ist nichts farbig, was nicht
blockiert ist oder wartet, 4 px, kein Schatten, kein Verlauf). (2) Weiß auf Rot ist mit 4,8:1 der knappste
Wert des Pakets — die Beispielzeile im Feld ist deshalb 0,8 rem und nicht kleiner. (3) Die Tönung einer
Karte (`#fee4e2`, `#fef0c7`) braucht im dunklen Modus eigene Werte (`#3a1715`, `#3a2810`), sonst kippt
sie ins Pastell — gemessen: Tinte auf Tönung 15,7 / 14,5 und 16,6 / 12,8, Signaltext auf Tönung
5,5 / 5,7, 4,8 / 7,7, 4,8 / 7,7. Bei 390 px: drei Felder untereinander (`e-390.png`).

**Verworfener Brief:** Farbfelder **und** farbige Karten für alle drei Klassen, also auch „in flight" als
petrolfarbene Tönung auf 77 Karten — verworfen, weil dann fast jede Karte dieser Tafel farbig wäre und
Farbe aufhörte, Signal zu sein.

## Sichtprotokoll 1c

1. **1c-1** (8 Bilder): D und E tragen hell, dunkel und bei 390 px; Kontraste im ersten Lauf alle über der
   Schwelle (E Weiß auf Rot 4,8 als knappster). Befund in beiden: das Phase-1-Blatt füllt den Kopf einer
   signalisierten Karte — BUG-0083 trug in D und E ein bernsteinfarbenes Band quer über die Karte, in D
   gegen die Regel „nur die Kante", in E doppelt zur Tönung. Regel in `M_RULES` ergänzt.
2. **1c-2** (3 Bilder): Band weg; E zeigt Tönung + Etikett; Akte in D geprüft (neutral, Haarlinie,
   Feldnamen in gemischter Schreibung). Neuer Befund in D: der Kopf der signalisierten Karte erbte weiße
   Schrift, die Id stand weiß auf Weiß — Kopf in D auf gedämpfte Tinte gesetzt.
3. **1c-3**: D nachgesehen (BUG-0083 mit Id, Kante und Flaggentext).

## Empfehlung

**E — Fläche**, weil sie den Satz des Nutzers wörtlich nimmt („starke farbliche Hervorhebung") und ihn
mit den drei Regeln oben vom Kachel-Look trennt: die Farbe steht nur bei den drei Zahlen und den wenigen
Karten, die etwas von dir wollen — auf dieser Tafel sind das 4 von 284. D ist die ruhigere Fassung für
jemanden, der die Farbe auf die Zahl beschränken will; beide teilen jedes Token, also ist der Wechsel
später eine Handvoll Regeln, kein neues Blatt. Der Nutzer entscheidet; Phase 2 trägt Blatt und Regeln
nach `board._STYLE`.
