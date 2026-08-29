# TSK-0091 / BUG-0072 — Messungen: falsches Netto aus ZUGFeRD/CII, und was ein Projekt nachprüfen muss

**Datum:** 2026-08-29 · **Rolle:** harness-implementer · **Gegenstand:**
`team-kits/office-team/templates/repo/scripts/einvoice_extract.py`

Dieses Dokument hält fest, was gemessen wurde, und vor allem **das Prüfkriterium für bereits
gebuchte E-Rechnungen** (AC-B2 des Nutzerprojekts) — das ist die Hälfte, die sonst nur im
Rundenbericht stünde und mit der Sitzung verschwindet.

## 1. Der Fehler

`_txt(root, *local_names)` (Stand vor dem Fix, Zeilen 30–36) durchlief `root.iter()` in
**Dokumentreihenfolge** über eine **Menge** von Namen. Damit gewann jedes Element, das im Dokument
zuerst steht — und in CII stehen alle `IncludedSupplyChainTradeLineItem/…/
SpecifiedTradeSettlementLineMonetarySummation/LineTotalAmount` **vor**
`ApplicableHeaderTradeSettlement/SpecifiedTradeSettlementHeaderMonetarySummation`.

Zwei unabhängige Hälften:

1. **Positionsebene schlägt Kopfebene.** Netto = `LineTotalAmount` der **ersten Position**.
2. **Dokumentreihenfolge schlägt Namensreihenfolge.** Auch ohne Positionen steht in derselben
   Summation `LineTotalAmount` über `TaxBasisTotalAmount` — bei Dokumentrabatt also der
   **Vor-Rabatt-Betrag**. In UBL identisch (`LineExtensionAmount` vor `TaxExclusiveAmount`).

Dasselbe traf `seller` (`_txt(root, "Name")` → `SpecifiedTradeProduct/Name` der ersten Position).

## 2. A/B über das echte Archiv (read-only)

Altes Skript (`git show HEAD:…`) gegen neues, über
`OneDrive/4-BuyPlugGo/archive/1-Finanzen`; 4 strukturierte E-Rechnungen insgesamt, alle vier mit
falschem Netto und **rc 0** (also ohne jede Fehlermeldung):

| Beleg | netto alt | netto neu | brutto | rc alt/neu |
|---|---|---|---|---|
| 2026-05-07 idealo | 0.51 | 20.00 | 23.80 | 0 / 0 |
| 2026-06-05 idealo | 18.87 | 47.94 | 57.05 | 0 / 0 |
| 2026-07-07 idealo | 5.10 | 114.24 | 135.95 | 0 / 0 |
| 2026-08-11 idealo | 14.28 | 214.20 | 254.90 | 0 / 0 |

`seller` in allen vier Fällen alt = Produktname, neu = „idealo internet GmbH". Keine einzige
Fehlverweigerung (rc 2) im echten Korpus.

## 3. Prüfkriterium für bereits gebuchte Belege (AC-B2, projektseitig)

**Betroffen ist eine Buchung genau dann, wenn ihr Netto nicht der Dokumentsumme entspricht, weil es
aus einem Positions- oder Vor-Rabatt-Element stammt.** Mechanisch nachprüfbar so:

1. **Kandidatenmenge:** alle Ledger-Zeilen, deren `source` auf ein **ZUGFeRD/Factur-X-PDF oder eine
   XRechnung-XML** zeigt (reine Scan-PDFs sind nie betroffen — dort hat der Extraktor nie gelesen,
   rc 1).
2. **Schnelltest je Zeile:** `net + tax == gross`? Bei `vat_rate`-Buchungen gleichwertig
   `net × (1 + rate) == gross`. Stimmt das **nicht**, ist die Zeile falsch — unabhängig von dieser
   Runde.
3. **Der gefährliche Rest**, den Schritt 2 *nicht* findet: eine Zeile, bei der jemand das
   **falsche Netto übernommen und den Bruttowert daraus gerechnet** hat (dann stimmt die Zeile in
   sich und ist trotzdem falsch). Solche Zeilen erkennt man nur am Beleg: neu extrahieren
   (`python scripts/einvoice_extract.py <source>`) und `net` vergleichen. Verdächtig ist jede
   Zeile, deren gebuchtes Netto gleich dem `LineTotalAmount` der **ersten** Position des Belegs ist
   (ohne Positionen: gleich dem `LineTotalAmount` der Kopfsummation statt `TaxBasisTotalAmount`).
4. **Zweitwirkung `counterparty`:** wo der Bookkeeper den `seller` des Extraktors übernommen hat,
   steht dort ein **Produktname** statt des Lieferanten. Verdächtig ist jede Gegenpartei, die wie
   eine Leistungsbezeichnung klingt.

**Befund im Nutzerprojekt (2026-08-29, nur gelesen):** die vier idealo-Zeilen in `ledger/2026.csv`
tragen die Dokumentwerte; die falschen Zahlen sind **nie gebucht** worden. Der Grund ist messbar
`scripts/ledger_add.py:133–139` (`net × (1+rate)` vs. `gross`, Toleranz 0.011) — jedes falsche
Netto wäre dort abgelehnt worden. Der Sweep bleibt trotzdem projektseitig: Schritt 3 liegt
außerhalb dessen, was der Ledger-Richter sehen kann.

## 4. Was der neue Guard prüft — und was nicht

Identität: **BR-CO-15**, `BT-112 Bruttosumme = BT-109 Nettosumme + BT-110 Steuersumme`,
Toleranz **0,01 EUR einschließlich**, Beträge als `Decimal`, auf den Cent mit `ROUND_HALF_UP`
gerundet. Kein Steuersatz geht ein — deshalb trägt die Prüfung Mehrsatz-Rechnungen und
0 %-Fälle gleichermaßen. Ein Rundungsbetrag (**BT-114**) gehört **nicht** hierher, sondern zu
BR-CO-16 (`BT-115 = BT-112 − BT-113 + BT-114`); er geht nur ein, wenn das Dokument keine
Bruttosumme nennt und der Zahlbetrag einspringt.

Nicht geprüft (bewusst, benannt): ob es die Zahlen des **richtigen** Belegs sind (drei Zahlen aus
der falschen Rechnung stimmen untereinander — FR-0065), und ob die **Steuersätze der einzelnen
Positionen** die Kopfsummen ergeben (BR-CO-14).

## 5. Nebenbefund: zwei Tests fielen an einer Umgebungsvariable, nicht an dieser Runde

`tools/test_hooks.py` setzte `$HARNESS_KERNEL_PATH` an zwei Stellen prozessweit und nahm sie nie
zurück. Der Einstiegspunkt behandelt diese Variable **absichtlich als autoritativ**, also
beantwortete jedes spätere Unterprogramm der Sitzung seine Kernel-Frage aus **diesem** Repo statt
aus dem gebauten Projekt. Folge: `test_kitupdate.py::test_the_bridge_reads_the_route_off_the_
projects_own_entry_point` und `…::test_a_stock_without_update_kit_is_lifted_by_the_bootstrap_and_
told_about_it` fielen in jedem Lauf, in dem `test_hooks.py` vorher lief — und liefen allein grün.

Gemessen: auf **unberührtem HEAD** (Tarball außerhalb des Repos) dieselben zwei Fehlschläge;
mit `HARNESS_KERNEL_PATH=…/team-kits` von Hand fallen sie auch allein; ohne sie laufen sie grün.
Behoben über `tools/conftest.py::_no_test_leaks_an_environment_variable` (stellt die Umgebung nach
jedem Test wieder her, wie es `_no_test_leaks_an_import_path` für `sys.path` tut), die beiden
Quellen benutzen jetzt `monkeypatch`. Messung:
`tools/test_repo_hygiene.py::test_no_test_in_this_suite_leaks_an_environment_variable`.

## 6. Lieferweg

`scripts/einvoice_extract.py` ist seit dieser Runde **kit-owned**
(`team-kits/repo_kit_owned.txt`): der Installer überschreibt die Projektkopie bei jedem Lauf, der
Fix erreicht bestehende Projekte ohne Zutun eines Menschen, und die Datei landet nie auf
`.claude/kit_update_pending.repo`. Gemessen mit dem echten `scaffold_team.ps1`: Vor-Fix-Kopie
(Hash `21e409cbc3ea`, exakt der Hash der Kopie im Nutzerprojekt) → nach Re-Install die Kit-Fassung,
rc 0, keine Pending-Zeile. Preis, ebenfalls benannt: eigene Änderungen eines Projekts an dieser
Datei werden dabei ohne Rückfrage überschrieben.
