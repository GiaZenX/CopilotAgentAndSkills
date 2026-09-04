# 03 — Visuelles System: die Plantafel (Phase-1-Blatt — abgelöst, siehe unten)

> **Stand nach DEC-0065 (6):** dieses Blatt las der Nutzer als zu nah an der Finanzseite von TSK-0109
> (welche sieben Werte gleich waren: `06-directions.md`). Es bleibt als Vergleich liegen; zur Wahl stehen
> `03-tokens-a.md`, `03-tokens-b.md`, `03-tokens-c.md`. Struktur, Signatur „überstehender Kartenkopf" und
> die Verworfen-Liste unten gelten weiter.

Die Werte stehen genau einmal: im `:root`-Block von `make_mockups.STYLE` (hell) und im
`@media (prefers-color-scheme: dark)`-Block darunter. Dieses Blatt trägt Namen, Rolle und Grund, keine
Hexwerte — Phase 2 trägt den Block nach `board._STYLE`, und dann ist **der** der Ort.

## Richtung, in einem Satz

**Eine T-Karten-Plantafel, kein Cockpit.** Die Welt des Gegenstands ist die Werkstatt-Plantafel:
Steckleisten (Slots) je Zustand, eine Karte je Vorgang, deren **Kopf** aus der Leiste herausschaut
und sagt, was sie ist, während der Körper erst beim Herausziehen (Klick → Akte) lesbar wird. Das ist
der physische Vorfahr des Kanban und kodiert die Mechanik der Seite selbst: Kopf = Fläche,
Körper = Akte. Das Finanz-Dashboard (TSK-0109) ist das Kassenbuch; die beiden Seiten eines Kits sind
Geschwister mit derselben Zurückhaltung, nicht Zwillinge — anderes Objekt, andere Signatur, andere
Schrift.

## Die Signatur: der überstehende Kartenkopf

`.card .head` überragt den Kartenkörper um je 4 px (negative Ränder), gefüllt in Tinte, Id in
Festbreite. Der Kopf trägt die **einzige** Farbe, die eine Karte je bekommt: rot gefüllt, wenn sie
blockiert ist; blau gefüllt, wenn sie auf den Nutzer wartet. Alles andere ist Tinte auf Karton. Man
sieht die drei Karten, die zählen, aus der Entfernung — und sonst nichts, was nach Aufmerksamkeit ruft.

## Token, mit Rolle

| Token | Rolle | Grund |
|---|---|---|
| `--board` | Seitengrund | kühles, helles Grau: die Magnettafel. Bewusst nicht das cremefarbene Papier (`frontend-design`, KI-Standard 1) und nicht Schwarz (Standard 2) |
| `--slot` | Grund eines Slots, der Fokus-Listen, der Warnbanner | die Steckleiste: eine Nuance dunkler als die Tafel, so dass Karten (weiß) sich abheben, ohne Schatten |
| `--card` | Kartenkörper, Knoten der Bäume, Akte | Karton |
| `--ink`, `--ink-2` | Text; Kartenköpfe; gedämpfte Beschriftungen | Tinte, ein Wert; die zweite Stufe für alles, was Beiwerk ist |
| `--rule` | Konturen (1 px `box-shadow`, kein `border`, damit nichts springt), Führungslinien der Bäume | die Kante der Karte |
| `--you` | **der eine Akzent**: „waiting on you", jeder Fokusrahmen, jeder Link, jeder Id-Knopf | Blau heißt auf dieser Seite immer „du handelst" — anklicken oder entscheiden. Kein Grün für „gut": die Seite lobt nicht |
| `--stop` | „blocked": Zahl, Kartenkopf, Ids in der Fokus-Liste, der rote Strich über „Unassigned" und der Warnbanner-Rand, verspätete Meilensteine | erscheint nur, wenn etwas hängt |
| `--font-head` | Kartenköpfe (Flaggen), Sektions- und Reitertitel, die drei Zahlen | `Bahnschrift SemiCondensed` (Windows) / `Avenir Next Condensed` (macOS) / `Arial Narrow`: die schmale Etikettenschrift eines Beschriftungsgeräts, wie sie auf T-Karten klebt. Systemschrift, weil das Kit keine Netzanfrage erlaubt (gemessen: `test_board.test_the_page_carries_no_event_handler_and_no_link_out_of_itself`) |
| `--font-body` | Titel, Fließtext, Akte | `Segoe UI` / `system-ui`: neutral |
| `--font-mono` | Ids, Status-Werte, Datumsangaben auf dem Lineal | das, was man abtippt oder in einen Befehl kopiert |
| `--s1`…`--s4` | 8 / 16 / 24 / 40 px | eine Skala; Sektionen trennt `--s3`, Karten `--s1` |

Typografie: die drei Zahlen 2,6 rem in `--font-head` mit Tabellenziffern; Sektionsköpfe 1,25 rem
(erster Buchstabe groß über `::first-letter`, weil `backlog_tree._LABELS` klein schreibt und die
Namen dort bleiben sollen); Slot-Köpfe Versalien, gesperrt, in `--ink-2`.

Hell/dunkel: allein über `prefers-color-scheme`. Im Dunkeln wird die Tafel anthrazit, die Karte
dunkelgrau, der Kartenkopf **hell** auf dunkler Karte (invertiert, damit er weiter der Kopf ist),
Akzent und Alarm heller, damit die Kontraste halten. Gesichtet: `*-1280-dark.png` aller vier Entwürfe.

Bewegung: **keine.** Die Seite ist ein Bericht; die Fokus-Schalter wechseln Zustand, nicht Animation.

Fokus: `aria-pressed` auf der gedrückten Zahl (Tinte gefüllt, Schrift auf Tafelgrund), Tafel dahinter
auf 22 % Deckkraft; `:focus-visible` überall in `--you`.

Mobil (≤ 720 px): die drei Zahlen nebeneinander ohne Beispielzeile; Slots untereinander in voller
Breite, leere Slots verschwinden und die Zeile „no cards in …" nennt sie alle; Fokus-Listen einspaltig;
Meilensteine untereinander.

## Verworfen, mit Grund

- **KPI-Kacheln mit Radius 14 px, Schatten, Farbverlauf, Pills** — das ist `progress.dashboard.template.html`
  heute und die Antwort auf jeden Dashboard-Auftrag; jede Zahl gleich wichtig. Verworfen für drei Zahlen auf
  einer Linie.
- **Abfahrtstafel (Fallblatt, bernstein auf schwarz)** für „in flight / delayed": hübsch, aber exakt
  KI-Standard 2 (dunkler Grund, ein Neonakzent) und eine Metapher, die „verspätet" verspricht, wo der Kernel
  keine Fristen kennt. Verworfen.
- **Karteikarte mit roter Kopflinie** (DIN-A7-Karteikarte): das Rot wäre auf jeder Karte und dem Alarm
  genommen. Verworfen; der Kopf ist Tinte, Rot bleibt „blockiert".
- **Ampelfarben je Status** (grün fertig, gelb in Arbeit): die Spalte sagt den Status schon; Farbe je Status
  macht die Tafel bunt und die drei Karten, die zählen, unsichtbar. Verworfen.
- **Fortschrittsringe / Prozent je Wurzel**: Archiviertes liegt nicht auf der Tafel, ein Anteil wäre falsch.
  Verworfen für Zahlen je Bahn.
- **Broadsheet (Haarlinien, Null-Radius, dichte Spalten)**: Slots sind Flächen, nicht Linien; Radius 2–3 px;
  großzügige Sektionsabstände — der Unterschied steht in den Screenshots.
- **Nummerierte Marker (01/02/03)** an Reitern oder Sektionen: keine Sequenz. Verworfen.
