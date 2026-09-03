#!/usr/bin/env python3
"""
make_mockups.py -- DESIGN PROTOTYPE for TSK-0109, not kit code.

Renders the three mockup states of the finance dashboard from ONE template and ONE set of render
functions, so the mockups cannot drift from each other. The build phase (Opus) ports `render_page`
and the `view_*` functions into `templates/repo/tools/finance_dashboard.py` and replaces
`sample_*` with the real ledger aggregation; the arithmetic below already IMPORTS the kit's own
`euer_report.sign_of` and `ledger_add.read_ledger`, so the sign convention has one home.

States:
  regular  a Kleinunternehmer's second year, 2025 + 2026 ledgers, open and overdue items
  empty    day one: no ledger file, business_profile unfilled
  alarm    previous-year turnover above the § 19 UStG limit, one invalid ledger row, overdue items

Usage: python make_mockups.py            (writes mockup-<state>.html beside this file)
"""
import csv
import datetime
import html
import os
import random
import sys
from collections import defaultdict

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_SCRIPTS = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "team-kits", "office-team", "templates", "repo", "scripts"))
sys.path.insert(0, KIT_SCRIPTS)
sys.dont_write_bytecode = True
import euer_report  # noqa: E402  the kit's sign convention and quarter arithmetic
import ledger_add   # noqa: E402  the kit's reader, columns and validator

TEMPLATE = os.path.join(HERE, "finance-dashboard.template.html")
SAMPLE_DIR = os.path.join(HERE, "sample")

# Payment term after which an unpaid receivable is a dunning candidate. The ledger carries no
# due date and business_profile.yaml no payment term (measured 2026-09-02), so the number lives
# here until a profile field exists -- open question 3 in README.md. The source of the number is
# § 286 Abs. 3 BGB (Verzug 30 Tage nach Fälligkeit und Zugang der Rechnung).
PAYMENT_TERM_DAYS = 30

# § 19 Abs. 1 UStG in the wording in force since 2025-01-01 (JStG 2024): previous calendar year
# up to 25.000 EUR AND current year up to 100.000 EUR. One place; the page prints these values.
KLEINUNTERNEHMER_LIMIT_PREVIOUS_YEAR = 25000.0
KLEINUNTERNEHMER_LIMIT_CURRENT_YEAR = 100000.0

GERMAN_MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

CATEGORIES = {
    "income": [
        ("sales_shop", "Umsätze Onlineshop", "Betriebseinnahmen"),
        ("sales_marketplace", "Umsätze Marktplätze", "Betriebseinnahmen"),
        ("sales_local", "Umsätze Direktverkauf", "Betriebseinnahmen"),
    ],
    "expense": [
        ("goods", "Wareneinkauf", "Waren, Roh- und Hilfsstoffe"),
        ("shipping", "Versandkosten", "Übrige Betriebsausgaben"),
        ("fees_marketplace", "Marktplatzgebühren", "Übrige Betriebsausgaben"),
        ("software", "Software und Hosting", "Übrige Betriebsausgaben"),
        ("packaging", "Verpackung", "Übrige Betriebsausgaben"),
        ("advisory", "Steuerberatung", "Rechts- und Steuerberatung"),
        ("postage", "Porto", "Übrige Betriebsausgaben"),
    ],
}
COUNTERPARTIES = {
    "sales_shop": ["Shopify Payments (Auszahlung)", "PayPal (Auszahlung)"],
    "sales_marketplace": ["Amazon EU S.à r.l.", "eBay GmbH"],
    "sales_local": ["Café Morgenrot", "Buchhandlung Kessler", "Praxis Dr. Lindqvist", "Hofladen Wiese"],
    "goods": ["Nordic Glass ApS", "Holzwerk Brandt GmbH", "Leinenweberei Voss"],
    "shipping": ["DHL Paket GmbH", "Deutsche Post AG"],
    "fees_marketplace": ["Amazon EU S.à r.l.", "eBay GmbH"],
    "software": ["Shopify International Ltd.", "Hetzner Online GmbH", "sevDesk GmbH"],
    "packaging": ["Ratioform GmbH", "Karton König e.K."],
    "advisory": ["Steuerkanzlei Behrens & Ude"],
    "postage": ["Deutsche Post AG"],
}


# --- sample ledgers ----------------------------------------------------------------------------

def _rows_for_year(year, rng, kleinunternehmer, income_target, until, pay_until=None):
    """A plausible year of bookings for a small online/local seller, deterministic per seed.

    `until` bounds the DOCUMENT dates (the year's last day, or today), `pay_until` the payment
    dates: a December invoice paid in January is routine and must not read as unpaid for a year.
    """
    rows = []
    pay_until = pay_until or until
    month_weights = [0.7, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.9, 1.0, 1.2, 1.6, 1.8]
    active_months = [m for m in range(1, 13) if datetime.date(year, m, 1) <= until]
    weight_sum = sum(month_weights[m - 1] for m in active_months)
    for month in active_months:
        month_income = income_target * month_weights[month - 1] / weight_sum
        days = 28
        # income: two payout rows, a marketplace payout, two or three local invoices
        for key, share in (("sales_shop", 0.45), ("sales_marketplace", 0.35), ("sales_local", 0.20)):
            pieces = 2 if key != "sales_local" else rng.choice((2, 3))
            for _ in range(pieces):
                gross = round(month_income * share / pieces * rng.uniform(0.8, 1.2), 2)
                doc_day = rng.randint(1, days)
                doc_date = datetime.date(year, month, doc_day)
                paid = doc_date + datetime.timedelta(days=rng.choice((0, 0, 2, 5, 9, 14)))
                cp = rng.choice(COUNTERPARTIES[key])
                if key == "sales_local":
                    paid = doc_date + datetime.timedelta(days=rng.choice((7, 12, 20, 33, 48)))
                    invoice_no = "RE-%d-%03d" % (year, len(rows) + 1)
                else:
                    invoice_no = "%s-%d%02d" % ("AUSZ" if key == "sales_shop" else "SETTL", year, month)
                if kleinunternehmer:
                    net, rate, treatment = gross, 0, "kleinunternehmer"
                else:
                    net, rate, treatment = round(gross / 1.19, 2), 19, "standard"
                    gross = round(net * 1.19, 2)
                rows.append(dict(doc_date=doc_date, payment_date=(paid if paid <= pay_until else None),
                                 direction="income", doc_type="invoice", counterparty=cp,
                                 invoice_no=invoice_no, net=net, vat_rate=rate, gross=gross,
                                 vat_treatment=treatment, category=key, note=""))
        # expenses
        for key, share, pieces in (("goods", 0.38, 2), ("shipping", 0.09, 2), ("fees_marketplace", 0.07, 1),
                                   ("software", 0.04, 2), ("packaging", 0.03, 1), ("postage", 0.01, 1)):
            for _ in range(pieces):
                net = round(month_income * share / pieces * rng.uniform(0.7, 1.3), 2)
                doc_date = datetime.date(year, month, rng.randint(1, days))
                paid = doc_date + datetime.timedelta(days=rng.choice((0, 1, 3, 7, 14, 21, 30)))
                cp = rng.choice(COUNTERPARTIES[key])
                if key == "fees_marketplace":
                    rate, treatment, gross = 0, "reverse_charge", net
                else:
                    rate, treatment, gross = 19, "standard", round(net * 1.19, 2)
                if key == "postage":
                    rate, treatment, gross = 0, "exempt", net
                rows.append(dict(doc_date=doc_date, payment_date=(paid if paid <= pay_until else None),
                                 direction="expense", doc_type="invoice", counterparty=cp,
                                 invoice_no="%s-%d-%04d" % (cp.split()[0][:4].upper(), year, rng.randint(100, 9999)),
                                 net=net, vat_rate=rate, gross=gross, vat_treatment=treatment,
                                 category=key, note=""))
        if month in (3, 9):
            net = 380.0
            doc_date = datetime.date(year, month, 15)
            rows.append(dict(doc_date=doc_date, payment_date=doc_date + datetime.timedelta(days=10)
                             if doc_date + datetime.timedelta(days=10) <= pay_until else None,
                             direction="expense", doc_type="invoice",
                             counterparty=COUNTERPARTIES["advisory"][0],
                             invoice_no="STB-%d-%02d" % (year, month), net=net, vat_rate=19,
                             gross=round(net * 1.19, 2), vat_treatment="standard",
                             category="advisory", note="Jahresabschluss-Vorbereitung" if month == 3 else ""))
    rows.sort(key=lambda r: r["doc_date"])
    return rows


def _write_ledger(path, rows, year, extra=None):
    """Rows -> ledger CSV in the kit's column order, ids assigned like `ledger_add.next_id`."""
    out = []
    for n, r in enumerate(rows, start=1):
        out.append({
            "id": "L%d-%04d" % (year, n),
            "doc_date": r["doc_date"].isoformat(),
            "payment_date": r["payment_date"].isoformat() if r["payment_date"] else "",
            "direction": r["direction"], "doc_type": r["doc_type"],
            "counterparty": r["counterparty"], "invoice_no": r["invoice_no"],
            "net": "%.2f" % r["net"], "vat_rate": "%.2f" % r["vat_rate"], "gross": "%.2f" % r["gross"],
            "vat_treatment": r["vat_treatment"], "category": r["category"],
            "source": "archive/finanzen/%d/%s/%s.pdf" % (year, "eingang" if r["direction"] == "expense" else "ausgang",
                                                          r["invoice_no"].replace("/", "-")),
            "reverses": r.get("reverses", ""), "note": r["note"],
        })
    for row in (extra or []):
        out.append(row)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ledger_add.COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in out:
            writer.writerow(row)
    return out


def build_sample(state):
    """Write sample/<state>/ledger/*.csv + master_data + business_profile; return the project root."""
    root = os.path.join(SAMPLE_DIR, state)
    ledger_dir = os.path.join(root, "ledger")
    profile = {"business": {"name": "Nordlicht Handel", "legal_form": "Einzelunternehmen"},
               "tax": {"kleinunternehmer": True, "fiscal_year": "calendar"}}
    if state == "empty":
        os.makedirs(root, exist_ok=True)
        profile = {"business": {"name": "", "legal_form": ""}, "tax": {"kleinunternehmer": None}}
        _write_json(os.path.join(root, "business_profile.yaml"), profile)
        _write_json(os.path.join(root, "master_data.yaml"), {"categories": {"income": [], "expense": []}})
        return root
    until = datetime.date(2026, 8, 30)
    rng = random.Random(2026 if state == "regular" else 2027)
    prev_target = 19800.0 if state == "regular" else 27400.0
    rows_2025 = _rows_for_year(2025, rng, True, prev_target, datetime.date(2025, 12, 31), pay_until=until)
    rows_2026 = _rows_for_year(2026, rng, True, 41000.0 * 12 / 8, until)
    # two local customers who have not paid for a while: the dunning candidates the page is about
    stale = [r for r in rows_2026 if r["category"] == "sales_local" and "2026-06" <= r["doc_date"].isoformat() < "2026-08"][:2]
    for r in stale:
        r["payment_date"] = None
    # the ledger's own file rule (`ledger_add.validate_cross`): a row lives in the file of its
    # PAYMENT year, so a December invoice paid in January is a 2026 row
    carried = [r for r in rows_2025 if r["payment_date"] and r["payment_date"].year == 2026]
    rows_2025 = [r for r in rows_2025 if r not in carried]
    rows_2026.extend(carried)
    # a credit note and a reversal, so the sign convention is visible on the page
    rows_2026.append(dict(doc_date=datetime.date(2026, 5, 19), payment_date=datetime.date(2026, 5, 26),
                          direction="income", doc_type="credit_note", counterparty="Café Morgenrot",
                          invoice_no="GS-2026-002", net=84.0, vat_rate=0, gross=84.0,
                          vat_treatment="kleinunternehmer", category="sales_local",
                          note="Bruchware, Teilgutschrift zu RE-2026-031"))
    rows_2026.sort(key=lambda r: r["doc_date"])
    _write_ledger(os.path.join(ledger_dir, "2025.csv"), rows_2025, 2025)
    extra = []
    # reversal of a duplicated expense booking
    target = next(r for r in rows_2026 if r["direction"] == "expense" and r["category"] == "packaging")
    target_index = rows_2026.index(target)
    extra.append({"id": "L2026-%04d" % (len(rows_2026) + 1), "doc_date": "2026-07-02", "payment_date": "2026-07-02",
                  "direction": "expense", "doc_type": "reversal", "counterparty": target["counterparty"],
                  "invoice_no": "", "net": "%.2f" % target["net"], "vat_rate": "%.2f" % target["vat_rate"],
                  "gross": "%.2f" % target["gross"], "vat_treatment": target["vat_treatment"],
                  "category": "packaging", "source": "archive/finanzen/2026/eingang/storno-L2026-%04d.txt" % (target_index + 1),
                  "reverses": "L2026-%04d" % (target_index + 1), "note": "Doppelt gebucht"})
    if state == "alarm":
        extra.append({"id": "L2026-%04d" % (len(rows_2026) + 2), "doc_date": "2026-08-28", "payment_date": "",
                      "direction": "expense", "doc_type": "invoice", "counterparty": "Holzwerk Brandt GmbH",
                      "invoice_no": "HB-2026-7781", "net": "214.20", "vat_rate": "19.00", "gross": "14.28",
                      "vat_treatment": "standard", "category": "goods",
                      "source": "archive/finanzen/2026/eingang/HB-2026-7781.pdf", "reverses": "", "note": ""})
    _write_ledger(os.path.join(ledger_dir, "2026.csv"), rows_2026, 2026, extra)
    _write_json(os.path.join(root, "business_profile.yaml"), profile)
    _write_json(os.path.join(root, "master_data.yaml"), {"categories": {
        d: [{"key": key, "label_de": label, "euer_line": line} for key, label, line in CATEGORIES[d]] for d in CATEGORIES}})
    return root


def _write_json(path, data):
    """The kit documents are YAML (`templates/project_memory/*.yaml`); the fixture keeps that shape."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


# --- aggregation (the build ports this into the generator) --------------------------------------

def fmt_eur(value, sign=1):
    """1234.5 -> '1.234,50 €'; corrections carry a real minus (U+2212)."""
    cents = int(round(abs(value) * 100))
    euros, rest = divmod(cents, 100)
    body = "{:,}".format(euros).replace(",", ".") + "," + "%02d" % rest + " €"
    return ("−" + body) if (value * sign) < 0 else body


def fmt_date(iso):
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return "%s.%s.%s" % (d, m, y)


def load_project(root):
    """Everything the page renders, read off the sample project the way the generator will."""
    profile = _read_json(os.path.join(root, "business_profile.yaml"))
    master = _read_json(os.path.join(root, "master_data.yaml"))
    categories = {}
    for direction in ("income", "expense"):
        for entry in (master.get("categories") or {}).get(direction) or []:
            categories[entry["key"]] = {"label": entry.get("label_de") or entry["key"],
                                        "euer_line": entry.get("euer_line") or "", "direction": direction}
    ledger_dir = os.path.join(root, "ledger")
    sources, rows = [], []
    names = sorted(os.listdir(ledger_dir)) if os.path.isdir(ledger_dir) else []
    for name in names:
        if not ledger_add.YEAR_FILE_RX.match(name):
            continue
        path = os.path.join(ledger_dir, name)
        findings = ledger_add.validate_file(path)
        loaded, error = ledger_add.read_ledger(path)
        year = name[:4]
        sources.append({"file": "ledger/" + name, "year": year, "rows": len(loaded or []),
                        "valid": not findings and not error, "findings": findings or ([error] if error else [])})
        for r in loaded or []:
            rows.append(dict(r, year=year))
    reversed_ids = {r["reverses"] for r in rows if r.get("doc_type") == "reversal" and r.get("reverses")}
    for r in rows:
        r["sign"] = euer_report.sign_of(r)
        r["cents"] = int(round(_num(r["gross"]) * 100)) * r["sign"]
        r["net_cents"] = int(round(_num(r["net"]) * 100)) * r["sign"]
        if r["id"] in reversed_ids:
            r["status"] = "storniert"
        elif r["doc_type"] in euer_report.NEGATIVE_DOC_TYPES:
            r["status"] = "korrektur"
        elif r.get("payment_date"):
            r["status"] = "bezahlt"
        else:
            r["status"] = "offen"
        r["category_label"] = categories.get(r["category"], {}).get("label") or r["category"]
        r["euer_line"] = categories.get(r["category"], {}).get("euer_line") or ""
        r["quarter"] = "Q%d" % ((int(r["doc_date"][5:7]) - 1) // 3 + 1)
    rows.sort(key=lambda r: (r["doc_date"], r["id"]), reverse=True)
    years = sorted({s["year"] for s in sources}, reverse=True)
    return {
        "business": {"name": (profile.get("business") or {}).get("name") or "",
                     "legal_form": (profile.get("business") or {}).get("legal_form") or "",
                     "kleinunternehmer": (profile.get("tax") or {}).get("kleinunternehmer")},
        "sources": sources, "rows": rows, "years": years, "categories": categories,
        "datenstand": max([r["doc_date"] for r in rows] + [r["payment_date"] for r in rows if r["payment_date"]] or [""]),
        "valid": all(s["valid"] for s in sources),
    }


def _read_json(path):
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _num(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def paid_in(rows, year, quarter=None):
    """Zufluss/Abfluss: by PAYMENT date, the way euer_report.py counts."""
    if quarter:
        start, end = euer_report.quarter_range(int(year), quarter)
    else:
        start, end = "%s-01-01" % year, "%s-12-31" % year
    return [r for r in rows if r["payment_date"] and start <= r["payment_date"] <= end]


def totals(entries):
    income = sum(r["cents"] for r in entries if r["direction"] == "income")
    expense = sum(r["cents"] for r in entries if r["direction"] == "expense")
    return income, expense


def open_items(rows, direction):
    return [r for r in rows if r["status"] == "offen" and r["direction"] == direction]


def threshold(data):
    """§ 19 UStG watch: only when the profile says the business uses the rule."""
    if data["business"]["kleinunternehmer"] is not True or not data["years"]:
        return None
    current = data["years"][0]
    previous = str(int(current) - 1)
    cur_income = totals(paid_in(data["rows"], current))[0] / 100.0
    prev_income = totals(paid_in(data["rows"], previous))[0] / 100.0 if previous in data["years"] else None
    verdict = "within"
    if prev_income is not None and prev_income > KLEINUNTERNEHMER_LIMIT_PREVIOUS_YEAR:
        verdict = "previous_exceeded"
    if cur_income > KLEINUNTERNEHMER_LIMIT_CURRENT_YEAR:
        verdict = "current_exceeded"
    return {"current_year": current, "previous_year": previous, "current": cur_income,
            "previous": prev_income, "verdict": verdict,
            "limit_previous": KLEINUNTERNEHMER_LIMIT_PREVIOUS_YEAR,
            "limit_current": KLEINUNTERNEHMER_LIMIT_CURRENT_YEAR}


# --- rendering ---------------------------------------------------------------------------------

def e(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def source_line(data, year=None, count=None, label="Zeilen"):
    files = [s for s in data["sources"] if year is None or s["year"] == year]
    names = ", ".join(s["file"] for s in files) or "kein Ledger"
    n = count if count is not None else sum(s["rows"] for s in files)
    return '<span class="src">aus %s · %d %s</span>' % (e(names), n, e(label))


def view_ueberblick(data):
    if not data["years"]:
        return ('<section id="view-ueberblick" class="view" role="tabpanel">'
                '<div class="empty"><p class="empty-lead">Noch keine Buchung.</p>'
                '<p>Diese Seite rechnet aus <code>ledger/&lt;Jahr&gt;.csv</code>. Die erste Buchung schreibt '
                'die Buchhaltung mit <code>python scripts/ledger_add.py</code> — sobald eine Zeile dort steht, '
                'stehen hier Einnahmen, Ausgaben und Überschuss.</p></div></section>')
    year = data["years"][0]
    parts = ['<section id="view-ueberblick" class="view" role="tabpanel">']
    parts.append('<div class="toolbar"><label>Jahr <select data-filter="year" data-scope="ueberblick">%s</select></label></div>'
                 % "".join('<option value="%s">%s</option>' % (y, y) for y in data["years"]))
    for y in data["years"]:
        paid = paid_in(data["rows"], y)
        income, expense = totals(paid)
        hidden = "" if y == year else " hidden"
        parts.append('<div class="year-block" data-year="%s"%s>' % (y, hidden))
        parts.append('<div class="ledger-row kpis">')
        for label, cents, cls in (("Einnahmen", income, ""), ("Ausgaben", expense, ""), ("Überschuss", income - expense, " total")):
            parts.append('<div class="kpi%s"><span class="label">%s</span><span class="figure">%s</span>%s</div>'
                         % (cls, label, e(fmt_eur(cents / 100.0)), source_line(data, y, len(paid), "bezahlte Zeilen")))
        parts.append('</div>')
        parts.append('<p class="rule-note">Zahlungsprinzip: gezählt wird, was im Jahr %s bezahlt wurde (Zufluss/Abfluss). '
                     'Offene Rechnungen stehen unter <a href="#offene-posten">Offene Posten</a>.</p>' % y)
        # what is due now
        rec, pay = open_items(data["rows"], "income"), open_items(data["rows"], "expense")
        th = threshold(data)
        parts.append('<h2>Jetzt ansteht</h2><ul class="due">')
        parts.append('<li><a href="#offene-posten"><span class="figure-s" data-due-count="receivables">%d</span> offene Forderungen · '
                     '<span data-due-sum="receivables">%s</span></a> <span class="muted">— davon <span data-overdue-count>…</span> Mahnkandidaten, '
                     'älter als %d Tage</span></li>' % (len(rec), e(fmt_eur(sum(r["cents"] for r in rec) / 100.0)), PAYMENT_TERM_DAYS))
        parts.append('<li><a href="#offene-posten"><span class="figure-s">%d</span> Rechnungen zu zahlen · %s</a></li>'
                     % (len(pay), e(fmt_eur(sum(r["cents"] for r in pay) / 100.0))))
        if th:
            verdict = {"within": "innerhalb der Grenzen",
                       "previous_exceeded": "Vorjahresgrenze überschritten — Regelbesteuerung seit 1. Januar prüfen",
                       "current_exceeded": "Grenze im laufenden Jahr überschritten — ab dem überschreitenden Umsatz Regelbesteuerung"}[th["verdict"]]
            cls = "" if th["verdict"] == "within" else ' class="alarm"'
            parts.append('<li%s><a href="#kleinunternehmer">Kleinunternehmer § 19 UStG: %s</a> <span class="muted">— %s von %s laufend, Vorjahr %s von %s</span></li>'
                         % (cls, e(verdict), e(fmt_eur(th["current"])), e(fmt_eur(th["limit_current"])),
                            e(fmt_eur(th["previous"]) if th["previous"] is not None else "kein Vorjahr"), e(fmt_eur(th["limit_previous"]))))
        elif data["business"]["kleinunternehmer"] is None:
            parts.append('<li class="muted">Steuerstatus nicht hinterlegt — <code>business_profile.yaml</code> <code>tax.kleinunternehmer</code> ist leer, '
                         'darum gibt es keine Schwellenwache.</li>')
        parts.append('<li>%s</li>' % ('Ledger geprüft: <span class="stamp ok">gültig</span>' if data["valid"]
                                      else 'Ledger geprüft: <span class="stamp alarm">ungültig</span> — die Summen oben sind nicht belastbar, Befunde im Kopf der Seite'))
        parts.append('</ul>')
        # monthly flow
        months = []
        for m in range(1, 13):
            entries = [r for r in paid if int(r["payment_date"][5:7]) == m]
            months.append(totals(entries))
        peak = max([max(i, x) for i, x in months] + [1])
        parts.append('<h2>Monat für Monat <span class="muted">(bezahlt, brutto)</span></h2><div class="flow">')
        for m, (i, x) in enumerate(months):
            parts.append('<div class="month"><div class="bars"><span class="bar in" style="height:%d%%" title="Einnahmen %s"></span>'
                         '<span class="bar out" style="height:%d%%" title="Ausgaben %s"></span></div><span class="mlabel">%s</span></div>'
                         % (round(100 * i / peak), e(fmt_eur(i / 100)), round(100 * x / peak), e(fmt_eur(x / 100)), GERMAN_MONTHS[m]))
        parts.append('</div><p class="legend"><span class="sw in"></span> Einnahmen <span class="sw out"></span> Ausgaben</p>')
        # last bookings
        parts.append('<h2>Zuletzt gebucht</h2><table class="ledger compact">%s</table>'
                     % "".join(row_html(r, compact=True) for r in [r for r in data["rows"] if r["year"] == y][:6]))
        parts.append('<p class="more"><a href="#rechnungen">Alle Buchungen →</a></p>')
        parts.append('</div>')
    parts.append('</section>')
    return "".join(parts)


def row_html(r, compact=False):
    struck = ' class="struck"' if r["status"] == "storniert" else ""
    stamp = {"bezahlt": '<span class="stamp ok">bezahlt</span>', "offen": '<span class="stamp open">offen</span>',
             "storniert": '<span class="stamp muted">storniert</span>', "korrektur": '<span class="stamp muted">Korrektur</span>'}[r["status"]]
    text = " ".join([r["counterparty"], r["invoice_no"], r["id"], r["note"], r["category_label"]]).lower()
    attrs = ('data-year="%s" data-q="%s" data-dir="%s" data-status="%s" data-cat="%s" data-cp="%s" data-cents="%d" '
             'data-doc-date="%s" data-text="%s"' % (r["year"], r["quarter"], r["direction"], r["status"], e(r["category"]),
                                                   e(r["counterparty"]), r["cents"], r["doc_date"], e(text)))
    amount = fmt_eur(r["cents"] / 100.0)
    if compact:
        return ('<tr %s%s><td class="date">%s</td><td class="cp">%s <span class="muted small">%s</span></td>'
                '<td class="amt %s">%s</td><td class="st">%s</td></tr>'
                % (attrs, struck, e(fmt_date(r["doc_date"])), e(r["counterparty"]), e(r["category_label"]),
                   r["direction"], e(amount), stamp))
    detail = ('<dl><dt>Beleg-Id</dt><dd><code>%s</code></dd><dt>Belegart</dt><dd>%s</dd><dt>USt-Behandlung</dt><dd>%s</dd>'
              '<dt>Quelle</dt><dd><code>%s</code></dd>%s%s</dl>'
              % (e(r["id"]), e(r["doc_type"]), e(r["vat_treatment"]), e(r["source"]),
                 '<dt>Storniert</dt><dd><code>%s</code></dd>' % e(r["reverses"]) if r["reverses"] else "",
                 '<dt>Notiz</dt><dd>%s</dd>' % e(r["note"]) if r["note"] else ""))
    return ('<tr %s%s><td class="date">%s</td><td class="no"><code>%s</code></td><td class="cp">%s</td>'
            '<td class="cat">%s</td><td class="amt">%s</td><td class="amt">%s</td><td class="amt %s">%s</td>'
            '<td class="pay">%s</td><td class="st">%s</td></tr>'
            '<tr class="detail" hidden><td colspan="9">%s</td></tr>'
            % (attrs, struck, e(fmt_date(r["doc_date"])), e(r["invoice_no"] or "—"), e(r["counterparty"]),
               e(r["category_label"]), e(fmt_eur(r["net_cents"] / 100.0)), e(fmt_eur((r["cents"] - r["net_cents"]) / 100.0)),
               r["direction"], e(amount), e(fmt_date(r["payment_date"]) or "—"), stamp, detail))


def view_rechnungen(data):
    if not data["years"]:
        return '<section id="view-rechnungen" class="view" role="tabpanel" hidden><div class="empty"><p class="empty-lead">Keine Rechnungen.</p><p>Die Liste füllt sich mit der ersten Buchung.</p></div></section>'
    cats = sorted({(r["category"], r["category_label"]) for r in data["rows"]}, key=lambda t: t[1])
    cps = sorted({r["counterparty"] for r in data["rows"]})
    def opt(pairs):
        return "".join('<option value="%s">%s</option>' % (e(value), e(label)) for value, label in pairs)
    parts = ['<section id="view-rechnungen" class="view" role="tabpanel" hidden>']
    parts.append('<form class="filters" data-scope="rechnungen" onsubmit="return false">'
                 '<input type="search" data-filter="text" placeholder="Suchen: Gegenpartei, Rechnungsnummer, Notiz" aria-label="Suchen">'
                 '<label>Richtung <select data-filter="dir"><option value="">alle</option><option value="income">Einnahmen</option><option value="expense">Ausgaben</option></select></label>'
                 '<label>Status <select data-filter="status"><option value="">alle</option><option value="offen">offen</option><option value="bezahlt">bezahlt</option><option value="storniert">storniert</option><option value="korrektur">Korrekturen</option></select></label>'
                 '<label>Jahr <select data-filter="year"><option value="">alle</option>%s</select></label>'
                 '<label>Quartal <select data-filter="q"><option value="">alle</option><option>Q1</option><option>Q2</option><option>Q3</option><option>Q4</option></select></label>'
                 '<label>Kategorie <select data-filter="cat"><option value="">alle</option>%s</select></label>'
                 '<label>Gegenpartei <select data-filter="cp"><option value="">alle</option>%s</select></label>'
                 '<button type="reset" class="link">Filter zurücksetzen</button></form>'
                 % (opt([(y, y) for y in data["years"]]), opt(cats), opt([(c, c) for c in cps])))
    parts.append('<p class="count"><span data-count>%d</span> von %d Buchungen · Summe brutto <span class="figure-s total" data-sum>%s</span> %s</p>'
                 % (len(data["rows"]), len(data["rows"]), e(fmt_eur(sum(r["cents"] for r in data["rows"]) / 100.0)), source_line(data)))
    parts.append('<table class="ledger full"><thead><tr><th>Datum</th><th>Nr.</th><th>Gegenpartei</th><th>Kategorie</th>'
                 '<th class="amt">Netto</th><th class="amt">USt</th><th class="amt">Brutto</th><th>Bezahlt am</th><th>Status</th></tr></thead><tbody>')
    parts.extend(row_html(r) for r in data["rows"])
    parts.append('</tbody></table><p class="show-all"><button type="button" class="link">alle anzeigen</button></p>'
                 '<p class="hint">Eine Zeile aufklappen zeigt Beleg-Id, Belegart, USt-Behandlung und die Quelle im Archiv. '
                 'Korrekturen (Gutschrift, Erstattung, Storno) stehen mit Minus in der Summe, so wie <code>euer_report.py</code> sie zählt.</p></section>')
    return "".join(parts)


def view_offene_posten(data):
    parts = ['<section id="view-offene-posten" class="view" role="tabpanel" hidden>']
    if not data["years"]:
        parts.append('<div class="empty"><p class="empty-lead">Keine offenen Posten.</p><p>Eine Buchung ohne Zahlungsdatum erscheint hier.</p></div></section>')
        return "".join(parts)
    parts.append('<div class="toolbar"><label class="check"><input type="checkbox" data-filter="overdue" data-scope="offene-posten"> nur Mahnkandidaten '
                 '<span class="muted">(Forderung älter als %d Tage, Stand heute)</span></label></div>' % PAYMENT_TERM_DAYS)
    for direction, title, lead in (("income", "Forderungen", "Was Kunden uns noch schulden"),
                                   ("expense", "Verbindlichkeiten", "Was wir noch zu zahlen haben")):
        items = sorted(open_items(data["rows"], direction), key=lambda r: r["doc_date"])
        parts.append('<h2>%s <span class="muted">— %s</span></h2>' % (title, lead))
        if not items:
            parts.append('<p class="empty-inline">Nichts offen.</p>')
            continue
        parts.append('<table class="ledger open" data-direction="%s"><thead><tr><th>Belegdatum</th><th>Alter</th><th>Nr.</th><th>Gegenpartei</th><th class="amt">Brutto</th><th></th></tr></thead><tbody>' % direction)
        for r in items:
            parts.append('<tr data-doc-date="%s" data-dir="%s" data-cents="%d" data-cp="%s"><td class="date">%s</td><td class="age" data-age>—</td><td class="no"><code>%s</code></td>'
                         '<td class="cp">%s <span class="muted small">%s</span></td><td class="amt %s">%s</td><td class="st" data-dun></td></tr>'
                         % (r["doc_date"], direction, r["cents"], e(r["counterparty"]), e(fmt_date(r["doc_date"])), e(r["invoice_no"] or "—"),
                            e(r["counterparty"]), e(r["category_label"]), direction, e(fmt_eur(r["cents"] / 100.0))))
        parts.append('</tbody><tfoot><tr class="sum"><td colspan="4">Summe <span class="muted">(<span data-count>%d</span> Posten)</span></td><td class="amt total" data-sum>%s</td><td></td></tr></tfoot></table>'
                     % (len(items), e(fmt_eur(sum(r["cents"] for r in items) / 100.0))))
    parts.append('<p class="hint">Alter = Tage seit Belegdatum, gerechnet beim Öffnen der Seite. Das Ledger kennt kein Fälligkeitsdatum; '
                 'die Frist von %d Tagen ist die gesetzliche Verzugsfrist (§ 286 Abs. 3 BGB). Ohne Skript bleibt die Spalte Alter leer.</p></section>' % PAYMENT_TERM_DAYS)
    return "".join(parts)


def view_euer(data):
    parts = ['<section id="view-euer" class="view" role="tabpanel" hidden>']
    if not data["years"]:
        parts.append('<div class="empty"><p class="empty-lead">Noch keine Einnahmen-Ausgaben-Rechnung.</p><p>Sie entsteht aus dem Ledger, Quartal für Quartal.</p></div></section>')
        return "".join(parts)
    parts.append('<div class="toolbar"><label>Jahr <select data-filter="year" data-scope="euer">%s</select></label>'
                 '<label>Zeitraum <select data-filter="period" data-scope="euer"><option value="year">ganzes Jahr</option>'
                 '<option value="1">Q1</option><option value="2">Q2</option><option value="3">Q3</option><option value="4">Q4</option></select></label></div>'
                 % "".join('<option value="%s">%s</option>' % (y, y) for y in data["years"]))
    for y in data["years"]:
        for period in ("year", 1, 2, 3, 4):
            paid = paid_in(data["rows"], y, None if period == "year" else period)
            income, expense = totals(paid)
            by_cat = defaultdict(lambda: [0, 0])
            vat_in = vat_out = 0
            rc = 0
            for r in paid:
                by_cat[(r["category_label"], r["euer_line"])][0 if r["direction"] == "income" else 1] += r["cents"]
                vat = r["cents"] - r["net_cents"]
                if r["vat_treatment"] == "standard":
                    if r["direction"] == "income":
                        vat_out += vat
                    else:
                        vat_in += vat
                elif r["vat_treatment"] == "reverse_charge":
                    rc += 1
            if period == "year":
                q_end = "%s-12-31" % y
                label = "Jahr %s" % y
            else:
                q_end = euer_report.quarter_range(int(y), period)[1]
                label = "%s Q%d" % (y, period)
            open_count = len([r for r in data["rows"] if r["status"] == "offen" and r["doc_date"] <= q_end])
            hidden = "" if (y == data["years"][0] and period == "year") else " hidden"
            parts.append('<div class="euer-block" data-year="%s" data-period="%s"%s>' % (y, period, hidden))
            parts.append('<h2>Einnahmen-Ausgaben-Gegenüberstellung %s <span class="muted">(bezahlt im Zeitraum, brutto)</span></h2>' % label)
            parts.append('<table class="ledger sums"><tbody><tr><td>Einnahmen</td><td class="amt">%s</td></tr><tr><td>Ausgaben</td><td class="amt">%s</td></tr>'
                         '<tr class="sum"><td>Überschuss</td><td class="amt total">%s</td></tr></tbody></table>%s'
                         % (e(fmt_eur(income / 100)), e(fmt_eur(expense / 100)), e(fmt_eur((income - expense) / 100)), source_line(data, y, len(paid), "bezahlte Zeilen")))
            parts.append('<h3>Nach Kategorie</h3><table class="ledger cats"><thead><tr><th>Kategorie</th><th>Zeile Anlage EÜR</th><th class="amt">Einnahmen</th><th class="amt">Ausgaben</th></tr></thead><tbody>')
            for (lab, line), (i, x) in sorted(by_cat.items()):
                parts.append('<tr><td>%s</td><td class="muted">%s</td><td class="amt">%s</td><td class="amt">%s</td></tr>'
                             % (e(lab), e(line or "—"), e(fmt_eur(i / 100)) if i else "", e(fmt_eur(x / 100)) if x else ""))
            parts.append('</tbody></table>')
            parts.append('<h3>Umsatzsteuer <span class="muted">(nur informativ)</span></h3><p>Vereinnahmte USt (standard): %s · Vorsteuer (standard): %s · Reverse-Charge-Belege (§ 13b): %d</p>'
                         % (e(fmt_eur(vat_out / 100)), e(fmt_eur(vat_in / 100)), rc))
            parts.append('<p class="muted">Offene Posten bis Zeitraumende: %d — <a href="#offene-posten">Liste</a></p>' % open_count)
            parts.append('</div>')
    parts.append('<p class="hint">Der Bericht für die Steuerberatung entsteht mit <code>python scripts/euer_report.py --year … --quarter …</code> unter '
                 '<code>reports/</code>. Diese Ansicht rechnet mit derselben Vorzeichenregel nach und ersetzt ihn nicht. Keine Steuerberatung.</p></section>')
    return "".join(parts)


def view_kleinunternehmer(data):
    th = threshold(data)
    parts = ['<section id="view-kleinunternehmer" class="view" role="tabpanel" hidden>']
    if th is None:
        if data["business"]["kleinunternehmer"] is False:
            parts.append('<div class="empty"><p class="empty-lead">Regelbesteuerung.</p><p><code>business_profile.yaml</code> sagt <code>tax.kleinunternehmer: false</code> — es gibt keine Umsatzgrenze zu beobachten.</p></div>')
        else:
            parts.append('<div class="empty"><p class="empty-lead">Steuerstatus nicht hinterlegt.</p><p>Die Schwellenwache rechnet erst, wenn <code>business_profile.yaml</code> unter <code>tax.kleinunternehmer</code> <code>true</code> trägt und ein Ledger Buchungen hat.</p></div>')
        parts.append('</section>')
        return "".join(parts)
    def gauge(value, limit, label, year):
        pct = min(100, round(100 * value / limit)) if value is not None else 0
        state = "alarm" if (value or 0) > limit else ("warn" if pct >= 80 else "")
        figure = fmt_eur(value) if value is not None else "kein Ledger"
        return ('<div class="gauge %s"><div class="gauge-head"><span class="label">%s %s</span><span class="figure-s">%s <span class="muted">von %s</span></span></div>'
                '<div class="track"><span class="fill" style="width:%d%%"></span><span class="limit-mark"></span></div>'
                '<div class="gauge-foot"><span>%d %%</span><span>%s</span></div></div>'
                % (state, e(label), year, e(figure), e(fmt_eur(limit)), pct, pct,
                   e("Rest %s" % fmt_eur(limit - value)) if value is not None and value <= limit else e("über der Grenze")))
    parts.append('<h2>Kleinunternehmergrenze § 19 UStG</h2>')
    parts.append('<p class="lead">Beide Bedingungen müssen gelten: Gesamtumsatz im Vorjahr bis %s <strong>und</strong> im laufenden Jahr bis %s. '
                 'Gezählt werden die bezahlten Einnahmen (Zufluss), brutto gleich netto, Korrekturen abgezogen.</p>'
                 % (e(fmt_eur(th["limit_previous"])), e(fmt_eur(th["limit_current"]))))
    parts.append(gauge(th["previous"], th["limit_previous"], "Vorjahr", th["previous_year"]))
    parts.append(gauge(th["current"], th["limit_current"], "Laufendes Jahr", th["current_year"]))
    verdict = {"within": ('ok', 'Innerhalb der Grenzen.'),
               "previous_exceeded": ('alarm', 'Der Vorjahresumsatz liegt über %s: die Kleinunternehmerregelung gilt seit dem 1. Januar %s nicht mehr. Mit der Steuerberatung klären, ab wann Umsatzsteuer auszuweisen ist.' % (fmt_eur(th["limit_previous"]), th["current_year"])),
               "current_exceeded": ('alarm', 'Der Umsatz des laufenden Jahres liegt über %s: ab dem Umsatz, der die Grenze überschritten hat, gilt die Regelbesteuerung.' % fmt_eur(th["limit_current"]))}[th["verdict"]]
    parts.append('<p class="verdict"><span class="stamp %s">%s</span> %s</p>' % (verdict[0], "innerhalb" if verdict[0] == "ok" else "überschritten", e(verdict[1])))
    parts.append('<p class="hint">Grenzen nach § 19 Abs. 1 UStG in der seit 1. Januar 2025 geltenden Fassung. Diese Seite ersetzt keine Steuerberatung.</p></section>')
    return "".join(parts)


def render_page(data):
    with open(TEMPLATE, encoding="utf-8") as fh:
        template = fh.read()
    name = data["business"]["name"] or "Dieses Unternehmen"
    banner = ""
    if not data["valid"]:
        findings = [f for s in data["sources"] for f in s["findings"]]
        banner = ('<div class="banner alarm" role="alert"><strong>Ledger ungültig.</strong> Die Summen auf dieser Seite sind nicht belastbar, bis die Zeile korrigiert ist. '
                  '<code>python scripts/ledger_add.py --validate ledger/&lt;Jahr&gt;.csv</code> zeigt alles.<ul>%s</ul></div>'
                  % "".join("<li>%s</li>" % e(f) for f in findings[:6]))
    th = threshold(data)
    show_ku = data["business"]["kleinunternehmer"] is not False
    tabs = [("ueberblick", "Überblick"), ("rechnungen", "Rechnungen"), ("offene-posten", "Offene Posten"), ("euer", "EÜR")]
    if show_ku:
        tabs.append(("kleinunternehmer", "Kleinunternehmer" + (' <span class="dot"></span>' if th and th["verdict"] != "within" else "")))
    nav = "".join('<button role="tab" data-view="%s" aria-selected="%s">%s</button>' % (view, "true" if i == 0 else "false", label)
                  for i, (view, label) in enumerate(tabs))
    stand = ("Datenstand %s · %s · %d Buchungen" % (fmt_date(data["datenstand"]), ", ".join(s["file"] for s in data["sources"]),
                                                    sum(s["rows"] for s in data["sources"])) if data["years"] else "Kein Ledger unter ledger/")
    body = "".join([view_ueberblick(data), view_rechnungen(data), view_offene_posten(data), view_euer(data),
                    view_kleinunternehmer(data)])
    return (template.replace("{{title}}", e(name)).replace("{{legal_form}}", e(data["business"]["legal_form"]))
            .replace("{{stand}}", e(stand)).replace("{{banner}}", banner).replace("{{nav}}", nav).replace("{{views}}", body)
            .replace("{{payment_term_days}}", str(PAYMENT_TERM_DAYS)))


def main():
    for state in ("regular", "empty", "alarm"):
        root = build_sample(state)
        data = load_project(root)
        out = os.path.join(HERE, "mockup-%s.html" % state)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_page(data))
        print("%s: %d rows, valid=%s -> %s" % (state, len(data["rows"]), data["valid"], os.path.basename(out)))


if __name__ == "__main__":
    main()
