# 03-b — Token-Blatt B: Blueprint

Werte stehen genau einmal: `directions.B_TOKENS` und `B_RULES` in `directions.py`.

| Token | Rolle | Grund |
|---|---|---|
| `--board`, `--card` | Zeichenpapier; Karten haben denselben Grund | eine Zeichnung hat eine Fläche und Linien darauf — keine zweite Fläche |
| `--slot` | `transparent` — ein Slot ist ein gezogener Rahmen (`border: 1px solid var(--rule)`), leer gestrichelt | Rahmen statt Flächen ist der Charakter |
| `--ink`, `--rule` | **die eine Tinte**: Text, Rahmen, Kartenkonturen, Reiterlinie — Preußischblau | eine Zeichnung hat eine Tintenfarbe; Blau ist hier nicht Akzent, sondern alles |
| `--ink-2` | gedämpfte Beschriftung | verdünnte Tinte |
| `--stop`, `--stop-ink`, `--hatch` | Rotstift: Rahmen 2 px, Kopf gefüllt, **Schraffur** auf dem Kartenkörper — blockiert | in der Zeichnung wird gestrichen und schraffiert; die Schraffur ist ein Muster, nicht nur eine Farbe |
| `--you`, `--you-ink` | Revisions-Ocker: Rahmen 2 px und Kopf gefüllt, schwarze Schrift — wartet auf dich | die Revisionswolke; hell nimmt die Zahl `#8a5a00`, weil Ocker auf Weiß zu hell wäre |
| `--font-head`, `--font-body` | Titel, Zahlen (Versalien), Text | `Candara` / `Corbel` / `Gill Sans`: humanistisch, offen, wie Normschrift ohne Schablone |
| `--font-mono` | Slot-Köpfe, Ids, Eyebrow — **gesperrt, Versalien** | `Lucida Console`: die Zeichenbeschriftung |
| Radius, Schatten, Verlauf | keine | Linien haben keinen Radius |

Kontrast (hell / dunkel): Tinte auf Papier 10,7 / 12,6; gedämpft 5,2 / 7,5; Weiß auf Rotstift 6,7 / 7,9;
Schwarz auf Ocker 10,4 / 10,4; rote Zahl 6,2 / 6,3 (groß); Ocker-Zahl 5,5 / 8,6 (groß).

Dunkel: die Blaupause — Grund `#0f2a4a`, Tinte und Rahmen `#e8f0f8`, Rotstift `#ff8a70` mit dunkler
Schrift, Schraffur heller.

Preis, benannt: das Papier `#f4f7fa` ist der eine Wert, der der Finanzseite (`#FBFBF9`) nahe bleibt.
