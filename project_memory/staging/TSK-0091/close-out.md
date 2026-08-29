# TSK-0091 close-out protocol (lead, 2026-08-29)

Round: BUG-0072 — the kit's e-invoice extractor returned a silent wrong net from a real invoice.
Money-reading code; the standard was raised accordingly. Verifier rounds: FAIL(B1 norm error,
B2 currency fallback + F3–F7) → PASS.

## The finding was bigger than the bug report

- ALL FOUR structured e-invoices in the user's archive were misread (0.51/18.87/5.10/14.28 vs
  true 20.00/47.94/114.24/214.20), not just the reported one.
- The same root (document-order name-set scan) also corrupted the SELLER (first product name
  instead of "idealo internet GmbH" — the ledger counterparty source) and returned pre-discount
  net on document-allowance invoices.
- NOTHING was booked wrong: ledger_add.py's own arithmetic check (net×(1+rate) vs gross,
  tolerance 0.011) would have refused every wrong net — the layered defense worked.

## What ships

- Structural anchoring: every money field read from the element its syntax puts it in, with
  name-order preference and currency preference; a currency conflict now REFUSES loudly instead
  of falling back to document order (verifier's CHF attack).
- The reconciliation guard on the document's OWN identity (EN 16931 BR-CO-15: BT-112 = BT-109 +
  BT-110; the rounding amount enters only on the BR-CO-16 fallback) — the verifier read the
  NORM against the code and caught both an over-refusal (valid rounding invoice refused) and a
  blessing (invalid one passed) before either could ship; the test that had pinned the wrong
  semantics was replaced by a three-leg one.
- NaN/Infinity anywhere in the money fields → contractual refusal, never a traceback.
- Delivery as kit-owned (judgement reasoned in the manifest header: a money parser must not
  fork silently; measured end to end with the user's exact pre-fix hash 21e409cbc3ea).
- BYCATCH FIXED: two tests red on pristine HEAD — tools/test_hooks.py leaked
  HARNESS_KERNEL_PATH process-wide and the entry point treats it as authoritative. Closed via
  the house pattern (env-restoring conftest fixture, restore-not-assert with the reason priced);
  the implementer RETRACTED his own earlier misattribution, and the verifier retracted having
  waved it through. Both retractions on the record.
- The mechanical sweep recipe for the user's project (their AC-B2) lives durably in
  docs/reviews/2026-08-29-tsk0091-measurements.md §3, incl. the case the ledger judge does not
  see.

## Hole list

H75 (lead's hand — the verifier asked; answered): seven measured boundaries incl. the verifier's
three edge forms and the healed-not-flagged env-leak trade-off, with the fixture/source claim
corrected to what probe 2 measured.

## Delivery

office 2026.08.29-12, dev/research -6. ruff, validate clean. Touched suites 939/14 (implementer)
and 886/16 (verifier, one process, the combination that was red on HEAD) — both zero failed.
Live invoice unchanged correct; A/B archive 4/4; delivery replayed twice. Full suite fresh by
the lead before commit. What the user gets: every e-invoice his projects read from now on
carries either the document's true totals or a loud, three-figure refusal — and the fix reaches
existing projects through the installer, not a rotting pending list.
