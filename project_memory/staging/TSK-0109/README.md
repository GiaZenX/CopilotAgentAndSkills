# TSK-0109 — Design-Paket Finanz-Dashboard (Phase 1 von 2, Fable)

Stream I, FR-0032, DEC-0059/DEC-0060. Phase 1 schreibt **nur** in dieses Verzeichnis und in
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0109\`; der Worktree `g2-dashboard` ist unberührt
(`git status` dort: 0 Zeilen). Kein Kit-File wurde angefasst.

## Inhalt

| Datei | Was |
|---|---|
| `01-information-architecture.md` | fünf Reiter, was jeder zuerst zeigt, welche Filter, was bewusst fehlt; die drei Zustände |
| `02-data-contract.md` | Ledgerspalte → Ansicht, abgeleitete Größen mit der Stelle ihrer Regel, was nicht gelesen wird |
| `03-tokens.md` | Richtung „Kassenbuch", Signatur Doppelstrich, Token mit Rolle und Grund, Verworfenes |
| `04-build-spec.md` | Dateien, Generatorform, Auslöser-Ableitung, Tests (rot ohne Fix), Lochkandidaten, Seams |
| `finance-dashboard.template.html` | die Hülle: Token-Blatt als `:root`, Struktur, das eine Skript — **die Autorität für jeden Wert** |
| `make_mockups.py` | Prototyp: Beispielprojekte erzeugen, aggregieren, rendern; importiert `euer_report` und `ledger_add` aus dem Kit |
| `mockup-regular.html`, `mockup-empty.html`, `mockup-alarm.html` | die drei Zustände, aus einer Vorlage |
| `sample/<state>/` | Fixture-Projekte: `ledger/2025.csv`, `ledger/2026.csv`, `business_profile.yaml`, `master_data.yaml` — vom Kit-Validator als gültig (regular, empty) bzw. ungültig (alarm) beurteilt |
| `render_mockups.py` | Sicht-Schleife: Playwright, 1280 und 390 px, jeder Reiter, dunkel, zwei Filterzustände, Uhr eingefroren |
| `review/*.png`, `review/render.json` | 38 Bilder, an die SHA-256 der gerenderten Bytes gebunden; `errors: []` bei allen drei |

## Sichtprotokoll (BUG-0076: nichts wird gezeigt, was niemand gerendert hat)

Drei Render-Durchgänge, jeder mit Befund und Korrektur, bevor irgendetwas hier als fertig steht:

1. **Durchgang 1** (13 Bilder gesichtet): Bahnschrift rendert, Doppelstrich steht, Filter und Detailzeile
   funktionieren, Dunkelmodus trägt, Alarmbanner und roter Reiterpunkt sichtbar. Befunde: Spaltenköpfe
   „Brutto" und „Bezahlt am" klebten aneinander; die Beispieldaten hatten 250 Tage alte offene
   Lieferantenrechnungen (Artefakt des Generators am Jahreswechsel); die Rechnungsliste bei 390 px war als
   Vollseite 28.000 px hoch und ohne Seitenschnitt.
2. **Durchgang 2**: Kit-Validator meldete den Normalzustand ungültig — zu Recht: eine Dezemberrechnung
   mit Januarzahlung gehört nach `ledger_add.validate_cross` in die Datei des Zahlungsjahres. Der
   Generator wurde der Regel angepasst statt umgekehrt. Danach: Rechnungsliste bei 390 px lief über
   den Rand (Nummer dreizeilig, Status abgeschnitten); der Verlauf an der Reiterleiste machte aus
   „Kleinunternehmer" ein „Kle nu".
3. **Durchgang 3**: Mobil behält Datum, Gegenpartei, Brutto, Status; kein Verlauf; Kategorie auf
   eigener Zeile. Fixtures auf YAML umgestellt (Kit-Form). Ein Satz auf der Seite korrigiert, der
   dem Skript widersprach („ohne Skript zeigt die Spalte das Belegdatum" → „bleibt leer").

## Messungen, die das Paket tragen

| Messung | Ergebnis |
|---|---|
| Filter Einnahmen + offen (Playwright, `_round-scratch/TSK-0109/measure_mockup.py`) | CSV: 4 Zeilen, 273.605 Cent; Seite: 4 sichtbar, `[data-count]` 4, `[data-sum]` 2.736,05 € |
| Reset nach Filter | 318 gezählt, 100 sichtbar (Seitenschnitt), Rest hinter „alle anzeigen" |
| Mahnkandidaten bei eingefrorener Uhr 2026-09-02 | CSV: 2 offene Einnahmen älter als 30 Tage; Seite: 2 Stempel „mahnen", `[data-overdue-count]` 2 |
| Anfragen der Seite | genau eine: die `file://`-URL der Seite selbst |
| DOM ohne Skript | 5 `section.view`, 4 `hidden`; `noscript` hebt es auf |
| Parität mit dem echten `euer_report.py` (`_round-scratch/TSK-0109/parity_euer.py`, Skript ins Beispielprojekt kopiert, acht Quartale) | 8 von 8: Einnahmen, Ausgaben und Zahl der offenen Posten identisch, 0 Abweichungen |
| Kit-Validator über die Fixtures | regular gültig (318 Zeilen), empty gültig (0), alarm ungültig mit dem BUG-0072-Befund `net 214.20 … != gross 14.28` wörtlich im Banner |
| Konsolen-/Seitenfehler beim Rendern | keine, in allen 38 Bildern (`render.json`) |
| `ruff check` über die beiden Prototyp-Skripte | sauber — nach sechs Befunden im ersten Lauf (ungenutzte Variablen, `l`, Lambda), behoben |
| Determinismus des Prototyps | zwei Läufe von `make_mockups.py` nach den Lint-Änderungen: alle drei Mockup-SHA-256 unverändert und gleich denen in `render.json` |

## Was frontend-design an den Entscheidungen geändert hat

Der Skill verlangt, jede Achse, die der Auftrag freilässt, **nicht** mit einem der drei
KI-Standardlooks zu füllen, und den Plan vor dem Bauen gegen die Frage zu prüfen, ob ein anderer
Auftrag dasselbe ergeben hätte. Das hat drei Dinge verändert:

- **Erster Entwurf war Kacheln.** Der naheliegende Plan — KPI-Kacheln mit Radius und Schatten,
  Farbverlauf-Balken, Pills als Status — ist das, was `progress.dashboard.template.html` schon ist,
  und es ist die Antwort auf jeden Dashboard-Auftrag. Ersetzt durch das Journal: Striche, Doppelstrich
  unter Summen, Stempel statt Pills. Der Nutzer wollte „weniger überladen, wichtige Zahlen direkt
  sichtbar" — Kacheln machen alles gleich wichtig.
- **Grün/Rot für Einnahme/Ausgabe verworfen**, weil Rot dann dem Alarm fehlt. Der Skill sagt „spend
  your boldness in one place": ein Akzent (Stempelblau), eine Alarmfarbe, sonst Tinte.
- **Schrift aus dem Gegenstand.** DIN-Form (Bahnschrift / DIN Alternate) statt einer beliebigen
  Grotesk, weil die Anlage EÜR und jedes deutsche Formular so gesetzt ist — und als Systemschrift,
  weil das Kit keine Netzanfrage erlaubt.

Die Selbstprüfung gegen den Broadsheet-Standard (Look 3) steht in `03-tokens.md` unter „Verworfen";
was mich davon trennt, ist in den Screenshots zu sehen, nicht behauptet: eine Spalte, 40 px
Sektionsabstand, 2,6-rem-Zahlen, Radius an Stempeln.

Was der Skill NICHT geändert hat: die Inhalte. Reiter, Filter und Zahlen kommen aus FR-0032, dem
Nutzerverdikt und den Ledgerspalten, nicht aus der Gestaltung.

## Offene Fragen an den Lead

1. **Wo lebt der Generator, und wem gehört er?** Der `allowed_scope` legt ihn nach
   `templates/repo/tools/` — das anpassbare Eigentum des Office-Developers, copy-if-absent. Ein
   Auslöser aus `gate_ledger_valid` (die einzige Stelle, an der jede Ledger-Änderung vorbeikommt,
   Ableitung in `04-build-spec.md` §3) darf nach dem Präzedenzfall `VALIDATOR` nur kit-owned Code
   ausführen (`repo_kit_owned.txt`). Entweder der Generator wird kit-owned und damit nicht anpassbar,
   oder er bleibt Hand-Schritt wie `generate_dashboard.py` und „auto-regeneriert" aus FR-0032 gilt
   nicht. Meine Empfehlung: kit-owned plus Seam an G; ohne diese Entscheidung baut Phase 2 den
   Hand-Schritt und benennt das Loch.
2. **`dashboards/finanzen.html` tracken oder ignorieren?** Die Verfassung führt `dashboards/` als
   getrackte Ausgabe; das Kernel-Board liegt unter `generated/` und ist ignoriert, weil eine bei jedem
   Schreiben regenerierte Datei in git eine immer veraltete zweite Kopie plus Merge-Konflikt ist.
   Empfehlung: ignorieren (`templates/repo/.gitignore`, unowned — Seam).
3. **Zahlungsfrist als Profilfeld?** Mahnkandidat = älter als 30 Tage (§ 286 Abs. 3 BGB), Konstante
   im Generator, weil weder Ledger noch Profil eine Frist kennen. Ein Feld `tax`/`payment_terms` im
   `business_profile.yaml` wäre Stream-G-Gebiet und ein Onboarding-Satz — nur wenn der Nutzer das
   will; die Seite sagt heute, woher die 30 kommen.
4. **Die BuyPlugGo-Vorlage.** Ich habe sie nicht erhalten und nichts daraus verwendet; das Paket ist
   aus FR-0032, dem Verdikt und dem Ledger abgeleitet. Bitte den Pfad für Phase 2 nennen: die
   Build-Phase vergleicht dann die Ansichtenliste und meldet, was die Vorlage hat und dieses Paket
   nicht — als Follow-up, nicht als stiller Umbau.
5. **Modell-Notiz für DEC-0059 (g):** Phase 1 auf Fable, Wall-Clock unten; die Prüferrunde misst,
   ob die Prosa-Überbehauptungen der ersten Generation hier ausbleiben.

## Was bewusst nicht geschlossen, aber benannt ist

- Kein Auslöser gebaut (Scope), kein Kit-File geändert, kein Test im Repo — Phase 2.
- Das Alter offener Posten hängt an der Uhr des Betrachters; ohne Skript bleibt es leer.
- Der Generator wird von `gate_ledger_valid._BLOCKED_SCRIPT_RX` nicht als Report erkannt und läuft
  gegen einen ungültigen Ledger — er sagt es dann auf der Seite (Alarm-Mockup).
- Die Beispieldaten sind erfunden (Seed 2026/2027), nicht aus einem Live-Projekt; sie sind so
  gebaut, dass sie den Kit-Validator bestehen, mehr nicht.
- `mockup-alarm.html` zeigt „Vorjahresgrenze überschritten" mit 26.323,76 € Vorjahresumsatz — die
  Fixture ist dafür gebaut; ob `kleinunternehmer: true` bei diesem Umsatz im echten Profil noch
  stimmt, ist genau die Frage, die die Seite stellt, nicht beantwortet.

## Wall-Clock

Beginn 2026-09-02 11:20 (erste Lesung der Eingaben), Ende 11:46. Davon Lesen und Ableiten ~12 min,
Prototyp und Vorlage ~8 min, drei Render-Sicht-Fix-Schleifen ~10 min, Dokumente und Lint ~6 min.
Modell: Fable (DEC-0059).
