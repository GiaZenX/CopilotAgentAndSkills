# 03 — Visuelles System: das Journal

Die Werte stehen genau einmal: im `:root`-Block von `finance-dashboard.template.html` (hell) und
im `@media (prefers-color-scheme: dark)`-Block darunter (dunkel). Dieses Blatt trägt die Namen, die
Rolle und den Grund — nicht die Hexwerte, die sonst an zwei Orten alterten.

## Richtung, in einem Satz

**Ein Kassenbuch, kein Cockpit.** Die Welt des Gegenstands ist die deutsche Buchführung: das
Belegjournal mit Linien, Beträge rechtsbündig in Tabellenziffern, der Stempel auf dem Beleg, der
Doppelstrich unter der Summe. Diese Dinge kodieren etwas Wahres über den Inhalt — darum tragen sie
die Gestaltung, und nichts ist Dekoration.

## Die Signatur: der Doppelstrich

In der Buchführung heißt ein einfacher Strich „hier wird addiert", ein Doppelstrich „hier ist die
Summe, abgeschlossen". Genau so auf der Seite: jede Zwischenzahl steht auf einem einfachen Strich,
jede Summe (Überschuss, Summe brutto der gefilterten Liste, Summe der offenen Posten, Überschuss
der EÜR) auf einem Doppelstrich (`border-bottom: 3px double`). Man erkennt die Summe, bevor man
sie liest. Das ist das eine Risiko dieses Entwurfs — eine Finanzseite ohne Kacheln —, und es ist
begründet: der Nutzer hat „weniger überladen, die wichtigen Zahlen direkt sichtbar" verlangt, und
Kacheln sind das, was jede Zahl gleich wichtig aussehen lässt.

## Token, mit Rolle

| Token | Rolle | Grund |
|---|---|---|
| `--paper` | Seitengrund | fast weiß, minimal warm — bewusst **nicht** das cremefarbene `#F4F1EA`-Papier, das die Kalibrierung des frontend-design-Skills als KI-Standard nennt |
| `--ink` | Text, Striche, Balken der Einnahmen | Tinte; ein Wert für alles, was „geschrieben" ist |
| `--ink-2` | Beschriftungen, Nebeninformation | gedämpfte Tinte statt einer zweiten Farbe |
| `--rule`, `--rule-soft` | Linien zwischen Zeilen, Formularunterstriche | die Linien des Journals; die weiche Variante zwischen Buchungszeilen, die harte unter Köpfen |
| `--stamp` | **der eine Akzent**: aktive Filter, Links, Stempel „bezahlt", „gültig", „innerhalb" | die Farbe des Stempelkissens — der Akzent bedeutet immer „abgehakt / anklickbar", nie „Einnahme" |
| `--alarm` | Stempel „mahnen", „ungültig", „überschritten"; Banner; roter Punkt am Reiter | die Farbe des Mahnstempels; erscheint nur, wenn es etwas zu tun gibt |
| `--font-display` | die großen Zahlen, Überschriften ersten Grades, Leerzustands-Sätze | `Bahnschrift` (Windows) / `DIN Alternate` (macOS): eine DIN-Schrift, die Schrift deutscher Formulare — Anlage EÜR inklusive. Systemschrift, weil das Kit keine Netzanfrage erlaubt; der Fallback ist eine schmale Grotesk |
| `--font-body` | Fließtext, Tabellen | `Segoe UI` / `system-ui`: neutral, damit die Display-Schrift die Persönlichkeit trägt |
| `--font-mono` | Beleg-Ids, Rechnungsnummern, Pfade | das, was man abtippt oder sucht, in Festbreite |
| `--s1`…`--s5` | Abstände 8 / 16 / 24 / 40 / 64 px | eine Skala; Sektionen trennt `--s4`, Zeilen `--s1` |
| `--page-max` | 72 rem | eine Spalte; Tabellen mit neun Spalten brauchen die Breite, ein Text 60 rem (`.lead`, `.hint`) |

Typografie: Tabellenziffern (`font-variant-numeric: tabular-nums`) auf dem gesamten `body`, damit
Beträge in jeder Spalte untereinander stehen. Überschriften zweiten Grades sind Versalien mit
Sperrung auf einem Strich — die Rubrikenköpfe des Journals. Die drei Kennzahlen: 2,6 rem Display,
Beschriftung darüber, Quellzeile darunter („aus ledger/2026.csv · 125 bezahlte Zeilen"), weil die
Office-Developer-Regel jede Summe nachrechenbar verlangt.

Stempel (`.stamp`): Versalien, gesperrt, 1,5 px Rahmen in der eigenen Farbe, 3 px Radius — ein
Stempel, nicht ein Pill-Badge; keine Füllung, keine Rotation.

Hell/dunkel: allein über `prefers-color-scheme`, kein Schalter — die Seite hat schon eine
Reiterleiste und eine Filterleiste, ein dritter Bedienstreifen wäre Chrom. Im Dunkeln wird das
Papier nicht schwarz, sondern anthrazit, die Tinte nicht weiß, sondern Papierweiß; der Akzent und
der Alarm werden heller, damit die Kontraste halten.

Bewegung: genau eine — die Füllstandsleisten der Schwellenwache gleiten beim Laden (0,4 s), und nur
unter `prefers-reduced-motion: no-preference`. Alles andere ist Zustand, nicht Animation.

Mobil (≤ 720 px): die drei Zahlen untereinander, die Reiterleiste scrollt seitlich (das angeschnittene
letzte Wort ist die Andeutung — ein Verlauf darüber las sich beim Sichten als Fehler), die
Rechnungsliste behält Datum, Gegenpartei, Brutto, Status; Nummer, Kategorie, Netto, USt und
Zahldatum liegen in der Detailzeile.

## Verworfen, mit Grund

- Kachel-Layout mit Schatten und 14-px-Radius (das Muster von `progress.dashboard.template.html`):
  jede Zahl gleich wichtig, Hierarchie nur über Größe. Verworfen für Striche.
- Farbcodierung Einnahme grün / Ausgabe rot: nimmt dem Alarm seine Farbe. Verworfen für Fettung
  der Einnahmebeträge und gefüllte vs. umrandete Balken.
- Dunkler Grund mit Neonakzent (KI-Standard 2): ein Kassenbuch ist Papier. Verworfen.
- Broadsheet-Look (KI-Standard 3: Haarlinien, Null-Radius, dichte Spalten): die Striche hier sind
  Journallinien in Tintenstärke, es gibt eine Spalte, großzügige Abstände und Radius an Stempeln —
  der Unterschied ist gemessen an den Screenshots, nicht behauptet.
- Nummerierte Marker (01/02/03) an den Reitern: die Reiter sind keine Sequenz. Verworfen.
- Kreisdiagramm nach Kategorie: die EÜR-Tabelle mit der Zeile der Anlage ist die Information, ein
  Kreis wäre ihre Verzierung.
