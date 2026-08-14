# TSK-0057 — kit_state: measured states, exits and next actions

Round: BUG-0036 fix (PR-0003). Everything below was produced by RUNNING the shipped code, not by
reading the spec. Where code and prose disagree, the disagreement is written down rather than
smoothed over.

## How it was measured

* `team-kits/dev-team/hooks/kit_trust_state.py` — `transition()` called in a subprocess with
  synthetic records, once per kit copy (`team-kits/*-team/hooks/kit_trust_state.py`, all three
  byte-identical at the time of writing). The probe is `tools/test_report.py::_shipped_transitions`,
  so the enumeration below is re-measured by the suite and not only by this document.
* `team-kits/write_kit_state.py:236` — the scaffold's recorder; it sets `state: restart_required`
  unconditionally, whatever the record said before.
* `team-kits/kernel/report.py::_hook_bundle_trust` — the doctor's `hook_trust` verdict and reason.
* Spec: `docs/HARNESS_V2_SPEC.md` section II.8 (the chain and the failure state) and the E2E
  acceptance block ("E2E pro Kit") for "exactly one next step at any time".

## The table

| record `state` | written by | what the RUNNING machine does | one honest next action |
|---|---|---|---|
| `restart_required` | `write_kit_state.py:236` (scaffold) | hash matches → `transition()` returns `active` | one new session — **if** a SessionStart run of the trust hook is registered |
| `active` | `kit_trust_state.py` (`transition` → `active`) | hash matches → returns `None` (nothing to do) | none; this is the verified case |
| `hooks_trust_required` | `kit_trust_state.py:105` (ANY state + hash mismatch) | mismatch → `None` (already recorded); **hash equal again → `active`** | `/hooks` review (spec II.8) |
| `update_available`, `approved`, `applying`, `failed_rolled_back` | no shipped writer — spec II.8 only | treated exactly like any non-`active` name: hash decides | as for `restart_required` / `hooks_trust_required` |
| unknown name, or no `state` field | — | same: the hash decides | as above, plus "this record is suspect" |
| any state with no usable `hook_bundle_hash` | — | `transition()` returns `(None, None)`; nothing is ever written | re-run the scaffold; restarting provably changes nothing |
| any state, `settings.json` without the SessionStart registration | — | nothing runs, so nothing flips | re-run the scaffold (the registration lives outside the hashed bundle) |

The property behind the table: **the running machine does not branch on the state name at all —
it branches on "is the installed bundle the recorded one".** The kernel's reason is built from that
same comparison, with exactly one name-keyed exception (`hooks_trust_required`, whose name records a
change that was seen and never reviewed — something no hash comparison can re-derive).

## Contradiction found in the kits' prose (→ BUG-0037)

`team-kits/*-team/hooks/kit_trust_state.py:23-27` states that nothing leads OUT of
`hooks_trust_required` and that only the scaffold can clear it. Measured against the same file's
own `transition()`: a record in `hooks_trust_required` whose bundle hash matches the recorded value
again returns `active` — restoring the changed file leaves the state at the next session, with no
scaffold, no review and no user. The kits' hook tree was out of scope for this round; the kernel's
reason is written to the measured behaviour, not to that paragraph.

## Residues this round did NOT close

* **F3 — the CLASS "a shipped text hands the entry window a `/hooks` step" is not closed.** Two
  carriers remain, measured and deliberately untouched here because their correct semantics are
  unmeasured:
  * `team-kits/kernel/report.py:2245-2248` — the `environment_notes` line for a project that also
    has a Codex surface ends in "read the Codex bundle-trust line in /hooks separately".
  * `team-kits/gen_provider_artifacts.py:1313` — the scaffold's closing line on the Codex path,
    "trust the project, then run /hooks to trust changed hooks".
  Both are Codex-surface statements. Whether Codex's `/hooks` step exists in the form these lines
  describe was NOT measured in this round; changing them on a guess would trade a possibly-true
  claim for a certainly-unmeasured one.
* **`report.py:2118`** carries "review the difference in /hooks" as the remedy for a bundle that
  changed after trust was recorded. That is the case spec II.8 routes through `/hooks`, so it is
  named here as a carrier of the token, not as a defect.
* **The recorder's provenance is unchanged.** `hook_trust` remains a doctor capability, not a
  proof: an agent that can run scripts can still rewrite `kit_state.json` (the class is stated at
  length in the kits' `hooks/_kernel.py::bundle_trust`). Nothing in this round moves that line.
