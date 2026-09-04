# 03-a — Token-Blatt A: Werkstatt

Werte stehen genau einmal: `directions.A_TOKENS` (hell und dunkel) und `A_RULES` in `directions.py`;
Phase 2 trägt sie nach `board._STYLE`. Hier Namen, Rolle, Grund.

| Token | Rolle | Grund |
|---|---|---|
| `--board` | Seitengrund | die Emaille der Plantafel — dunkel in beiden Modi; hell ist ein Werkstattlicht, dunkel die Nachtschicht |
| `--slot` | Steckleiste eines Zustands, Fokus-Listen, Warnbanner | eine Stufe heller als die Tafel, damit Karten darauf liegen |
| `--ink`, `--ink-2` | alles, was **auf der Tafel** steht: Kopf, Reiter, Sektionstitel, Slot-Köpfe | Kreide; zwei Stufen |
| `--rule` | Konturen auf der Tafel | die Kante der Leiste |
| `--card`, `--card-ink`, `--card-ink-2` | Manila-Karton und seine Tinte; auch Akte, Baumknoten, Fokus-Zeilen | Karton ist hell, Tafel ist dunkel — darum zwei Tintenpaare, und jedes Element sagt, worauf es steht |
| `--card-head` | Kopf einer gewöhnlichen Karte | derselbe Karton, eine Stufe tiefer: das Etikett |
| `--card-stop`, `--head-stop` | roter Karton und sein Kopf: **blockiert** | die Farbe des Kartons trägt die Antwort; der Kopf nennt den Blocker in Weiß |
| `--card-you`, `--head-you` | gelber Karton und sein Kopf: **wartet auf dich** | Gelb ist der Zettel, der einen angeht |
| `--stop`, `--you` | die Zahlen oben, der Fokusrahmen — auf der Tafel | hellere Stufen derselben zwei Farben, weil sie auf Dunkel stehen |
| `--link-on-card` | Id-Knöpfe in der Akte | Ocker auf Manila; das Blau der Finanzseite gibt es hier nicht |
| `--font-head` | Titel, Sektionen, Reiter | `Franklin Gothic Medium` / `Gill Sans` / `Trebuchet MS`: die Grotesk des Werkstattschilds |
| `--font-body` | Kartentitel, Fließtext | `Trebuchet MS` / `Gill Sans` |
| `--font-mono` | Ids, Status, **die drei Zahlen** | `Courier New`: die Schreibmaschine der Laufkarte |
| Radius, Schatten, Verlauf | keine | Karton hat Kanten |

Kontrast (hell / dunkel, `contrast.py`): Text auf Tafel 8,2 / 12,4; gedämpft 6,0 / 7,4; Titel auf Karton
12,0 / 8,5; gedämpft auf Karton 4,6 / 5,7; Id auf Kartenkopf 9,6 / 6,4; Titel auf rotem Karton 9,3 / 8,8;
Weiß auf rotem Kopf 7,4 / 6,4; Titel auf gelbem Karton 11,7 / 6,7; Kopf des gelben Kartons 7,4 / 7,6; rote
Zahl 4,9 / 7,3 (groß); gelbe Zahl 7,5 / 11,2 (groß); Ids in den Fokus-Listen 5,3 / 4,8 und 5,3 / 7,3.

Dunkel: Tafel `#1b2422`, Karton `#4a3f2e` mit heller Tinte, roter Karton `#6a2a25`, gelber `#5f4d14`; die
Köpfe bleiben kräftig (`#b0301f`, `#d2ab2c` mit dunkler Schrift).
