# TSK-0087 close-out protocol (lead, 2026-08-29)

Round: FR-0035 — the user's four-eyes filing requirement, in his own words: "ein Hook der das
Verschieben sperrt bis der Datei kein neuer Name zugewiesen wurde und ein zweiter unabhängiger
Agent nicht auf dasselbe Ergebnis kommt." ENFORCED, not advised. Verifier rounds:
FAIL(4 blockers) → PASS bound to three commit contents, all delivered.

## What was built

- NEW gate_second_reading (office kit, chained AFTER gate_filing): a document entering the
  archive is refused unless TWO classification readings agree on the FULL target incl. filename
  AND their attestations name two different runs. Disagreement or a missing reading leaves the
  document in inbox/ and shows BOTH readings.
- Readings are bound to the BYTES of the document (source digests stamped at attestation,
  recomputed on the move) — a document swapped after being read invalidates its readings, with
  the count named ("1 of 2 attested readings no longer match its bytes").
- The POLICY is a plan property (FR-0028): a rule releases its class to ONE reading — never zero
  (the user's question was ever "two runs or one", never "two or none"); overlapping rules: the
  higher demand wins, now pinned by a fixture with overlapping templates (max→min mutation red).
- The user's cost number, measured against the installed end state: fixed context of a second
  reader 16,169–20,276 B ≈ 4,040–5,070 tokens (with constitution ~13,000–14,000); ONE extra run
  per sweep, not per document (a reading record carries a list); mechanism overhead ~+73 ms per
  checked call.

## The verifier's four blockers, closed and re-measured

1. Archive-internal laundering: one legit filing used to open the whole archive as a free
   namespace (move to another rule, forge a name, move back — all rc 0). Now an entry is
   everything except same-rule-same-filename; his G2/G3 chains rc 2.
2. Readings covered a target PATH, not a document: a foreign document, a redirect and a direct
   Write landed under the read name. Now the source is compared and a landing with no document
   behind it is always refused; his D2/D3/D4 rc 2.
3. ARCHIVE//Archive/ case-folding passed all six hooks and really landed in archive/ (NTFS
   folds, under() compared case-sensitively). normcase both sides; his F1/F2 rc 2. This also
   CLOSES the exit-direction half of the pre-existing hole-list entry.
4. The cost number had been measured against the PRE-round state (13–41% low). Re-measured
   against a freshly scaffolded end-state project; old table marked superseded; verifier
   confirmed every digit.

Plus his residues taken in-round: NotebookEdit on both filing gates (was rc 0 past everything);
test_role_contracts floor restored (>=3 per schema AND >=20 aggregate); the false order claim
removed and the stand-down property pinned by running the gate ALONE. And the implementer's own
find B2e: an ambiguous relative word requires readings for EVERY existing candidate (over-refusal,
named file in the refusal).

## PASS conditions (verifier), all in this commit

1. Hole list: H72 (four measured boundaries of the four-eyes wall: the tidy-exemption compares
   template+filename not location — K7/K8, closing it is a user decision with a cost; inbox
   overwrite itself stays free with the consequence closed by byte-binding; three named
   over-refusals; the procedure boundary). Pre-existing entry updated: the ARCHIVE/ half is
   closed, the rm-variable half stays.
2. The "a folder being tidied" docstring now says what the code compares (template+filename, not
   folder), with K7/K8 as the measured chains, honestly marked as a gap this code does not close.
3. The no-digest refusal separates "swapped" from "never bound" (unbound vs stale), red-first
   both directions; the size limit read from _readings.MAX_DOCUMENT_BYTES, no second literal.

## Delivery

office-team 2026.08.29-5 (content f4757d47…). ruff clean, validate clean. Affected suites across
the rounds: 3025 passed/13 skipped, then 856 passed/13 skipped after the surgical items.
23 mutations over the whole task, all red, re-run after the last change. 20+ red-without-fix
tests seen in clones. Full delivery suite: run by the lead before commit (result in the commit).
Measurement protocol: docs/reviews/2026-08-28-tsk0087-measurements.md (§8d added).

Full delivery run (lead): 3879 passed, 14 skipped, 1 failed in 32:39 — the failure was the
constitution-section tripwire doing its job on THIS round's own legitimate rule-text changes
(AGENTS.md §2/§5/§6, ENFORCEMENT.md §1). Re-pinned deliberately via
pin_constitution_sections.py --write with the round named in the note (4 changes journaled in
phase0-disposition.md); test_shortening_net re-run: 35 passed. Same shape as TSK-0086's journal
count — the tripwire forces the look, the look happened, the reason is recorded.

## What the user gets

His four-eyes principle is now a MECHANISM: no document is filed until a second, independent
reading agrees on the same target and name, both bound to the document's actual bytes. His
policy question (two readings for everything, or only for sensitive classes?) is now a per-rule
plan setting — safe default TWO, a release means ONE reading, never zero — so his answer is a
plan edit, not a rebuild. The corrected cost number for that decision: ~4,000–5,000 tokens of
fixed context for the second reader, incurred once per sweep, not per document.
