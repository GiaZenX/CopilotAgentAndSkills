"""User decision 2026-09-05: the invoice application is its OWN product (dev-team project with UI for
the user and a command surface for the office roles), not a script in the office kit. PR-0009 (DRAFT,
still updatable) loses FR-0073 and gains the DOCKING POINT instead: intake, validation, filing and
booking of invoices the external app produces. Body on stdin to `kernel.cli update PR-0009`."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "update", "PR-0009"]

BODY = {
    "title": "G5-3 Office package: correspondence capability (FR-0033), the docking point for the external invoice application (intake, validation, filing, booking), a year-versioned chart of accounts with EUeR mapping (FR-0081), the eight takeovers from a real operation (FR-0002), and the four open office bugs (BUG-0070/0071/0072/0079)",
    "problem": "The office kit reads and files documents and keeps a ledger, but it cannot WRITE outward: no correspondence role or workflow (FR-0033), no chart of accounts (FR-0081 -- SKR03/SKR04 with account-to-EUeR-line mapping, year-versioned, legal space named), and the eight measured takeovers from the user's real operation (FR-0002) are still prose. Outgoing invoices are NOT built here: the user decided 2026-09-05 that the invoice application (product catalogue, two businesses with their own number ranges, marketplace importers for eBay / Kaufland / Shopify, designed templates, UI, PDF + e-invoice, GoBD / paragraph 14 UStG) is its own dev-team product; the office kit is its consumer and needs a docking point. Live use measured four dead ends or wrong figures: add-filing-rule cannot create the rules list (BUG-0070), categories have no kernel writer (BUG-0071), einvoice_extract.py returned a non-reconciling net from a real invoice (BUG-0072), documents.py prints a remedy it refuses (BUG-0079).",
    "goal": "The office kit gains the outward half it owns: a correspondence capability (role or teachable workflow, decided DEC-first with the user), a chart-of-accounts template with the EUeR mapping as a year-versioned kit document with a kernel writer, the eight takeovers absorbed where they belong, and a DOCKING POINT for the external invoice application: an intake route that takes an invoice file the app produced (PDF with embedded XML or XML), validates it (norm rules, net x (1+vat) = gross, number-range continuity per business), files it through the sanctioned document route and books it -- the same reader path that BUG-0072 hardens; the four bugs closed red-first; every new document class has a kernel writer and every printed remedy is a line the kernel accepts.",
    "acceptance_criteria": [
        {"id": "AC-1", "text": "FR-0033: a DEC decides role vs teachable workflow with the user; then a scaffolded office pilot produces an offer, a reminder (Mahnung) and a customer letter from ledger + master data through the sanctioned document route, each reviewed before it leaves (gate or duty named), measured end to end; the texts pass the humanizer/plain-language bar the kit already ships"},
        {"id": "AC-2", "text": "Docking point for the invoice application: an intake route accepts an invoice file the external app produced (fixture set: one PDF/ZUGFeRD, one XRechnung XML), validates norm rules and the reconciling triple, checks number-range continuity per business against the ledger, files it through the document route and books it -- a planted violation (broken triple, gap in the number range, missing mandatory field) is refused with the figures named; the interface contract (file shape, where it is dropped, what the kit answers) is written down for the app project; measured on a pilot; red-first"},
        {"id": "AC-3", "text": "FR-0081: SKR03/SKR04 as year-versioned kit documents with the account-to-EUeR-line mapping and the legal space named; the bookkeeper's booking names an account and the EUeR rollup reads the mapping; a kernel writer exists for the document (no editor line); measured on a pilot"},
        {"id": "AC-4", "text": "FR-0002: each of the eight takeovers is either built in this goal with its own acceptance line, absorbed by another item (named), or rejected with the reason -- none stays prose without a verdict"},
        {"id": "AC-5", "text": "BUG-0070 + BUG-0071: add-filing-rule creates the rules list when the plan carries none; categories (and, decided in the round, every kit-document list) get a sanctioned approval-gated kernel writer -- special case vs general mechanism decided with reasons (P4-12 lineage); red-first on an old-stock copy outside the repo"},
        {"id": "AC-6", "text": "BUG-0072 + BUG-0079: einvoice_extract.py returns the reconciling document total from CII structures and fails loudly on a non-reconciling triple (both directions tested); every remedy line the kernel prints is executed by a test against the CLI and accepted; red-first"},
    ],
    "out_of_scope": [
        "Producing outgoing invoices (FR-0073): the invoice application is its own dev-team product with UI and command surface -- planned with the user in its own entry interview; this goal builds only the intake side",
        "Sending mail or connecting to a tax office / ELSTER -- humans send",
        "Changes to the dev-team or research-team kits beyond mirrored files",
    ],
}

env = dict(os.environ, PYTHONPATH="team-kits")
result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps(BODY),
                        capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
