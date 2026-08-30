# TSK-0093 close-out protocol (lead, 2026-08-30)

Round: BUG-0073 — approval cards reached the user as a German-English weave because nothing told
the drafting roles which language VALUES carry. Verifier: FAIL(F1 loaded surface omits the cut,
F2 self-contradicting card) → PASS.

## What ships

- The value-language rule on BOTH lead surfaces of all three kits, byte-identical per surface:
  values the user must UNDERSTAND (reasons, spelled-out naming rules, retention) are German;
  values something else MATCHES (ids, paths, templates, document classes, file names, remotes,
  branches) keep that thing's spelling — translating changes WHAT is approved. The honest limit
  in both forms: nothing enforces it; what the kernel does is narrower (folds, cuts where long,
  never translates).
- The loaded surface now also warns that GERMAN RUNS LONGER (+14% measured) and a value that
  only just fitted can lose its end to the cut — "say it shorter rather than let the cut
  choose". The implementer had caught his own "UNCHANGED" overclaim; the verifier caught that
  the cut-warning lived only on the surface that does not load.
- The document_proposal card no longer contradicts itself: the withholding clause is narrowed to
  the LIST case, and the true half is stated (a filled field, a new key and a new comment stand
  verbatim above) — new red-first kernel test reading the BUILT card in both directions.
- Test infrastructure: anchors derived from the running parser (backticked: 0 foreign hits vs 14
  bare), the TSK-0089-repaired clause reader reused not forked, _NEGATION_RX extended to German
  with a floor test (an honest German limit no longer reads as an overclaim).

## Measured end to end

The screenshot's card shape now renders one language throughout on a scaffolded project; umlauts
and ß intact through Git-Bash AND real PowerShell AND on disk (UTF-8 verified). The English call
still renders rc 0 — the rule cannot be enforced, and says so.

## Hole list

H77 (lead's hand — the verifier asked; answered): no gate enforces value language; the prose
test reads anchors and honesty, not direction and not vocabulary-free overclaims (both languages
measured, incl. the affirmative-idiom probe); document_types stands bare in the German sentence;
the records-clerk — the ONLY non-lead role typing a free --reason across all three kits — does
not carry the rule (small own round); a changed card wording invalidates pending unanswered
approval questions fail-closed.

## Delivery

Kits ×3 2026.08.30-10; ratchets re-recorded twice with journal lines; ruff, validate clean;
affected suites through the rounds 219 + 271 + 2198/1/1 (the one red = the known noise-guard
test under load, isolated re-run green — same as TSK-0086's case) + 94/1 verifier-side. Full
suite fresh by the lead before commit. The one environment-shaped red is named, not explained
away.
