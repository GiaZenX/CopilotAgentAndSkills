# Humanizer — Vorher/Nachher an einem Produkttext (TSK-0111, FR-0072)

**Für den Nutzer.** FR-0072 nennt als Test: ein Vorher/Nachher an echter Shop-Kopie, und das Urteil
ist deins. Diesen Text hier hat der Umsetzer erfunden, damit dein Live-Shop nicht gelesen werden
musste; er ist so gebaut, wie ein Sprachmodell einen Produkttext typischerweise schreibt. Wenn du
willst, dass die eigentliche Probe an deinem echten Text läuft: gib dem Lead einen Produkttext, die
Rolle wendet den Skill an, und du liest beide Fassungen.

Die Frage an dich ist nur eine: **Welche der beiden Fassungen klingt nach einem Menschen, der das
Produkt kennt — und würdest du die zweite so in den Shop stellen?** Was dir an der zweiten fehlt
oder zu viel ist, ist der Befund für die nächste Runde.

*Stand: Nacharbeit 3.* Die erste Nachher-Fassung dieses Paars hatte Dinge geändert, die der Skill
nicht ändern darf — „Getränke" wurde zu „Tee" und „Wasser", ein „ganzer Arbeitstag" zu „durch den
Tag" mit einer erfundenen Bedingung, „nahezu jeden gängigen" zu „die meisten" (Befund B4 des
Prüfers). Danach führten zwei Fassungen ihre Abweichungen von der Vorlage auf, und beide waren
unvollständig — weil die Liste aufgezählt war, was jemandem aufgefallen ist, statt aus den beiden
Texten abgeleitet (Befunde N3 und B2 des Prüfers). Diese Fassung zählt nicht mehr auf: sie zerlegt
die Vorlage vollständig in Abschnitte, stellt jedem seinen Platz in der Nachher-Fassung gegenüber,
und ein Skript rechnet nach, dass nichts fehlt.

---

## Vorher (so geliefert, unverändert)

> In der heutigen schnelllebigen Welt ist eine zuverlässige Trinkflasche nicht nur ein praktisches
> Accessoire, sondern ein echter Begleiter für jeden Tag. Tauchen Sie ein in die Welt der
> hochwertigen Isolierflaschen und entdecken Sie ein Produkt, das Design, Funktionalität und
> Nachhaltigkeit nahtlos miteinander verbindet. Die innovative Doppelwand-Vakuumisolierung kann Ihre
> Getränke bis zu 12 Stunden warm und bis zu 24 Stunden kalt halten — ideal für Büro, Sport und
> Reise. Darüber hinaus besteht die Flasche aus robustem Edelstahl 18/8, der möglicherweise auch bei
> intensiver Nutzung eine lange Lebensdauer gewährleisten kann. Mit einem Fassungsvermögen von bis
> zu 750 ml bietet dieses einzigartige Modell ausreichend Kapazität für einen ganzen Arbeitstag —
> ohne dabei sperrig zu wirken. Des Weiteren ermöglicht der BPA-freie Deckel mit Silikondichtung
> ein absolut auslaufsicheres Handling: Ihre Tasche bleibt trocken. Die Reinigung des Deckels kann
> bequem in der Spülmaschine erfolgen, während die Reinigung der Flasche von Hand vorgenommen
> werden sollte. Zudem passt der Artikel mit einem Durchmesser von 7,3 cm in nahezu jeden gängigen
> Getränkehalter — perfekt für unterwegs. Mit einem Gewicht von nur 380 g ist diese Lösung außerdem
> leicht, kompakt und stilvoll. Zusammenfassend lässt sich sagen, dass diese Isolierflasche eine
> optimale Kombination aus Qualität, Design und Alltagstauglichkeit darstellt. Sind Sie bereit,
> Ihren Alltag auf das nächste Level zu heben?

## Nachher (der Skill angewendet, wie eine Rolle es täte: Fakten unverändert, Ton „sachlich")

> Die Isolierflasche fasst 750 ml. Das reicht schon für einen ganzen Arbeitstag, und sperrig wirkt
> sie dabei nicht. Sie ist doppelwandig vakuumisoliert und hält Getränke bis zu 12 Stunden warm und
> bis zu 24 Stunden kalt, im Büro, beim Sport und auf Reisen. Die Flasche besteht aus Edelstahl 18/8,
> der auch intensive Nutzung lange aushalten sollte. Der Deckel ist BPA-frei und hat eine
> Silikondichtung; die Flasche läuft nicht aus, Ihre Tasche bleibt trocken. Deckel in die
> Spülmaschine, die Flasche von Hand. Mit 7,3 cm Durchmesser passt sie in nahezu jeden gängigen
> Getränkehalter, und sie wiegt 380 g.

---

## Was gemessen wurde (die Zählungen aus dem Skill, mit einem Skript über beide Texte)

Die Tabelle ist die Arbeitsweise des Skills: erst zählen, dann umschreiben, dann noch einmal zählen.
Gezählt hat `_round-scratch/TSK-0111/measure_pair.py` (Fassung der Nacharbeit 2; ein
Wegwerf-Instrument der Runde, nicht Teil des Kits) über `before.txt`/`after.txt` daneben. Jede
Zeile trägt eine Regel, und die Spalte „Regel" nennt sie so, wie das Instrument sie heißt; wo das
Instrument zwei Zahlen in einer Zeile druckt, stehen hier zwei Zeilen.

| Eigenschaft (Nummer im Skill) | Regel (Name im Instrument) | Vorher | Nachher |
|---|---|---|---|
| Wörter | Whitespace-Token | 209 | 97 |
| Sätze | Satzende an `. ! ?` vor Großbuchstabe | 11 | 7 |
| Satzlängen in Wörtern (1) | Whitespace-Token je Satz | 21 22 25 20 24 16 20 19 15 16 11 — kürzester 11, längster 25, keiner unter 8 | 5 13 25 13 17 8 16 — kürzester 5, längster 25, einer unter 8 |
| Dreier-Folgen gleich langer Sätze (1) | drei aufeinanderfolgende Sätze mit Spanne ≤ 5 | 7 | 0 |
| Em-Dashes (2, G4) | Zeichen `—` zählen | 3 (unspatiiert) | 0 |
| Spatiierte En-Dashes (2, G4) | Zeichenfolge ` – ` zählen | 0 | 0 |
| Doppelpunkte (2) | Zeichen `:` zählen | 1 | 0 |
| Abschwächer und Modalverben auf Fakten (3, G5) | `HEDGE` — kann, können, könnte, möglicherweise, unter Umständen, potenziell, gegebenenfalls, in vielen Fällen, sollte | 5 („kann" ×3, „möglicherweise", „sollte") | 1 („sollte" — Punkt 2 unten) |
| Satzanfänge mit Diskursmarker (4, G6) | `MARKER` | 4 („Darüber hinaus", „Des Weiteren", „Zudem", „Zusammenfassend") | 0 |
| „nicht nur … sondern" (5b, G2) | Zeichenkette | 1 | 0 |
| Dreier-Aufzählungen „x, y und z" (5a) | `TRIPLET` — je Glied ein Vorwort erlaubt | 4 | 1 („im Büro, beim Sport und auf Reisen" — Punkt 15 unten) |
| Wertende Adjektive (7) | `EVALUATIVE` — elf Wortstämme | 10 (zuverlässig, hochwertig, nahtlos, innovativ, ideal, robust, einzigartig, perfekt, stilvoll, optimal) | 0 |
| Namen für dasselbe Produkt (8) | `PRODUCT_NAME` — verschiedene Lemmata, Plural gefaltet | 9 (Trinkflasche, Accessoire, Begleiter, Isolierflasche, Produkt, Flasche, Modell, Artikel, Lösung) | 2 (Isolierflasche, Flasche) |
| Funktionsverb-Konstruktionen (G1) | `LIGHT_VERB` | 3 („ermöglicht", „erfolgen", „vorgenommen") | 0 |
| Modalpartikel (G3) | `PARTICLE` | 0 | 1 („schon") |
| Anglizismen (G2) | `ANGLICISM` | 2 („Handling", „Level") | 0 |
| Frage an den Leser (6) | `?` zählen | 1 | 0 |

**Was unverändert ist — nachgezählt, nicht behauptet** (Zeile `facts present` des Instruments,
beide Texte): jede Zahl als Ziffer (750 ml, 12 Stunden, 24 Stunden, 18/8, 380 g, 7,3 cm), jede
Eigenschaft (BPA-frei, Silikondichtung, Deckel in die Spülmaschine, Flasche von Hand, läuft nicht
aus und die Tasche bleibt trocken, intensive Nutzung), jeder Referent (Getränke bleiben Getränke,
die Flasche bleibt die Flasche, der Arbeitstag bleibt ein ganzer, „nahezu jeden gängigen"
Getränkehalter, die drei Einsatzorte Büro, Sport, Reise) und beide „bis zu" auf den Stunden.

**Was die Nachher-Fassung anders sagt als die Vorlage — die Vorlage vollständig, Abschnitt für
Abschnitt.** Die Tabelle unten zerlegt die Vorlage in Abschnitte und stellt jedem gegenüber, was im
Nachher-Text an seiner Stelle steht. Die Spalte „Art" sagt, was mit ihm passiert ist, und kennt
genau drei Werte: **unverändert** (dieselbe Aussage, andere Worte), **Abweichung → n** (der Satz
behauptet etwas anderes als vorher, erklärt in Punkt n darunter) und **gestrichen → n** (steht im
Nachher-Text nicht mehr).

Dass nichts fehlt, rechnet das Skript `devlist.py` neben dieser Datei nach — es gehört nicht
zum Kit. Ob das Urteil in der Spalte „Art" stimmt, entscheidet es nicht: das liest du an den
beiden Zellen nebeneinander ab, und dafür stehen sie nebeneinander.

| Nr. | Vorlage | Nachher | Art |
|---|---|---|---|
| 1 | In der heutigen schnelllebigen Welt ist eine zuverlässige Trinkflasche nicht nur ein praktisches Accessoire, sondern ein echter Begleiter für jeden Tag. | (nichts) | gestrichen → 9 |
| 2 | Tauchen Sie ein in die Welt der hochwertigen Isolierflaschen und entdecken Sie ein Produkt, das Design, Funktionalität und Nachhaltigkeit nahtlos miteinander verbindet. | (nichts) | gestrichen → 10 |
| 3 | Die innovative Doppelwand-Vakuumisolierung | Sie ist doppelwandig vakuumisoliert | Abweichung → 7, 8 |
| 4 | kann Ihre Getränke bis zu 12 Stunden warm und bis zu 24 Stunden kalt halten | und hält Getränke bis zu 12 Stunden warm und bis zu 24 Stunden kalt | Abweichung → 3 |
| 5 | — ideal für Büro, Sport und Reise. | , im Büro, beim Sport und auf Reisen. | Abweichung → 7, 15 |
| 6 | Darüber hinaus | (nichts) | gestrichen → 11 |
| 7 | besteht die Flasche aus robustem Edelstahl 18/8, | Die Flasche besteht aus Edelstahl 18/8, | Abweichung → 7 |
| 8 | der möglicherweise auch bei intensiver Nutzung eine lange Lebensdauer gewährleisten kann. | der auch intensive Nutzung lange aushalten sollte. | Abweichung → 2 |
| 9 | Mit einem Fassungsvermögen von bis zu 750 ml | Die Isolierflasche fasst 750 ml. | Abweichung → 1 |
| 10 | bietet dieses einzigartige Modell ausreichend Kapazität | Das reicht | Abweichung → 7, 8 |
| 11 | für einen ganzen Arbeitstag | schon für einen ganzen Arbeitstag, | Abweichung → 14 |
| 12 | — ohne dabei sperrig zu wirken. | und sperrig wirkt sie dabei nicht. | unverändert |
| 13 | Des Weiteren ermöglicht | (nichts) | gestrichen → 11 |
| 14 | der BPA-freie Deckel mit Silikondichtung | Der Deckel ist BPA-frei und hat eine Silikondichtung; | unverändert |
| 15 | ein absolut auslaufsicheres Handling: | die Flasche läuft nicht aus, | Abweichung → 6 |
| 16 | Ihre Tasche bleibt trocken. | Ihre Tasche bleibt trocken. | unverändert |
| 17 | Die Reinigung des Deckels kann bequem in der Spülmaschine erfolgen, | Deckel in die Spülmaschine, | Abweichung → 4, 7 |
| 18 | während die Reinigung der Flasche von Hand vorgenommen werden sollte. | die Flasche von Hand. | Abweichung → 5 |
| 19 | Zudem | (nichts) | gestrichen → 11 |
| 20 | passt der Artikel mit einem Durchmesser von 7,3 cm in nahezu jeden gängigen Getränkehalter | Mit 7,3 cm Durchmesser passt sie in nahezu jeden gängigen Getränkehalter, | Abweichung → 8 |
| 21 | — perfekt für unterwegs. | (nichts) | gestrichen → 12 |
| 22 | Mit einem Gewicht von nur 380 g | und sie wiegt 380 g. | Abweichung → 7 |
| 23 | ist diese Lösung außerdem leicht, kompakt und stilvoll. | (nichts) | gestrichen → 12 |
| 24 | Zusammenfassend lässt sich sagen, dass diese Isolierflasche eine optimale Kombination aus Qualität, Design und Alltagstauglichkeit darstellt. | (nichts) | gestrichen → 13 |
| 25 | Sind Sie bereit, Ihren Alltag auf das nächste Level zu heben? | (nichts) | gestrichen → 13 |

Und die Punkte, auf die die Spalte „Art" verweist:

1. **Kapazität: aus einer Spanne wird eine Zahl.** „Fassungsvermögen von bis zu 750 ml" → „fasst
   750 ml". Der Zug G5 des Skills an seinem eigenen Beispiel: eine Kapazität ist keine Spanne. Die
   Fassung setzt voraus, dass der Katalog 750 ml sagt; sagt der Katalog selbst „bis zu", bleibt es
   stehen.
2. **Haltbarkeit: aus zwei Abschwächern wird einer.** „der möglicherweise … gewährleisten kann" →
   „der auch intensive Nutzung lange aushalten sollte". Zwei Abschwächer auf einer Behauptung
   (Eigenschaft 3), jetzt einer. Der Skill streicht keine Behauptung, er nimmt den Stapel weg; ob
   die Aussage überhaupt in den Text gehört, entscheidet der Katalog.
3. **Leistung: „kann" fällt weg.** „kann Ihre Getränke … halten" → „hält Getränke …". Das „kann"
   auf einer Leistungsaussage ist G5; die Spanne („bis zu") bleibt, die Leistung wird im Indikativ
   behauptet. Wenn die Isolierung das nur unter Bedingungen leistet, gehört die Bedingung in den
   Satz — der Skill sagt das selbst.
4. **Deckelreinigung: aus einer Erlaubnis wird eine Anweisung.** „Die Reinigung des Deckels kann …
   in der Spülmaschine erfolgen" → „Deckel in die Spülmaschine". G1 (Funktionsverb weg) und G5
   zusammen. Der Sachverhalt — spülmaschinengeeignet — ist derselbe; die Sprechhaltung nicht.
5. **Flaschenreinigung: aus einer Empfehlung wird eine Anweisung.** „während die Reinigung der
   Flasche von Hand vorgenommen werden sollte" → „die Flasche von Hand". Derselbe Zug wie in 4. Wer
   die Empfehlung als Empfehlung will, schreibt „die Flasche besser von Hand" — das ist eine Frage
   an die Inhaltsrichtlinien.
6. **Auslaufsicherheit: drei Dinge auf einmal.** „ermöglicht … ein absolut auslaufsicheres
   Handling" → „die Flasche läuft nicht aus". Der Anglizismus „Handling" (G2) und der leere
   Intensivierer „absolut" (7) sind weg — und die Zuschreibung ebenfalls: die Vorlage sagt, der
   Deckel *ermöglicht* die Dichtheit, der Nachher-Text sagt nur noch, dass die Flasche nicht
   ausläuft. Wenn die Ursache im Text stehen soll, gehört sie hingeschrieben.
7. **Wertende Beiwörter ohne eigene Tatsache sind gestrichen:** „innovative", „robustem",
   „einzigartige", „ideal", „bequem" und das „nur" vor 380 g. Das ist Eigenschaft 7, und der Text
   behauptet danach weniger als vorher. Steht eines davon in deinen Inhaltsrichtlinien, gehört es
   zurück — zusammen mit der Tatsache, die es trägt.
8. **Ein Ding, ein Name.** „dieses einzigartige Modell" und „der Artikel" verschwinden, und aus
   „die innovative Doppelwand-Vakuumisolierung" wird die Flasche selbst („sie ist doppelwandig
   vakuumisoliert"). Eigenschaft 8; die Zeile `PRODUCT_NAME` der Tabelle oben zählt den Zug.
9. **Gestrichen: der Eröffner** („In der heutigen schnelllebigen Welt …"). Er trägt keine Tatsache,
   er trägt die Figur „nicht nur … sondern" (5b) und drei Wertungen.
10. **Gestrichen: die Einladung** („Tauchen Sie ein …", „Design, Funktionalität und Nachhaltigkeit
    nahtlos"). Werbeanrede, ein Dreier und zwei Wertungen, kein Fakt darin.
11. **Gestrichen: die Diskursmarker** „Darüber hinaus", „Des Weiteren", „Zudem" (Eigenschaft 4).
    Sie verbinden nichts, was ohne sie nicht zusammenhinge.
12. **Gestrichen: die Nachsätze ohne Tatsache** — „perfekt für unterwegs" und „ist diese Lösung
    außerdem leicht, kompakt und stilvoll" (Eigenschaft 7). Hinter „leicht" steht mit 380 g eine
    Zahl im Text, hinter „kompakt" und „stilvoll" steht keine. Wenn die Inhaltsrichtlinien Stil
    behaupten wollen, ist das eine Frage an sie, nicht an den Skill.
13. **Gestrichen: die Schluss-Zusammenfassung und die Schluss-Frage** (Eigenschaften 4 und 6). Die
    Zusammenfassung wiederholt nur, die Frage verlangt vom Leser eine Antwort, die der Text nicht
    braucht.
14. **Eingefügt: die Modalpartikel „schon"** („Das reicht schon für einen ganzen Arbeitstag"). G3 —
    die Zeile `PARTICLE` der Tabelle oben zählt sie.
15. **Nicht geändert, obwohl die Zählung ihn sieht: der Dreier.** „im Büro, beim Sport und auf
    Reisen" bleibt ein Dreier, weil es drei SIND — die Einsatzorte der Vorlage. Eigenschaft 5a
    fragt genau das („ask whether there ARE three"), und die Zählung zeigt den Dreier ehrlich als 1.

Zur `HEDGE`-Zeile der Tabelle: 5 → 1 sind vier entfernte Abschwächer, und die Punkte oben erklären
alle vier — Nr. 2 (zwei davon: „möglicherweise", „kann"), Nr. 3 („kann"), Nr. 4 („kann"), Nr. 5
(„sollte"); das „sollte" in Nr. 2 ist der eine, der steht.

**Was der Skill hier NICHT belegt:** dass die zweite Fassung dir gefällt. Die Zählungen zeigen, dass
sich die gemessenen Eigenschaften bewegt haben; ob das Ergebnis nach dir klingt, sagt nur dein
Lesen. Und die Instrumente dieser Runde — das Zählskript und `devlist.py` — sind ausdrücklich nicht
Teil des Kits (DEC-0056: ein Prosa-Skill für einen Prosa-Fehler). Die Rolle zählt von Hand; die
Skripte haben nur diese Tabellen ehrlich gemacht.
