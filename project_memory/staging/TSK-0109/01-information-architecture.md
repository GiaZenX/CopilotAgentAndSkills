# 01 — Informationsarchitektur: fünf Reiter, eine Datei

Gegenstand: das Finanz-Dashboard des Office-Kits (FR-0032). Zielgruppe: die Inhaberin eines
kleinen Betriebs, die ihre Belege buchen lässt und wissen will, wie das Geschäft steht und was sie
als Nächstes tun muss. Das ist die eine Aufgabe der Seite: **Stand und nächste Handlung, in unter
einer Minute.** Alles, was dieser Aufgabe nicht dient, steht nicht auf dem ersten Reiter.

Der Nutzer hat vorgegeben (FR-0032 `triage_result`): nicht alles auf eine Seite; Dashboard,
Rechnungen, filterbar, Reiter. Daraus folgt: **eine generierte HTML-Datei, fünf Reiter**, Reiter
und Filter als DOM-Zustand (`hidden`-Attribut) wie beim Kernel-Board (`kernel/board.py`), damit
ein Test die Seite ohne Browser lesen kann und ohne Skript alles untereinander steht.

## Die Reiter, in der Reihenfolge der Leiste

| # | Reiter | Erstes, was man sieht | Filter | Was bewusst NICHT hier steht |
|---|---|---|---|---|
| 1 | **Überblick** | Drei Zahlen auf einer Journalzeile: Einnahmen, Ausgaben, Überschuss des Jahres (bezahlt, Zufluss/Abfluss), der Überschuss mit Doppelstrich. Darunter „Jetzt ansteht" (max. vier Zeilen: offene Forderungen mit Mahnkandidaten, zu zahlende Rechnungen, Kleinunternehmer-Stand, Ledger-Prüfung), dann zwölf Monatsbalken, dann die letzten sechs Buchungen | Jahr | Kategorien, USt, Listen — jede davon hat ihren Reiter |
| 2 | **Rechnungen** | Die Filterleiste und direkt darunter „n von N Buchungen · Summe brutto" mit Doppelstrich, dann die Liste, neueste zuerst, 100 Zeilen, Rest per „alle anzeigen" | Volltext (Gegenpartei, Nummer, Notiz, Id), Richtung, Status (offen/bezahlt/storniert/Korrektur), Jahr, Quartal, Kategorie, Gegenpartei; „Filter zurücksetzen" | Belegtext, Archivinhalt — nur der Archivpfad in der Detailzeile |
| 3 | **Offene Posten** | Zwei Listen: Forderungen (was Kunden schulden) und Verbindlichkeiten (was wir zahlen), älteste zuerst, mit Alter in Tagen und Summenzeile; Mahnkandidaten tragen den Stempel „mahnen" | „nur Mahnkandidaten" | Ein Mahnschreiben — das ist `outbox/`-Arbeit einer Rolle, nicht dieser Seite |
| 4 | **EÜR** | Dieselben Summen, die `euer_report.py` für den Zeitraum schreibt: Einnahmen, Ausgaben, Überschuss (Doppelstrich), nach Kategorie mit der Zeile der Anlage EÜR, USt informativ, Zahl der offenen Posten | Jahr, Zeitraum (ganzes Jahr / Q1–Q4) | Der Bericht selbst — die Seite verweist auf `reports/euer_<Jahr>_Q<q>.md` und ersetzt ihn nicht |
| 5 | **Kleinunternehmer** | Zwei Füllstandsleisten: Vorjahr gegen 25.000 €, laufendes Jahr gegen 100.000 €, darunter der Befund als Stempel (innerhalb / überschritten) und ein Satz, was das bedeutet | keine | Eine Hochrechnung aufs Jahresende — eine erfundene Zahl; die Seite zeigt nur Gemessenes |

Reiter 5 erscheint nur, wenn `business_profile.yaml` nicht `tax.kleinunternehmer: false` sagt; bei
`null` zeigt er, dass der Steuerstatus fehlt (und der Überblick sagt es in „Jetzt ansteht" ebenfalls).
Trägt der Befund „überschritten", bekommt der Reiter einen roten Punkt in der Leiste.

## Zustände, die jede Ansicht hat

Die drei Mockups sind die drei Zustände, die der Generator erzeugen muss — nicht drei Entwürfe:

- **regular** — ein zweites Geschäftsjahr, zwei Ledgerdateien, offene und überfällige Posten.
- **empty** — Tag eins: kein `ledger/`, Profil leer. Jede Ansicht sagt, woher ihr Inhalt kommen
  wird und welcher Befehl ihn schreibt. Leere ist Richtung, nicht Stimmung.
- **alarm** — ungültige Ledgerzeile (Banner im Kopf, Befund wörtlich aus `ledger_add.validate_file`),
  Vorjahresgrenze überschritten (roter Punkt am Reiter, Alarmzeile im Überblick), Mahnkandidaten.

## Was nicht auf die Seite gehört, und warum

- **Keine Uhrzeit der Erzeugung.** Die Datei ist eine reine Funktion der Daten (Office-Developer-
  Regel: „no timestamps-as-content"). Der „Datenstand" im Kopf ist das jüngste Datum im Ledger.
  Das Alter offener Posten rechnet der Browser beim Öffnen aus seiner eigenen Uhr.
- **Keine Karten, keine Schatten, kein Farbverlauf, keine Kacheln.** Die Seite ist ein Journal,
  keine Kachelwand — siehe `03-tokens.md`.
- **Keine Diagrammbibliothek, keine Schrift aus dem Netz.** Zwölf Balken sind zwölf `div`s mit
  Höhe in Prozent; das Kit verbietet jede externe Anfrage.
