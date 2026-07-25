#!/usr/bin/env python3
"""
euer_report.py — deterministic quarterly income/expense statement FROM the ledger.

The report is GENERATED, never written by an LLM: numbers that pass through a model are a second
hallucination opportunity, and sums could drift from the data. Zufluss/Abfluss principle
(§ 11 EStG): paid totals count by PAYMENT date within the quarter; document-dated-but-unpaid
items are listed separately as OPEN, never mixed in. Prose (anomalies, context) belongs in the
bookkeeper's reports/<name>_notes.md.

Usage: python scripts/euer_report.py --year 2026 --quarter 2
Exit 0 = report written to reports/euer_<year>_Q<q>.md. Exit 1 = refused (reason on stderr).
"""
import argparse
import csv
import datetime
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DISCLAIMER = (
    "> **Hinweis:** Vorbereitende Aufstellung aus dem Belegjournal — keine Steuerberatung, keine\n"
    "> Steuererklärung, keine revisionssichere Archivierung. Zahlungsprinzip (Zufluss/Abfluss);\n"
    "> offene Posten sind separat ausgewiesen. Prüfung und Abgabe: Steuerberater/in.\n")


# THE SIGN CONVENTION, in one place because it is the single arithmetic fact this whole report
# rests on. Three doc types REDUCE the total of their own direction:
#
#   reversal     — cancels an earlier entry outright
#   credit_note  — a Gutschrift: reduces what was invoiced
#   refund       — money given back on an earlier booking
#
# `credit_note` and `refund` used to be signed +1, i.e. added. An income invoice of 1190,00 plus
# the credit note that cancels it therefore reported 2380,00 EUR income and 380,00 EUR VAT — in a
# document prepared for a tax office. Nothing flagged it: both rows are individually valid, the
# validator accepted them, and the report has no reason to suspect its input. `direction` says
# WHOSE side the money is on; `doc_type` says whether it adds or removes. Keep this list and
# `ledger_add.py`'s `NEGATIVE_DOC_TYPES` identical — a test pins that they are.
NEGATIVE_DOC_TYPES = ("reversal", "credit_note", "refund")


def sign_of(entry):
    return -1 if entry.get("doc_type") in NEGATIVE_DOC_TYPES else 1


def quarter_range(year, quarter):
    start = datetime.date(year, 3 * (quarter - 1) + 1, 1)
    end_month = 3 * quarter
    if end_month == 12:
        end = datetime.date(year, 12, 31)
    else:
        end = datetime.date(year, end_month + 1, 1) - datetime.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--quarter", type=int, required=True, choices=(1, 2, 3, 4))
    args = ap.parse_args()

    path = os.path.join(ROOT, "ledger", "%d.csv" % args.year)
    if not os.path.isfile(path):
        sys.stderr.write("[euer_report] no ledger for %d (%s)\n" % (args.year, path))
        sys.exit(1)
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    q_start, q_end = quarter_range(args.year, args.quarter)
    paid, open_items = [], []
    reversed_ids = {r["reverses"] for r in rows if r.get("doc_type") == "reversal" and r.get("reverses")}
    for r in rows:
        pd = r.get("payment_date") or ""
        if pd and q_start <= pd <= q_end:
            # PAID aggregation keeps BOTH the original and the reversal row (sign -1 below): the
            # original stays historically correct in ITS quarter (Zufluss/Abfluss), the reversal
            # subtracts in the quarter it was booked — the year nets to zero. Skipping the original
            # AND subtracting the reversal double-cancelled (a booked+reversed 119 showed as -119).
            paid.append(r)
        elif not pd and (r.get("doc_date") or "") <= q_end:
            # OPEN items: a reversed original is no longer owed, and reversal rows are corrections,
            # not receivables/payables — both stay out of the open list.
            # a credit note / refund is a correction, not a receivable — same reasoning as a
            # reversal, and it belongs in the same list for the same reason
            if r.get("doc_type") not in NEGATIVE_DOC_TYPES and r.get("id") not in reversed_ids:
                open_items.append(r)

    def total(entries, direction):
        return round(sum(float(e["gross"]) * sign_of(e)
                         for e in entries if e.get("direction") == direction), 2)

    income, expense = total(paid, "income"), total(paid, "expense")
    by_cat = defaultdict(lambda: [0.0, 0.0])
    vat_in, vat_out, reverse_charge = 0.0, 0.0, []
    for e in paid:
        sign = sign_of(e)
        gross, net = float(e["gross"]) * sign, float(e["net"]) * sign
        idx = 0 if e.get("direction") == "income" else 1
        by_cat[e.get("category") or "?"][idx] = round(by_cat[e.get("category") or "?"][idx] + gross, 2)
        vat_amount = round(gross - net, 2)
        if e.get("vat_treatment") == "standard":
            if e.get("direction") == "income":
                vat_out = round(vat_out + vat_amount, 2)
            else:
                vat_in = round(vat_in + vat_amount, 2)
        elif e.get("vat_treatment") == "reverse_charge":
            reverse_charge.append(e)

    lines = ["# Einnahmen/Ausgaben-Gegenüberstellung %d Q%d" % (args.year, args.quarter), "",
             DISCLAIMER,
             "Zeitraum (Zahlungsdatum): %s bis %s · Quelle: ledger/%d.csv · generiert: %s"
             % (q_start, q_end, args.year, datetime.date.today().isoformat()), "",
             "## Summen (bezahlt im Quartal)", "",
             "| | Betrag (brutto) |", "|---|---|",
             "| Einnahmen | %.2f EUR |" % income,
             "| Ausgaben | %.2f EUR |" % expense,
             "| **Überschuss** | **%.2f EUR** |" % round(income - expense, 2), "",
             "## Nach Kategorie", "", "| Kategorie | Einnahmen | Ausgaben |", "|---|---|---|"]
    for cat in sorted(by_cat):
        lines.append("| %s | %.2f | %.2f |" % (cat, by_cat[cat][0], by_cat[cat][1]))
    lines += ["", "## Umsatzsteuer (nur informativ)", "",
              "Vereinnahmte USt (Einnahmen, standard): %.2f EUR · Vorsteuer (Ausgaben, standard): "
              "%.2f EUR · Reverse-Charge-Belege (§ 13b, netto=brutto): %d"
              % (vat_out, vat_in, len(reverse_charge))]
    lines += ["", "## Offene Posten (Belegdatum bis Quartalsende, unbezahlt)", ""]
    if open_items:
        lines += ["| Beleg | Gegenpartei | Belegdatum | Brutto |", "|---|---|---|---|"]
        for e in sorted(open_items, key=lambda x: x.get("doc_date") or ""):
            lines.append("| %s %s | %s | %s | %s EUR |"
                         % (e.get("id"), e.get("invoice_no") or "", e.get("counterparty"),
                            e.get("doc_date"), e.get("gross")))
    else:
        lines.append("keine")
    lines += ["", "_Anmerkungen der Buchhaltung: siehe reports/euer_%d_Q%d_notes.md_"
              % (args.year, args.quarter), ""]

    out_dir = os.path.join(ROOT, "reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "euer_%d_Q%d.md" % (args.year, args.quarter))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("[euer_report] %s written (%d paid entries, %d open items)"
          % (out, len(paid), len(open_items)))


if __name__ == "__main__":
    main()
