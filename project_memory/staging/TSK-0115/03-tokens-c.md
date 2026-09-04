# 03-c — Token-Blatt C: Leitsystem

Werte stehen genau einmal: `directions.C_TOKENS` und `C_RULES` in `directions.py`.

| Token | Rolle | Grund |
|---|---|---|
| `--board` | die Wand, an der die Schilder hängen | warmes Mittelgrau — weder das Papier der Finanzseite noch die kühle Tafel aus Phase 1 |
| `--slot` | Steckleiste, leere Felder oben, Fokus-Listen | eine Stufe dunkler als die Wand |
| `--card` | das weiße Schildfeld | Weiß trägt schwarze Schrift am besten |
| `--ink`, `--ink-2` | Schrift; **Kopfbänder** der Slots (Wandfarbe auf Tinte, invertiert) | schwarz wie Beschilderung; das Kopfband ist das Schild über der Leiste |
| `--rule` | linke Kante gewöhnlicher Karten (10 px), leere Slot-Köpfe | die neutrale Kante |
| `--stop`, `--stop-ink` | **Stoppfeld**: die Zahl oben als Feld, die Kante und die Flagge einer blockierten Karte, weiße Schrift | Rot mit Weiß ist das Halt-Schild |
| `--you`, `--you-ink` | **Warnfeld**: Gelb mit schwarzer Schrift — wartet auf dich | Gelb trägt keine weiße Schrift; darum schwarz, und darum tragen Ids in der Liste das Feld statt der Farbe |
| `--go`, `--go-ink` | **Richtungsfeld**: Grün mit Weiß — in flight | die dritte Zahl bekommt ein Feld, aber ein ruhiges; bei null ist jedes Feld grau |
| `--font-head`, `--font-body`, `--font-mono` | alles — **eine** Schrift, Ids mit Tabellenziffern | `Verdana` / `Tahoma` / `Helvetica Neue`: die humanistische Beschilderungsschrift; eine Schrift, weil ein Schild eine hat |
| Radius, Schatten, Verlauf | keine; Felder bis an den Rand | das ist, was ein Feld von einer Kachel trennt |

Kontrast (hell / dunkel): Text auf Wand 14,7 / 15,2; gedämpft 6,6 / 8,3; Text auf Feld 18,9 / 12,1; gedämpft
auf Feld 8,5 / 6,6; Weiß auf Stopp 6,5 / 5,4; Schwarz auf Gelb 11,2 / 11,2; Weiß auf Grün 6,3 / 5,3; Kopfband
14,7 / 15,2.

Dunkel: Wand `#1c1c1a`, Felder `#2e2e2b`, Stopp `#c2372b`, Grün `#167a57`, Gelb bleibt `#f2c200` mit
schwarzer Schrift.

Preis, benannt: die drei Farbfelder oben sind das, was einer Kachelwand am nächsten kommt; die Tinte
`#111111` ist derselben Klasse wie die der Finanzseite.
