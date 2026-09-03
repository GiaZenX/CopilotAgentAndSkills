# TSK-0109 -- user feedback on the built dashboard (2026-09-02 ~14:10)

Verbatim, after seeing regular-ueberblick-1280.png, regular-rechnungen-390.png and
alarm-kleinunternehmer-1280-dark.png:

> Beim Dashboard haette ich die Einnahmen, Ausgaben, Ueberschuss auch gerne aufgeteilt mit
> Brutto / Netto / USt untereinander, wie beim BuyPlugGo Kit. So sieht man gleich das
> Nettoergebnis nach USt und die USt-Zahllast. Aber das Design gefaellt mir viel besser.

## What this is

A CONTENT request inside FR-0032's own addendum ("use the existing BuyPlugGo finance dashboard
TEMPLATE as the content reference"): the three headline figures on the Ueberblick tab -- and by
the same rule the EUeR tab -- carry three stacked lines each: Brutto, Netto, USt. From them the
reader sees the net result after VAT and the VAT payload (Zahllast = USt on paid income minus
Vorsteuer on paid expenses) without opening the report.

The design itself is accepted by the user ("gefaellt mir viel besser") -- no restyle, the
journal look stays; the split is more rows under the same numbers.

## Derived points for the rework (lead's reading; the implementer measures)

1. The ledger already carries `net`, `vat_rate`, `gross`, `vat_treatment` per row
   (`scripts/ledger_add.py:50`) -- no new data, a second aggregation of the same rows.
2. Two tax states, both must render honestly:
   - `kleinunternehmer: true` (the fixtures' state): no USt is charged and no Vorsteuer deducted --
     Brutto equals Netto, the USt line reads "keine USt (Kleinunternehmer, § 19 UStG)" and no
     Zahllast is shown. Showing "0,00 EUR Zahllast" would be a wrong statement, not a zero.
   - Regelbesteuerung (including the alarm state where the threshold is exceeded): full split
     and the Zahllast line; the sign convention (payload vs refund) stated on the page.
   - `vat_treatment` per row (standard / reverse-charge / exempt ...) decides which rows carry
     USt at all -- the generator follows `euer_report.py`'s treatment of that column, never its
     own rule (the parity test extends to the three new figures).
3. Parity: `euer_report.py` is the authority; if the report does not print Netto/USt sums today,
   the generator may compute them from the same rows, and the parity test then compares against
   an independent aggregation of the CSV, not against the generator itself.
4. Sighting: the Ueberblick and EUeR tabs re-rendered at 1280/390 light/dark for all three
   fixtures plus the founding-year fixture the verifier is building; the stacked three lines
   must survive 390 px without truncation (the 390 px filter block is already long -- measure
   whether the split pushes the first booking below the fold and say so).
5. The BuyPlugGo template itself is still not received; "wie beim BuyPlugGo Kit" is the user's
   description of it, and this note is the reference until the file arrives.

Apply with the verifier's findings in ONE rework round (Opus), not as a separate spawn.
