# 03-e — Token-Blatt E: Modern, Fläche

Dieselben Token wie D (`directions.M_TOKENS_LIGHT`, `M_TOKENS_DARK`, `M_FONTS`); der Unterschied liegt
in `E_RULES`: **das Signal ist die Fläche selbst.**

| Token | Rolle in E | Grund |
|---|---|---|
| `--stop`, `--you`, `--go` + `--*-ink` (Weiß) | die drei Zahlen oben als **volle Farbfelder** mit weißer Schrift; eine Null ist ein neutrales Feld (`--slot`) mit gedämpfter Zahl | die Signalgebung aus C, die dem Nutzer gefiel — flach, 4 px Radius, ohne Verlauf, Schatten oder Piktogramm |
| `--stop-tint`, `--you-tint`, `--go-tint` | Grund einer **signalisierten Karte** und der Zeilen in den Fokus-Listen | die Karte ist getönt, nicht gefüllt: Titel bleibt Tinte (15,7 / 14,5), die Flagge ist ein kleines gefülltes Etikett (3 px Radius, rechteckig — kein Pill) |
| `--stop-text`, `--you-text`, `--go-text` | Id und Flaggentext auf der Tönung | gemessen 5,5 / 5,7, 4,8 / 7,7, 4,8 / 7,7 |
| Grund, Karte, Tinte, Linien, Schrift, Radius | wie D | ein Blatt, zwei Charakterregeln — die Wahl des Nutzers ist die Dimension, nicht das System |

Kontrast (hell / dunkel): Weiß auf Rot 4,8 / 4,8; Weiß auf Bernstein 5,4 / 5,4; Weiß auf Petrol 5,6 / 5,6;
blockiert-Text auf Tönung 5,5 / 5,7; Bernstein-Text auf Tönung 4,8 / 7,7; Petrol-Text 4,8 / 7,7; Tinte auf
roter Tönung 15,7 / 14,5; auf gelber 16,6 / 12,8. Weiß auf Rot ist mit 4,8 der knappste Wert des Pakets —
darum ist die Beispielzeile im Feld 0,8 rem und nicht kleiner.

Preis, benannt: drei volle Farbfelder oben sind der Punkt, an dem E einer Kachelwand am nächsten kommt —
was trennt, steht in `07-modern.md` (Farbe nur als Signal, eine Null ist grau, kein Radius über 4 px, kein
Schatten, und unterhalb der drei Zahlen ist nichts farbig, was nicht blockiert ist oder auf dich wartet).
