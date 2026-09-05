"""Generation 5 cut (DEC-0067 bundle at the goal; user decision 2026-09-05): TWO product goals,
captured through the kernel in DRAFT. G5-2 (backlog system FR-0024/0019/0022) and G5-4 (provider &
environment FR-0023/0025/0020) are DEFERRED by the user -- "need more planning" -- and are NOT here.
Wishes are merged into the goals at triage by the lead after this runs (FR -> MERGED with
resulting_item; BUG.related_pr -> the PR). Not idempotent -- run once; read the ids it prints."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "capture", "PR"]

GOALS = [
    {
        "title": "G5-1 Bestandsbereinigung: every open BUG and wish of this repo measured against the running code and closed through the kernel or kept with its chain (FR-0058), plus a derivable notion of 'done' so the stock cannot lie upward again",
        "class": "normal",
        "user_story": "As the user who steers this project by its backlog, I want the 89 open bugs and 21 open wishes to be what is REALLY open -- each one measured against the code that ships today, closed through the kernel with the evidence that closes it, or kept with a measured chain -- so that the next generation is planned on a true stock and not on a list that grew for two months without anyone closing what was built.",
        "problem": "FR-0058 states it: delivered wishes and repaired bugs stay open. Measured 2026-09-05: 89 BUG items active, 5 VERIFIED; 21 FR items active; most bugs date from the August pilots (P4-x lines, BUG-0001..0082) and several are known to be built since (kernel `update` exists while BUG-0001 says the surface has none; BUG-0062 names the office timeouts that G4-1 reworked; BUG-0025/0033/0069/0088/0090/0091 are fixed in generation 4 but not VERIFIED because no evidence line ran the confirming edge). Nothing derives 'done' from the code -- a bug is closed only when a hand transitions it.",
        "goal": "Every active BUG and FR carries a measured verdict after this round: VERIFIED/archived through the kernel with the evidence that measured it (a test named, red-first where a fix was made), or kept OPEN/TRIAGED with the chain that still reproduces today and the item it belongs to; the small old kernel contracts on the way are built (BUG-0023 empty expected_outputs refused; BUG-0022 the CR type reached or removed with reasons); and the kernel gains a derivable 'done' reading -- a validator line that names an item whose confirming test or evidence exists while the item stands open.",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "FR-0058 (survey): Given the 89 active BUGs, When each is measured against the running code (its observed line re-run or its test executed), Then each carries one of three verdicts in the state -- VERIFIED and archived through the kernel with an Evidence item naming the test/measurement; still OPEN with the re-measured chain and date; or CANCELLED/superseded with the item that absorbed it -- and the round's protocol lists all 89 with verdict and measured line; no verdict without a measurement"},
            {"id": "AC-2", "text": "FR-0058 (wishes): Given the 21 active FRs, When each is triaged against what ships, Then delivered ones are MERGED with resulting_item, absorbed ones point at their goal, the deferred block (FR-0024, FR-0019, FR-0022, FR-0023, FR-0025, FR-0020) stays TRIAGED with the user's 'needs planning' note, and no FR remains whose source section describes something already built"},
            {"id": "AC-3", "text": "FR-0058 (the derivable 'done'): Given an item that stands OPEN while its confirming evidence or named regression test exists and passes, When validate runs, Then it names the item as 'stock lies upward' with the evidence/test it found -- a property derived from the items and the evidence store, not a list; red-first"},
            {"id": "AC-4", "text": "BUG-0023: create-task and capture TSK refuse an empty expected_outputs list naming the field (both entrances, one rule); existing items with an empty list are named by the validator; red-first"},
            {"id": "AC-5", "text": "BUG-0022: the CR type is either reached in a measured run (a change to something built produces a CR item through its automaton, and the PM texts say WHEN a CR applies instead of a PR replacement, with a test on the text-to-behaviour path) or removed with the reasons recorded -- no dead contract; the PR-replacement path stays for real re-orientations and records the replacement"},
            {"id": "AC-6", "text": "Generation-4 leftovers closed through the kernel: BUG-0025, BUG-0033, BUG-0069, BUG-0088, BUG-0090, BUG-0091 VERIFIED against the merged tree with their evidence lines; BUG-0083..0086 and BUG-0089 archived; the seven G4 stream items archived"},
        ],
        "invariants": [
            "A verdict without a measurement is not a verdict: every closed item names the test or the re-run line that closed it",
            "The kernel is the only writer of state; a bug is closed by a transition with evidence, never by editing a file",
            "Superseded means named: an item absorbed by another names it in resulting_item or supersedes",
        ],
        "out_of_scope": [
            "Building fixes for old bugs that still reproduce and are larger than a line -- they get their re-measured chain and stay open for a later goal",
            "The deferred block (backlog system, provider & environment) -- its own planning round",
        ],
        "priority": "high",
    },
    {
        "title": "G5-3 Office package: correspondence capability (FR-0033), a norm-conformant invoice writer (FR-0073), a year-versioned chart of accounts with EUeR mapping (FR-0081), the eight takeovers from a real operation (FR-0002), and the four open office bugs (BUG-0070/0071/0072/0079)",
        "class": "large",
        "user_story": "As the owner of a small business run through the office kit, I want the kit to write my outgoing letters and offers, produce e-invoices that validate before they leave the house, book against a real chart of accounts mapped to the EUeR lines, and no longer send me into a text editor for a category or a filing rule -- so that the office project handles the whole loop from document to booking to correspondence without a developer.",
        "problem": "The office kit reads and files documents and keeps a ledger, but it cannot WRITE outward: no correspondence role or workflow (FR-0033), no invoice writer (FR-0073 -- XRechnung/ZUGFeRD, EN 16931), no chart of accounts (FR-0081 -- SKR03/SKR04 with account-to-EUeR-line mapping, year-versioned, legal space named), and the eight measured takeovers from the user's real operation (FR-0002) are still prose. Live use measured four dead ends or wrong figures: add-filing-rule cannot create the rules list (BUG-0070), categories have no kernel writer (BUG-0071), einvoice_extract.py returned a non-reconciling net from a real invoice (BUG-0072), documents.py prints a remedy it refuses (BUG-0079).",
        "goal": "The office kit gains the outward half: a correspondence capability (role or teachable workflow, decided DEC-first with the user), an invoice writer whose output is validated against the norm before it is filed, a chart-of-accounts template with the EUeR mapping as a year-versioned kit document, the eight takeovers absorbed where they belong; the four bugs closed red-first; every new document class has a kernel writer and every printed remedy is a line the kernel accepts.",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "FR-0033: a DEC decides role vs teachable workflow with the user; then a scaffolded office pilot produces an offer, a reminder (Mahnung) and a customer letter from ledger + master data through the sanctioned document route, each reviewed before it leaves (gate or duty named), measured end to end; the texts pass the humanizer/plain-language bar the kit already ships"},
            {"id": "AC-2", "text": "FR-0073: the invoice writer produces an e-invoice (XRechnung or ZUGFeRD profile chosen DEC-first) from ledger and master data, validates it against EN 16931 rules before filing (a validator that FAILS on a planted violation), reconciles net x (1+vat) = gross, and never leaves the house unvalidated; measured on a pilot with a fixture set; red-first"},
            {"id": "AC-3", "text": "FR-0081: SKR03/SKR04 as year-versioned kit documents with the account-to-EUeR-line mapping and the legal space named; the bookkeeper's booking names an account and the EUeR rollup reads the mapping; a kernel writer exists for the document (no editor line); measured on a pilot"},
            {"id": "AC-4", "text": "FR-0002: each of the eight takeovers is either built in this goal with its own acceptance line, absorbed by another item (named), or rejected with the reason -- none stays prose without a verdict"},
            {"id": "AC-5", "text": "BUG-0070 + BUG-0071: add-filing-rule creates the rules list when the plan carries none; categories (and, decided in the round, every kit-document list) get a sanctioned approval-gated kernel writer -- special case vs general mechanism decided with reasons (P4-12 lineage); red-first on an old-stock copy outside the repo"},
            {"id": "AC-6", "text": "BUG-0072 + BUG-0079: einvoice_extract.py returns the reconciling document total from CII structures and fails loudly on a non-reconciling triple (both directions tested); every remedy line the kernel prints is executed by a test against the CLI and accepted; red-first"},
        ],
        "invariants": [
            "Nothing leaves the house unvalidated: an outgoing document is checked by code before it is filed or sent",
            "Every kit document has a kernel writer -- no sanctioned path ends in a text editor for a non-developer",
            "Money figures reconcile or refuse: a triple that does not add up is a loud failure naming all three figures",
        ],
        "out_of_scope": [
            "Sending mail or connecting to a tax office / ELSTER -- the writer produces files, humans send them",
            "Changes to the dev-team or research-team kits beyond mirrored files",
        ],
        "priority": "high",
    },
]


def main():
    env = dict(os.environ, PYTHONPATH="team-kits")
    for goal in GOALS:
        result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps(goal),
                                capture_output=True, text=True, encoding="utf-8")
        print(result.stdout.strip()[-300:])
        if result.returncode != 0:
            print(result.stderr.strip()[-1500:])
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
