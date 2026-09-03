# 02 — Datenvertrag: welches Feld welche Ansicht speist

Alles abgeleitet aus den Dateien, die das Office-Kit heute ausliefert — kein Feld ist erfunden.
Quellen, mit der Stelle, die die Wahrheit hält:

| Quelle | Autorität | Was davon gelesen wird |
|---|---|---|
| `ledger/<Jahr>.csv` | `scripts/ledger_add.py` `COLUMNS`, `YEAR_FILE_RX`, `read_ledger`, `validate_file` | alle 15 Spalten; nur Dateien, die `YEAR_FILE_RX` matcht (eine `2026 - Kopie.csv` ist unsichtbar, so wie für `euer_report.py`) |
| Vorzeichen und Zeitraum | `scripts/euer_report.py` `NEGATIVE_DOC_TYPES`, `sign_of`, `quarter_range` | **importiert, nicht kopiert** — die Regel hat ein Zuhause, und `ledger_add.py` pinnt sie schon per Test an `euer_report.py` |
| `project_memory/master_data.yaml` | Vorlage `templates/project_memory/master_data.yaml` | `categories.<direction>[].key / label_de / euer_line`; `counterparties[].canonical` wird NICHT gelesen — der Ledger trägt die Gegenpartei schon normalisiert (Bookkeeper-Skill, Schritt 2) |
| `project_memory/business_profile.yaml` | Vorlage `templates/project_memory/business_profile.yaml` | `business.name`, `business.legal_form`, `tax.kleinunternehmer` |

Die Ledgerspalten und ihre Rolle auf der Seite:

| Spalte | Rechnungen | Überblick | Offene Posten | EÜR | Kleinunternehmer |
|---|---|---|---|---|---|
| `id` | Detailzeile, Volltext | — | — | — | — |
| `doc_date` | Spalte Datum, Sortierung, Quartal | letzte Buchungen | Belegdatum, Alter | „offen bis Zeitraumende" | — |
| `payment_date` | Spalte „Bezahlt am", Status | **Zuordnung zum Jahr und Monat** | leer = offen | **Zuordnung zum Zeitraum** | Zuordnung zum Jahr |
| `direction` | Filter, Fettung des Bruttobetrags | Einnahmen/Ausgaben | Forderung vs. Verbindlichkeit | Einnahmen/Ausgaben | nur `income` |
| `doc_type` | Status „Korrektur", Detailzeile | Vorzeichen | Korrekturen sind keine Posten | Vorzeichen | Vorzeichen |
| `counterparty` | Spalte, Filter, Volltext | letzte Buchungen | Spalte | — | — |
| `invoice_no` | Spalte Nr., Volltext | — | Spalte Nr. | — | — |
| `net` | Spalte Netto | — | — | USt = brutto − netto | — |
| `vat_rate` | — (folgt aus netto/brutto) | — | — | — | — |
| `gross` | Spalte Brutto, Summe | die drei Zahlen, Balken | Summe | Summen, nach Kategorie | Gesamtumsatz |
| `vat_treatment` | Detailzeile | — | — | `standard` → USt-Zeilen; `reverse_charge` → Zähler | — |
| `category` | Spalte (Label), Filter | Label bei letzten Buchungen | Label | nach Kategorie, `euer_line` | — |
| `source` | Detailzeile (Archivpfad, kein Inhalt) | — | — | — | — |
| `reverses` | Detailzeile; das Ziel bekommt Status „storniert" | Status | storniertes Original ist kein Posten | wie `euer_report.py` | — |
| `note` | Volltext, Detailzeile | — | — | — | — |

## Abgeleitete Größen — und wo ihre Regel steht

- **Status einer Zeile** (in dieser Reihenfolge): `storniert`, wenn eine `reversal`-Zeile sie in
  `reverses` nennt; `korrektur`, wenn `doc_type` in `NEGATIVE_DOC_TYPES`; `bezahlt`, wenn
  `payment_date` gesetzt; sonst `offen`. Genau die Fallunterscheidung, die `euer_report.main`
  für „paid" und „open" trifft — Prototyp: `make_mockups.load_project`.
- **Betrag in Cent, vorzeichenbehaftet**: `round(gross·100)·sign_of(row)`. Alle Summen laufen über
  Ganzzahlen, im Python-Generator wie im Seitenskript (`data-cents`), damit kein Gleitkommarest
  zwischen zwei Anzeigen derselben Summe steht.
- **Zeitraum-Zuordnung**: Zufluss/Abfluss, also nach `payment_date`; `quarter_range` aus
  `euer_report`. Eine Dezemberrechnung, im Januar bezahlt, liegt laut `ledger_add.validate_cross`
  ohnehin in der Datei des Zahlungsjahres — die Beispieldaten mussten das lernen (der Kit-Validator
  hat es beim ersten Rendern angemahnt).
- **Mahnkandidat**: `status == offen` und `direction == income` und Alter > `PAYMENT_TERM_DAYS`
  (30; Quelle § 286 Abs. 3 BGB). Der Ledger hat kein Fälligkeitsdatum, das Profil keine
  Zahlungsfrist — die Zahl steht daher im Generator, an genau einer Stelle, und die Seite sagt das.
- **Kleinunternehmer-Befund**: Vorjahr = das zweitjüngste Ledgerjahr, laufend = das jüngste;
  Gesamtumsatz = bezahlte `income`-Zeilen brutto, Korrekturen abgezogen. Grenzen 25.000 / 100.000 €
  (§ 19 Abs. 1 UStG, Fassung seit 2025-01-01); Befund `within` / `previous_exceeded` /
  `current_exceeded`. Nur wenn `tax.kleinunternehmer` `true` ist.
- **Datenstand**: `max(doc_date ∪ payment_date)` über alle Zeilen. Kein Erzeugungszeitpunkt.
- **Gültigkeit**: `ledger_add.validate_file(path)` je Datei; ein Befund → Banner mit den ersten
  sechs Befunden wörtlich, Stempel „ungültig" im Überblick, Summen bleiben sichtbar (die kaputte
  Zeile muss gefunden werden), aber als nicht belastbar bezeichnet.

## Was die Seite NICHT liest, benannt

- `counterparties[].aliases` / `default_vat_treatment` — Buchungslogik, nicht Anzeige.
- `document_sources`, `revenue_sources`, `privacy` — nichts davon ist eine Zahl.
- `reports/euer_*.md` — die Seite verweist per Pfadmuster, liest den Bericht nicht (ein zweiter
  Leser derselben Zahlen wäre eine zweite Wahrheit).
