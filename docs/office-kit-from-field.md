# Was das Office-Kit aus einem echten Betrieb übernehmen sollte

Gemessen am 2026-08-04 an der Kopie von BuyPlugGo (`v2-pilot/BuyPlugGo-KOPIE`, Kit
`2026.07.17-8`, vier Wochen Betrieb, 16 Verfahren, ein Aktenplan über 920 abgelegte Dokumente).
Das Original ist ein laufendes Geschäft und wurde nicht angefasst.

Die Trennlinie dieses Dokuments: **generalisierbar ist, was jeder deutsche Kleinbetrieb braucht.
Spezifisch ist, was BuyPlugGo als Händler braucht.** eBay-, Kaufland- und Shopify-Abläufe, der
Produktkatalog, die Preislisten und die Bildpflege stehen deshalb NICHT auf dieser Liste, so gut
sie im Feld auch funktionieren.

---

## F1 — Der Aktenplan wird gefüllt ausgeliefert (höchster Wert)

**Heute:** das Kit liefert `filing_plan.yaml` mit einer leeren Regelliste aus. `gate_filing`
schlägt darauf fail-closed an — **das erste Dokument, das ein frisch aufgesetztes Office-Projekt
je ablegen will, wird verweigert.** Und weil es ein Kit-Dokument ist, hat es nach der Installation
keinen Schreiber mehr: wer es nicht beim Aufsetzen füllt, kommt nicht mehr heran.

**Aus dem Feld:** BuyPlugGos Baum ist kein Sonderweg, sondern der deutsche Normalfall —

```
archive/1-Finanzen/Rechnungen/<Jahr>/1_Eingangsrechnungen/<Quartal>/<MM>/
archive/1-Finanzen/Rechnungen/<Jahr>/2_Ausgangsrechnungen/<Quartal>/<MM>/
```

mit Dokumentklassen je Knoten (`invoice_incoming`, `credit_note`, `cancellation_storno`,
`purchase_receipt_kaufbeleg`, `differenzbesteuert`, `shipping_receipt`).

**Zu übernehmen:** ein gefüllter DE-Standardaktenplan als Vorlage, den ein Projekt kürzt statt ihn
zu erfinden. Ein Kit, dessen Kernfunktion beim ersten Gebrauch verweigert, ist kein Kit.

## F2 — Aufbewahrung ist ein Feld mit Rechtsgrundlage und einem Ehrlichkeitsvermerk

**Aus dem Feld,** wörtlich je Knoten:

> `retention: "8y (Belege gem. Paragraph 147 AO — DE-Default; confirm with Steuerberater)"`

und im Kopf der Datei der Vermerk, dass diese Vorgaben **nicht** gegen die tatsächliche Beratung
geprüft sind.

**Zu übernehmen:** beides. Die Frist mit ihrer Rechtsgrundlage — und der Vermerk, dass ein
Standardwert ein Standardwert ist. Das ist im Aktenplan dieselbe Hausregel wie im Code: kein
Kommentar darf Schutz behaupten, den niemand gebaut hat.

## F3 — Benennung als Schema, nicht als Gewohnheit

**Aus dem Feld:** `naming_rule: "YYYY-MM-DD_<counterparty>_<doctype>"`, dazu eine Tabelle je
Dokumentart für die Fälle, die davon abweichen.

**Zu übernehmen:** die Regel als Vorlagenfeld mit der Tabelle daneben. Ohne sie entscheidet jeder
Ablauf neu, wie eine Datei heißt, und nach hundert Dokumenten ist der Bestand unsortierbar.

## F4 — Die Grenze zwischen Eingang und Archiv, als Definition

Das ist die teuerste Erkenntnis im ganzen Repo, weil sie über mehrere Fassungen erarbeitet wurde
(v1.2 → v1.9):

> Der **Eingang** liegt im Wurzelverzeichnis neben dem Archiv, nicht darin, und hat **keine
> Unterordner**. Unklare Fälle wandern nicht in einen Eingangs-Unterordner, sondern in einen Knoten
> **innerhalb** des Archivs (`archive/0-Prüfen/`).

**Der Grund ist mechanisch:** Bewegungen innerhalb des Archivs sind vom Wächter erlaubt. Liegt der
Klärungsknoten im Eingang, muss ein Mensch jede unklare Datei von Hand hinübertragen — ein
Zwischenschritt, den die erste Fassung hatte und der im Betrieb nicht durchgehalten wurde.

**Zu übernehmen:** als Definition in die Vorlage, mit dem Grund. Ein Kit, das nur die Struktur
liefert, lässt jeden Betrieb dieselben zwei Fassungen durchlaufen.

## F5 — Gelöscht wird nie; es gibt eine Quarantäne

**Aus dem Feld** (PROC-0015 und der Aktenplan):

> Dateien, die als überholt oder kaputt erkannt werden, wandern mit **protokolliertem Grund** in
> einen Quarantäneknoten. Das Team löscht nicht. Nur die Inhaberin leert ihn.

**Zu übernehmen:** wörtlich. Bei Geschäftsdokumenten ist ein irrtümliches Löschen nicht
reparierbar, und ein Agent, der löschen darf, wird es irgendwann tun.

## F6 — Zwei Dinge in `.gitignore`, beide aus Schaden gelernt

**(a) Die Unterscheidung, welche Geschäftsdaten versioniert werden.** Aus dem Feld:

> Binäre Dokumente werden **nicht** verfolgt — sie blähen das Repo, und die DSGVO-Löschung nach
> Art. 17 muss möglich bleiben, denn Git-Historie ist für immer. **Das Ledger bleibt verfolgt:**
> die gesetzliche Aufbewahrung geht der Löschung vor.

Diese Abwägung ist richtig und trifft jeden Betrieb, der Belege und Buchhaltung im selben Repo
hält. Sie gehört ins Kit, nicht in jedes Projekt neu.

**(b) Eine gemessene Falle:** `dir/` schließt das Verzeichnis aus, und Git kann eine Datei darin
danach **nicht** wieder einschließen. Damit waren die Ordner-Seeds des Kits still unverfolgt und
ein frischer Klon kaputt. Richtig ist `dir/*` plus Negation.

**Zu übernehmen:** beides, mit der Begründung — sonst „vereinfacht" die nächste Hand es zurück.

## F7 — Zwei wiederkehrende Verfahren sind Büroarbeit, nicht Handel

Von den 16 Verfahren sind die meisten händlerspezifisch. Diese zwei nicht:

- **Eingangsroutine** (PROC-0005): eine Schleife je Datei — öffnen, klassifizieren, umbenennen,
  buchen / zur Klärung parken / in Quarantäne. Das ist der Kernablauf jedes Büros.
- **Unabhängige Projektprüfung** (PROC-0010): eine wiederkehrende, **read-only** Stichprobe über
  Ablage, Ledger und Berichte, die gegen die Quellen reproduziert. Im Feld hat sie 435 von 435
  Quellen byte-identisch bestätigt und dabei zwei Hygienemängel gefunden, die sonst niemand
  gesehen hätte.

**Zu übernehmen:** beide als Verfahrensvorlagen. Besonders die Prüfung — ein Kit, das seine eigene
Arbeit stichprobenweise gegen die Quellen prüft, findet Drift, bevor sie teuer wird.

## F8 — Die Jahresansicht

`dashboards/yearly_overview.html` aus PROC-0014: eine interaktive Jahresübersicht über Einnahmen
und Ausgaben aus dem Ledger. Die Zahlen erzeugt `euer_report.py` bereits; **es fehlt die Sicht.**

Deckt sich mit Abschnitt 5 der Wunschliste (Nachtrag des Users vom 2026-07-31) und mit derselben
Bedingung: die Ansicht gehört nach `generated/`, regenerierbar und **nicht committet** — eine
committete Bilanz wäre eine zweite Wahrheit neben dem Ledger, und das Ledger ist der Beleg. Und
sie muss ihre Quelle und ihren Stichtag nennen.

---

## Stand (2026-09-02, TSK-0107 -- Generation 2, Strom G)

Der Stand gehoert in dieses Dokument, weil die Prosa hier liegt und `FR-0002` nur den Zustand
traegt. Was gebaut ist, ist gegen den ausgelieferten Baum gemessen; jede Zeile nennt die Stelle,
nicht den Satz.

| Punkt | Stand | Wo |
|---|---|---|
| F1 | **gebaut** (FR-0031 / TSK-0102) | der Aktenplan wird mit Regelentwurf statt leer uebergeben |
| F2 | **gebaut** | `filing_plan.yaml`: `retention` traegt Spanne UND Rechtsgrundlage, dazu der Ehrlichkeitsvermerk (kein primaerer Gesetzestext gelesen). Der Waechter darauf ist `_duties.retention_duties` |
| F3 | **gebaut** | `filing_plan.yaml`: `filename_template` als Schema mit den drei benannten Abweichungen |
| F4 | **gebaut** | `filing_plan.yaml`: Eingang neben dem Archiv, Klaerungsknoten INNERHALB (`archive/_unsorted/`), plus die Regel `FP-900` im Beispielblock |
| F5 | **gebaut** | `filing_plan.yaml`: Quarantaeneknoten `archive/_quarantine/` plus Regel `FP-901`; die Wand darunter ist der vorhandene `guard_fs_tripwire` |
| F6 | **war schon ausgeliefert, jetzt gemessen** | `templates/repo/.gitignore` trug beide Haelften bereits; neu ist der Stolperdraht `tools/test_hooks_v2.py::test_the_office_gitignore_still_lets_the_tray_seeds_into_a_fresh_clone`, der die `dir/*`-plus-Negation-Falle mit `git check-ignore` in beide Richtungen misst |
| F7 | **offen, eigenes Paket** | zwei Verfahrensvorlagen (Eingangsroutine, unabhaengige Projektpruefung). Braucht PROC-Vorlagen im Kit und einen Rollentext, der sie nennt -- beides ausserhalb von TSK-0107 |
| F8 | **offen, eigenes Paket** | die Jahresansicht. Liegt beim Dashboard-Strom, nicht bei der Vorlagenarbeit; die Bedingung aus Abschnitt 5 der Wunschliste gilt weiter (nach `generated/`, nicht committet, Quelle und Stichtag genannt) |

## Reihenfolge

**F1 zuerst und allein blockierend** — solange der Aktenplan leer ausgeliefert wird, verweigert
jedes neue Office-Projekt seine erste Ablage, und nach der Installation kann es niemand mehr
reparieren. F2 bis F6 sind Vorlagen- und Textarbeit im selben Zug. F7 und F8 sind eigene Pakete.

## Was NICHT übernommen wird

Marktplatz-Abläufe (eBay-Bündelaufteilung, Kaufland-Rechnungsgenerator), Produktkatalog,
Preislisten-Abgleich, Bildpflege, Marketingplan. Sie funktionieren im Feld, aber sie beschreiben
einen Händler, kein Büro. Ein Kit, das sie mitliefert, zwingt jedem Steuerberaterbüro einen
Produktkatalog auf.
