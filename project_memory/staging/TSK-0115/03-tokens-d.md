# 03-d — Token-Blatt D: Modern, Kante

Werte stehen genau einmal: `directions.M_TOKENS_LIGHT`, `M_TOKENS_DARK`, `M_FONTS` (gemeinsam mit E) und
`D_RULES` in `directions.py`. D und E teilen Grund, Tinte, Schrift und die drei Signalfarben; sie
unterscheiden sich in **einer** Dimension — D signalisiert mit einer 4-px-Leiste an der Kante, jede
Fläche bleibt neutral.

| Token | Rolle | Grund |
|---|---|---|
| `--board` | ruhiger neutraler Grund (hell `#f5f5f7`, dunkel `#0f1115`) | eine Produktoberfläche von heute steht auf Neutral; der dunkle Modus ist ein echter (Grund, Karte, Tinte, Linien kippen alle) |
| `--card` | Karte, Fokus-Liste, Akte, Baumknoten | Weiß bzw. `#171a1f`; eine Karte ist eine Zeile mit Kante — Haarlinie `--rule`, kein Schatten |
| `--slot` | leere Zahl oben, Grund der Records-Liste | eine Stufe vom Grund weg, sonst nichts |
| `--ink`, `--ink-2` | Text; Reiter-Unterstrich; Fokusring; Links | Tinte trägt alles Chrom — **kein Akzent für Klickbares**, damit Farbe Signal bleibt |
| `--rule` | Haarlinien: Kartenrand, Reiterlinie, Trennlinien; die neutrale Kantenleiste | `#e2e4e8` / `#2a2f37` |
| `--stop`, `--stop-text` | **blockiert**: Leiste an Zahl und Karte; Zahl, Flagge, Id in der Liste als Text | Rot `#d92d20`; als Text `#b42318` (hell) / `#f97066` (dunkel), damit 4,5:1 hält |
| `--you`, `--you-text` | **wartet auf dich**: Leiste; Text | Bernstein `#b54708`; Text hell derselbe, dunkel `#fdb022` |
| `--go`, `--go-text` | **in flight**: Leiste; Text | Petrol `#107569`; Text dunkel `#2ed3b7` — bewusst kein Blau (Finanz-Stempel) und kein Violett (das alte Template) |
| `--*-tint` | in D ungenutzt (E-Token) | — |
| `--font-display` | `h1`, `h2`, die drei Zahlen | `Segoe UI Variable Display` / `Inter` / `SF Pro Display`: geometrisch-humanistische Sans, enge Laufweite (−0,02/−0,03 em) |
| `--font-body` | alles andere, auch Ids (Tabellenziffern, Gewicht 500) | `Segoe UI Variable Text` / `Inter` / `SF Pro Text`; **keine Festbreite** |
| Radius | 4 px an Karte, Zahl, Akte; 3 px an Badges; 0 an Reitern | minimal und begründet: die Kante einer Zeile, kein Kachelrahmen; kein Schatten, kein Verlauf |

Kontrast (hell / dunkel, `contrast.py`): Text auf Grund 17,4 / 17,2; gedämpft 5,7 / 7,3; Text auf Karte
18,9 / 15,8; gedämpft auf Karte 6,2 / 6,7; blockiert als Text 6,6 / 6,3; wartet als Text 5,4 / 9,5;
in flight als Text 5,6 / 9,2; die drei Zahlen auf dem Grund 6,0 / 6,8, 5,0 / 10,3, 5,1 / 10,0 (groß).

Abstand zu TSK-0109 (sieben Token): Kopfschrift Segoe UI Variable Display statt Bahnschrift; Fließtext
**Segoe UI Variable statt Segoe UI — dieselbe Familie, vom Brief so verlangt (Inter/Segoe-UI-Variable-Klasse)**;
keine Festbreite statt Consolas; **kein Akzent** statt Stempelblau; Alarm `#d92d20`/`#b42318` statt `#C8102E`
(Konvention bleibt, Wert nicht); Grund `#f5f5f7` statt `#FBFBF9` — **dieselbe Klasse „fast weiß"**, weil ein
ruhiger Neutralgrund die Forderung des Briefs ist; Tinte `#0f1115` statt `#191C1F` — dieselbe Klasse. Drei
von sieben bleiben also in der Klasse, und alle drei sind die, die „modern, neutral" verlangt; was die Seite
von der Finanzseite trennt, ist das Fehlen von Bahnschrift, Doppelstrich, Stempel, Blauakzent und Festbreite
sowie die Signalfarben, die dort nicht existieren.
