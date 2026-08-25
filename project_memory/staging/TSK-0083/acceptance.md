# TSK-0083 — acceptance protocol (harness-implementer)

Item: TSK-0083 (bugfix, derives_from BUG-0063). Measured 2026-08-23.
All command verdicts below come from **real hook processes** (`gate_ledger_valid.py`, JSON on
stdin) against a project scaffolded **outside the repo** at
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0083\proj\`. "before" = the HEAD copy of the gate,
"after" = the working tree.

## 1. The defect, reproduced before the change

| line | before | after |
|---|---|---|
| `python scripts/harness.py evidence --summary "fixed the -m flag handling in scripts/ledger_add.py" && git commit -m x` | rc 2 | rc 0 |
| same with `-c` | rc 2 | rc 0 |
| same with `-e` | rc 2 | rc 0 |
| same line without the flag word (control) | rc 0 | rc 0 |

Module view of the same line (`inspect_rx.py`): `_ENTRY_POINT_RUN_RX.search(...)` → `None`,
`_writes_protected(...)` → `True`; after → match at span (0, 25), `False`.

## 2. What the trailing lookahead actually caught (asked BEFORE dropping it)

`what_the_lookahead_catches.py` compiles each pattern with and without the tail
`(?![^\n]*\s-(?:c|e|m)\b)` and asks both.

**In front of the script — nothing.** `python -c "…"`, `python -Bc "…"` and `python -m scripts.harness`
match neither pattern, with or without the tail: `_INTERPRETER_OPTIONS` alone refuses them, because
an option word carrying `c`/`e`/`m` ends the option run before the script argument.

**Behind the script — one real direction, and it was the VALIDATOR's, not the entry point's.**
`_LEDGER_ADD_RUN_RX` was asked per **segment** in `_writes_ledger`, and `|` is deliberately not a
separator in `_SEGMENT_SPLIT_RX`, so a segment holds a whole pipeline. The tail was the only thing
keeping the validator's exemption from swallowing a neighbouring stage that happened to spell `-c`:

- `python scripts/ledger_add.py --validate ledger/2026.csv | python -c "open('ledger/2026.csv','w')" && git commit -m x` → rc 2 before, rc 2 after

That protection was an accident and was already incomplete — the same neighbour without a
`c`/`e`/`m` letter rode along free:

- `python scripts/ledger_add.py --validate ledger/2026.csv | sed -i s/119.00/150.00/ ledger/2026.csv && git commit -m x` → **rc 0 before**, rc 2 after

A write-and-commit in one call, allowed. It is the same stage-versus-segment defect
`_stages_beside_the_entry_point` was written for one round earlier, still standing in the other
exemption.

## 3. What was built

`team-kits/office-team/hooks/gate_ledger_valid.py`

1. `_canonical_run(script)` builds both patterns from one construction; the trailing lookahead is
   gone from both. The guard is carried by the interpreter-option position alone
   (`_INTERPRETER_OPTIONS`) — the only place an inline payload can stand.
2. `_stages_beside_the_entry_point` → `_stages_beside_the_vouched_runs`: it drops the canonical
   validator's stage as well, and `_writes_ledger` no longer exempts a whole segment on
   `_LEDGER_ADD_RUN_RX`. `_writes_ledger` and `_writes_protected` now use the same definition.

`tools/test_hooks_v2.py` — the tests named in §4 and §5.

## 4. Tests that go RED without the fix (red SEEN, twice)

Clone at `…\_round-scratch\TSK-0083\clone\` (working tree copied, `.git` excluded), gate put back
to its HEAD content with `restore_defect.py`:

```
6 failed, 20 passed, 1273 deselected in 7.95s
FAILED test_prose_about_the_ledger_in_a_body_or_an_argument_is_not_a_write[the entry point whose summary talks about a flag-…]
FAILED test_prose_about_the_ledger_in_a_body_or_an_argument_is_not_a_write[the validator's own run, whose note names the folder it lives in-…]
FAILED test_the_same_constructs_still_refuse_a_real_write[a write in the stage after the validator-…]
FAILED test_an_option_word_after_the_script_is_an_argument_not_a_payload[c]
FAILED test_an_option_word_after_the_script_is_an_argument_not_a_payload[e]
FAILED test_an_option_word_after_the_script_is_an_argument_not_a_payload[m]
```

**Second red run — the defect this correction could have introduced.** `naive_fix.py` applies the
obvious correction (drop the tail, change nothing else) to the clone's HEAD gate:

```
2 failed, 24 passed, 1273 deselected in 33.68s
FAILED test_prose_about_the_ledger_in_a_body_or_an_argument_is_not_a_write[the validator's own run, whose note names the folder it lives in-…]
FAILED test_the_same_constructs_still_refuse_a_real_write[a write in the stage after the validator-…]
```

So the per-stage half of the fix is measured, not asserted.

The letters `c`/`e`/`m` are **not typed** in the tests: `_inline_payload_option_letters()` derives
them from the pattern that runs (an option letter that keeps `_ENTRY_POINT_RUN_RX` from matching)
and asserts the derived set is non-empty, so the two parametrised tests cannot become vacuous.

## 5. The behaviour the fix WIDENS, measured and pinned

Vouching for the validator's stage means the words in its own arguments stop being read as
commands — the P4-12 property the entry point already had. `flip_probe.py`, HEAD vs now:

| line | before | after |
|---|---|---|
| `python scripts/ledger_add.py add --note "cp backup.py scripts/" && git commit -m x` | rc 2 | rc 0 |
| `python scripts/ledger_add.py -o scripts/ && git commit -m x` | rc 2 | rc 0 |
| `python scripts/ledger_add.py add --note "see .claude/ledger_state.json" && git commit -m x` | rc 2 | rc 0 |
| `python scripts/ledger_add.py --validate ledger/2026.csv ; cp backup.py scripts/ && git commit -m x` | rc 2 | rc 2 |
| `python scripts/ledger_add.py --validate ledger/2026.csv \| xargs -I{} cp {} scripts/ && git commit -m x` | rc 2 | rc 2 |
| `python scripts/ledger_add.py --validate ledger/2026.csv \| tee .claude/ledger_state.json && git commit -m x` | rc 2 | rc 2 |

The first line is pinned as an ALLOW in `_PROSE_ABOUT_THE_LEDGER`, the two `cp` controls as
REFUSALS in `_WORK_ON_THE_LEDGER`, so the widening cannot grow further unnoticed. What bounds it:
the exemption is anchored to `scripts/ledger_add.py`, a copy under any other path is a decoy, and
a write into the canonical file from any other stage is still refused — all three already tested.

## 6. Counter-direction, still refused (rc 2 before AND after)

- `python -c "open('scripts/ledger_add.py','w').write('')" && git commit -m x`, and `-e`, `-m`
- `python -m scripts.harness submit-result --summary 'booked via ledger_add.py' && git commit -m x`
- `python -m scripts.harness doctor > scripts/ledger_add.py && git commit -m x`
- `python scripts/harness.py doctor > ledger/2026.csv && git commit -m x`
- `python scripts/harness.py doctor > .claude/ledger_state.json && git commit -m x`
- `python -B tools/ledger_add.py && git commit -m x`
- `python scripts/harness.py doctor | tee scripts/ledger_add.py`

## 6b. Rework after the verifier's FAIL (round 2 — F1, F2, F3; F4 handed back)

### F1 — the counter-test measured a different mechanism than the one it named

The counter-test ran `python -<letter> "open(…)"` with **no script argument**. That line is refused
by `_INLINE_CODE_RX` alone, so it never exercised `_INTERPRETER_OPTIONS` — the pattern its comment
credited. Reproduced the verifier's mutation in the clone (`mutate.py letters`, `[cem]` → `[cm]`):

- `python -e scripts/harness.py evidence --summary 'booked via scripts/ledger_add.py' && git commit -m x`
  → **rc 0** under the mutation.

Built, both parts of the prescribed fix:

1. The counter-test now runs the payload option **in the position the claim is about**, for both
   canonical invocations: `python -<letter> scripts/harness.py evidence --summary "…"` and
   `python -<letter> scripts/ledger_add.py --validate ledger/2026.csv`, each `&& git commit -m x`,
   each expected rc 2.
2. The letter set is cross-checked against the module's **second, independent** spelling of it
   (`_INLINE_CODE_RX`), and the parametrisation runs over the **union** of both readers — so a
   letter dropped from one reader keeps its own test case. `test_the_two_readers_of_an_inline_payload_option_agree`
   is the tripwire on the disagreement itself.

Red seen under the `letters` mutation: **3 failed, 39 passed** —
`test_the_two_readers_of_an_inline_payload_option_agree`,
`test_a_real_interpreter_payload_before_the_script_is_still_refused[e-the entry point-…]` and
`[e-the validator-…]`.

**Two findings of my own inside this rework, both measured:**

- The two readers do **not** agree letter-for-letter as written: `_INLINE_CODE_RX` is
  `re.IGNORECASE`, so it also answers yes to `-C`/`-E`/`-M`, while `_INTERPRETER_OPTIONS` is
  case-sensitive on purpose (`-E` is an option, `-e` a payload flag). The first cut of the
  cross-check therefore failed on 6 cases. Resolved by comparing the **case-folded** sets, with the
  reason stated in the test: the inline reader's over-match only keeps a line unstripped, which is
  the conservative direction.
- The table comment above `_PROSE_ABOUT_THE_LEDGER` claimed "`-E` … is here as its control" while
  **no `-E` case existed** — a comment claiming coverage the code did not build. Added the case
  (`python -E scripts/harness.py … ` → rc 0), which is now also what pins the case-sensitivity the
  cross-check deliberately does not compare.

### F2 — the anchor did not end at the canonical name

`_canonical_run` ended on `\b`, and a word boundary is satisfied by the `.` of `.bak`. Measured
before (identical at HEAD — old pattern weakness, new claim):

| line | before | after |
|---|---|---|
| `python scripts/ledger_add.py.bak ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `python scripts/harness.py.bak evidence --summary 'booked via scripts/ledger_add.py' && git commit -m x` | rc 0 | rc 2 |
| `python scripts/harness.py-evil evidence --summary 'booked via scripts/ledger_add.py' && git commit -m x` | rc 0 | rc 2 |
| `python scripts/ledger_add.pyc …` / `…py2 …` (already refused) | rc 2 | rc 2 |

Took the **pattern** variant: `\b` → `(?![\w.-])`. Over-refusal checked against ten legitimate
spellings of the two canonical invocations (plain, `./`-prefixed, behind `-B`, under `python3`, as
the last word, before `;`, as the first pipeline stage, with a comma in its own prose) — **all rc 0
before and after**. Red re-measured in round 4 (the name this section carried before did not exist
in the repo — verifier finding V8): defect restored in a clone outside the repo
(`…\rework4\redproof.py anchor10`, the anchor back to `(?![\w.-])`) → **36 failed**, every one of
them `test_a_name_that_continues_past_the_canonical_one_is_a_different_file[…]`.

### F3 — only the first redirect target of a segment was read

`_REDIRECT_INTO_RX.search(...)` at both readers. Measured before:

| line | before | after |
|---|---|---|
| `cat ledger/2026.csv > /tmp/a > ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `cat scripts/ledger_add.py > /tmp/a > scripts/ledger_add.py` | rc 0 | rc 2 |
| `cat README.md > /tmp/a > .claude/ledger_state.json` | rc 0 | rc 2 |
| `cat ledger/2026.csv > /tmp/a > /tmp/b > ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `cat ledger/2026.csv > ledger/2026.csv > /tmp/a && git commit -m x` (harmful first) | rc 2 | rc 2 |
| `cat ledger/2026.csv > /tmp/a > /tmp/b && git commit -m x` (all point away) | rc 0 | rc 0 |
| `cat ledger/2026.csv > /tmp/backup.csv && git commit -m x` | rc 0 | rc 0 |

Built `_redirect_targets(segment)` (`finditer`), used at both readers. Red seen under
`mutate.py redirect` (targets truncated to the first): **4 failed**,
`test_every_redirect_target_of_a_segment_is_read[…]` ×4.

### F4 — measured and handed BACK, not taken

Per-stage decoy check (`_DECOY_VALIDATOR_RX` over `_stages_beside_the_vouched_runs`) applied in the
clone and measured. It is **not** the clean one-liner it looks like:

| line | today | with F4 |
|---|---|---|
| `python scripts/ledger_add.py --validate ledger/2026.csv --note "the old copy was tools/ledger_add.py" && git commit -m x` | rc 2 | rc 0 |
| `python scripts/harness.py evidence --summary "ledger/2026.csv was rebuilt with tools/ledger_add.py" && git commit -m x` | rc 2 | rc 0 |
| `cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x` (the gate's own advertised remedy) | rc 2 | **rc 2** |
| `python tools/ledger_add.py ledger/2026.csv && git commit -m x` (control) | rc 2 | rc 2 |
| `python scripts/ledger_add.py --validate ledger/2026.csv \| python tools/ledger_add.py && git commit -m x` (control) | rc 2 | rc 2 |

It fixes two of three over-refusals, leaves the **user-visible** one standing (a bare
`ledger_add.py` after `cd scripts` is not a vouched run, so the stage is kept; that case needs the
`inside_scripts` exemption moved ahead of the decoy check, a different change), and it loosens the
one rule that stands between the gate and a validator nobody guards. Not worth a bolt-on at the end
of a rework — handed back with these numbers.

## 6c. Rework after the verifier's round-2 FAIL (F5–F9)

Measured through the verifier's own rig — the **full registered PreToolUse chain** of a scaffolded
office project (`verify/chain.py`, registration read from that project's `settings.json`, never
from memory), driven by `chainrun.py`, which first copies the repo's current hooks into the
project. Before/after over the verifier's case files: **13 mismatches → 1**, and that one is
explained below.

### F5 — quoting inside a word defeated the anchor and the decoy rule

The `(?![\w.-])` anchor was a character-class question; a shell removes quote marks character by
character and the gate did not. One view fixes both directions: `_quoting_resolved()` performs the
shell's QUOTE REMOVAL on the text `_canonical_run` and `_DECOY_VALIDATOR_RX` read, one line per
reading (`_compat.shell_readings` — the two shells disagree about the backslash, and a newline is
already a segment separator here, so a second reading can only add refusals). Redirection is
deliberately NOT resolved in that view: `_compat.git_argument_text` drops the word after a `>`, and
`_redirect_targets` must still read it — one view, one place, said in the docstring.

| line | before | after |
|---|---|---|
| `python scripts/ledger_add.py'.bak' ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `python scripts/ledger_add.py\.bak ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `python scripts/harness.py'.bak' ledger/2026.csv && git commit -m x` | rc 0 | rc 2 |
| `python tools/ledger_add".py" && git commit -m x` | rc 0 | rc 2 |
| `python tools/ledger_add'.py' && git commit -m x` | rc 0 | rc 2 |
| `python tools/ledger_add\.py && git commit -m x` | rc 0 | rc 2 |
| `python "scripts/ledger_add.py" --validate ledger/2026.csv && git commit -m x` | rc 2 | rc 0 |
| `python "scripts/harness.py" evidence --summary '…' && git commit -m x` | rc 2 | rc 0 |

The sibling test is now parametrised over **quoting spellings** and not over suffixes: `%s`,
`"%s"`, `'%s'`, `%s''`, `''%s`, each asked of BOTH canonical paths (derived from
`_VOUCHED_INVOCATIONS`) and in both directions — the sibling must refuse, the canonical must pass.
Red seen (`mutate.py quoting`, the normalisation taken back out, 2 call sites): **6 failed, 111
passed** — `test_quoting_inside_a_word_does_not_change_which_file_it_names[…]` ×6.

**One case of the verifier's file stays "red" and should not go green:** `python
scripts/harn'ess.py' … && git commit` is expected 2 there, and I measure rc 0. The real shell is
the arbiter and was asked: `bash -c 'printf "%s\n" scripts/harn'"'"'ess.py'"'"''` prints
`scripts/harness.py` — that spelling IS the canonical entry point, not a sibling, so vouching for
it is the P4-12 direction and matches the file's own `quoted canonical harness` row. The same
check on `scripts/ledger_add.py'.bak'` prints `scripts/ledger_add.py.bak`, a real sibling, and that
one refuses. I believe the expectation in that row encodes the pre-fix behaviour.

### F6 — a closing paren ended no word (BUG-0065)

Took neither of the two options as offered: making a closing paren a SEGMENT boundary was measured
against prose parens first, as instructed, and it cuts `--summary "1,19 (ok)"` into command
fragments. So the word-END is where the fix went — `_WORD_END`, written once and used by both
closers of `_PROTECTED_DIR_RX`.

| line | before | after |
|---|---|---|
| `echo "$(tar -xf evil.tar -C scripts/)" && git commit -m x` | rc 0 | rc 2 |
| `echo "$(cp evil.py scripts/)" && git commit -m x` | rc 0 | rc 2 |
| `echo "$(cp evil.py scripts/)"` (no commit) | rc 0 | rc 2 |
| ``echo "`tar -xf evil.tar -C scripts/`" && git commit -m x`` | rc 0 | rc 2 |
| `(cp evil.py scripts/) && git commit -m x` | rc 0 | rc 2 |
| `python scripts/ledger_add.py --validate … --note "$(cp evil.py scripts/)" && git commit -m x` | rc 0 | rc 2 |
| ``… --note "`cp evil.py scripts/`" …`` | rc 0 | rc 2 |
| `--summary "net 1,19 (ok) …"`, `-m 'total 1,19 (ok) …'`, `--note "1,19 (ok)"` | rc 0 | rc 0 |

**A finding inside my own fix, caught by measurement:** the first cut of `_WORD_END` omitted the
BACKTICK, and the two backtick spellings stayed exit 0 while the `$(…)` spellings refused. It is in
the set now, with its own mutation as proof. What deliberately stays OUT: expansion characters
(`$`, `{`, `*`) — the shell continues a word there, and ending it would read `scripts/$X` as the
bare directory.

Red seen: `mutate.py paren` (the pre-BUG-0065 set) → **5 failed**,
`test_a_closing_paren_ends_a_word_for_this_reader_too[…]` ×5; `mutate.py backtick` (only the
backtick missing) → **1 failed**, the backtick row. The gate comment that named the `tar` form
closed now names that test.

### F7 — `>|` and the word EVERY

Taken as the pattern fix (`>>?\|?`), because it cost one character class and makes the docstring
true. `>&` deliberately yields no target: `2>&1` duplicates a descriptor and writes no file.

**And a defect of my own on the way:** I first pinned `>|` end to end, and that test **could not
fail** — `mutate.py clobber` left it green, exactly as the verifier's note predicted (the `|`
splits the stage and the second stage's verb is not a reading one, so those lines refuse either
way). A case that passes with and without the fix is not a measurement, so it is gone. The property
is pinned where it CAN fail, at the running function:
`test_the_redirect_reader_names_every_target_and_only_targets` calls `_redirect_targets` and
compares the full list. Red seen: `mutate.py clobber` → **2 failed**, the `>|` rows.

### F8 — the widening F3 produced, named by mechanism

Not two accidental spellings: **redirect targets are read on the same view as everything else, and
that view keeps the content of quoted spans while the redirect check runs BEFORE the stage
exemption.** So any `>` inside an argument — including inside a quoted prose span, and including
inside the arguments of a vouched invocation — is read as a redirection, and the word after it is
read as its target. It refuses only when that word also matches a ledger path or a protected file,
which is why it shows up as: `--note "row > ledger/2026.csv"` rc 0 → **rc 2**, while
`--note "net > gross"` stays rc 0. Direction is over-refusal, so it is safe, and it is the price of
reading every target rather than the first; closing it would mean knowing which `>` the shell will
execute, which is the quoting question F5 answers for words and not for operators. Named here for
your decision on the holes list; not closed.

### F9

The sentence "measured exit 0 for all three" is gone with the suffix table it counted.

## 6d. Rework after the verifier's round-3 FAIL (F10–F16)

Measured on the verifier's own rig (`…\_round-scratch\TSK-0083\verify3\`): the full registered
PreToolUse chain of a scaffolded office project, plus the HEAD twin `proj_head` to separate "new"
from "pre-existing". Driver `chainrun3.py` copies the repo's current hooks into the twin first.

**Batteries, before → after this rework:** `cases_anchor` **10 → 0**, `cases_bound` **4 → 1**,
`cases_state` **4 → 2**, `cases_base` 0 → 0, `cases_fp` 0 → 0, and my own `cases_r3` 0 → 0,
`cases_r2b`/`cases_r2c` 1 → 1 (the row the verifier withdrew). The remaining four are all
**rc 0 at the HEAD twin as well** — B5, S5, S6 — i.e. pre-existing, not opened here.

### F10 — the anchor was an enumeration of continuation characters

Taken as prescribed: `_canonical_run`'s `(?![\w.-])` → `_WORD_END`, the set already in the file.

| line | HEAD | before this rework | after |
|---|---|---|---|
| `python "scripts/ledger_add.py"$'.bak' ledger/2026.csv && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `python "scripts/ledger_add.py"${X}bak …` | rc 2 | rc 0 | rc 2 |
| `python "scripts/ledger_add.py"+x …` | rc 2 | rc 0 | rc 2 |
| `python scripts/ledger_add.py+x …`, `…py~`, `…py,v`, `…py@`, `…py%1`, `…py=x` | rc 0 | rc 0 | rc 2 |
| `python scripts/ledger_add.py:evil …` (NTFS stream), `…py/../evil.py …` | rc 0 | rc 0 | rc 2 |
| `python "scripts/ledger_add.py" --validate … && git commit -m x` (control) | rc 2 | rc 0 | rc 0 |

The verifier's hole-list candidate 4 is therefore **measured closed by this one-liner**: S7 (ADS)
and S8 (`/../`) drop out of `cases_state`.

The test is no longer a list of suffixes. A sibling is *any name that continues past the canonical
one*, and the characters it can continue with are exactly those that do not end a shell word — so
they are probed off the running `_WORD_END`
(`test_a_name_that_continues_past_the_canonical_one_is_a_different_file`, 2 paths × 88 characters).

### F11 — a second reading REMOVED a refusal

`inside_scripts` was computed over the joined readings and then ended the decoy loop outright, so
one `cd scripts` anywhere switched the rule off for the whole command — and `_quoting_resolved`
produced that `cd scripts` from spellings the raw text never had.

I did **not** take the verifier's minimal fix as offered. Measured on his own `proj_fix11`: `if
_CD_SCRIPTS_RX.search(segment)` closes B1/B2/B3/B6 but leaves **B4** open
(`cd 'scripts' && python ../tools/ledger_add.py && git commit`, rc 2 at HEAD → rc 0), because the
loop then breaks at the `cd` segment and never reaches the decoy behind it. So the exemption is
narrowed by its *reason* instead: in `scripts/` the **bare** name is the canonical file, while
`tools/ledger_add.py` names a different file from every working directory. `_only_the_bare_validator`
is that rule, used at all three `inside_scripts` sites.

| line | HEAD | before | after |
|---|---|---|---|
| `python tools/ledger_add.py && cd "scripts" && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd 'scripts' && python ../tools/ledger_add.py && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cat x \| python tools/ledger_add.py && cd "scripts" && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `python tools/ledger_add.py && c\d scripts && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `sed -i s/119/150/ ledger/2026.csv && cd "scripts" && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x` | rc 2 | rc 2 | **rc 0** |

The last row is the gate's own advertised remedy, refused since before this task (the decoy check
stood in front of the exemption). It works now, and has its own test.

The monotonicity the docstring claims is measured rather than asserted
(`test_a_second_shell_reading_can_only_add_refusals`: no single reading may refuse where all of
them together do not), and the two-reading construction itself is pinned
(`test_the_resolved_view_keeps_every_reading_the_shells_disagree_about`) — the verifier's
`one_reading` mutation used to leave the whole file green.

### F12 — the comment claimed a derivation the code does not build

`_WORD_END` was described as `_compat._SYNTAX_CHARS`. It is not that set (`&|;#\n\r`) and nothing
computes it. The sentence now says hand-written, and the enumeration gets the tripwire CLAUDE.md
asks for: the set is stated a **second time, independently**, in the test.

**A defect of my own inside this fix, caught by the verifier's mutation:** the first cut derived
the tripwire's parameters from the pattern it was testing, so dropping `<`/`>` removed the very
cases that should have failed — the same self-referential blind spot as F1 one round earlier.
`wordend_lt` went from 0 red to 1 red after the correction.

### F13 — the comment's reason was refuted by the measurement

The line claimed `$`/`{`/`*` must stay out because `scripts/$X` would otherwise read as the bare
directory. With `X` unset it **is** the bare directory — filesystem witness, the copy lands in
`scripts/`. The comment now states the measurement and says why adding `$` would not fix it (the
word the shell builds is not in the text).

**Corrected in round 4 (verifier finding V6):** that comment also said the gap "is carried as an
open hole in `docs/POST_V2_WISHLIST.md`", and no such entry exists — a claim about a document this
task does not write. The sentence now says the gap is open and points at nothing; whether it gets a
holes-list entry is the lead's call, not this file's.

### F14 — dead test pointer

`gate_ledger_valid.py` cited `test_a_sibling_of_the_canonical_name_is_not_the_canonical_file`,
which this round had already replaced. Corrected to the live name. Second occurrence, in §7 of
this protocol (`test_every_shipped_hook_is_mirrored_across_the_kits`), corrected to
`tools/test_hooks.py::test_shared_kit_files_identical`.

**A THIRD occurrence, missed here and found by the verifier in round 4 (V8):** §6c/F2 above still
named the same dead test as its red proof. It is corrected there, and the red is re-measured rather
than re-worded. The count in this section ("two occurrences") was therefore wrong when it was
written; the honest number for the whole document is **three**, and the way to keep it honest is a
scan, not a count — an AST scan over `tools/test_hooks.py` + `tools/test_hooks_v2.py` for every
backticked `test_…` name in this file and in the gate.

### F15 — "cosmetic" was the wrong diagnosis

The line held two literal **U+0008** bytes where `\b` belongs, so `re.search` could never match a
command line: the `inside_scripts` exemption in `_writes_protected` was dead code. §9 of this
protocol had looked straight at it and called it stray spaces. Repaired — and repairing it alone
would have opened a hole, because the naive regex forgives *any* segment naming the validator,
including `cp evil.py scripts/ledger_add.py && cd scripts && git commit`. It is safe only together
with F11's bare-name rule, and that is exactly what the `f15naive` mutation measures.

### F16 — the spellings were narrower than their own docstring

`_QUOTING_SPELLINGS` put quoting only around the WHOLE word, while the defect the docstring quotes
is `scripts/ledger_add.py'.bak'` — quoting around the SUFFIX. The spellings are now **generated**
from the word (whole-word quoting, empty spans at either end, and the same applied to the word
split at its last dot, which is where a suffix begins), so the measured shape is among them.

### Red seen (fresh clone per mutation, `redproof3.py`)

| mutation | what it puts back | red |
|---|---|---|
| `anchor10` | the `(?![\w.-])` anchor | **36 failed** |
| `cdwide` | the text-wide decoy exemption | **4 failed** |
| `decoywide` | the unguarded decoy check | **1 failed** |
| `f15naive` | the exemption forgiving any validator mention | **1 failed** |
| `wordend_lt` | `<>` out of the word-end set | **1 failed** |
| `wordend_quotes` | `"'` out of the word-end set | **3 failed** |
| `one_reading` | only the first shell reading | **1 failed** |

### Not mine

F17 (PowerShell backtick) and hole-list candidates 1–3 are the coordinator's, untouched. Still
open and **pre-existing at the HEAD twin**, named here because I measured them: B5/S6 (a decoy or
sibling run with **no** blocked operation in the same call — `_writes_ledger` is only consulted
when one is present) and S5 (`scripts/harness.py+x submit-result …` names neither a ledger path nor
a protected file, so this gate has nothing textual to object to).

## 6e. Rework after the verifier's round-4 FAIL (V1–V6, V8, plus one of my own)

Measured on my own rig, `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0083\rework4\`: an office
project scaffolded from a fresh copy of this working tree (`scaffold.sh`), driven through its OWN
registered PreToolUse chain (`chain.py`, registration read from that project's `settings.json`),
against three twins — `proj0` (this tree), `proj_pre` (the tree as the verifier found it) and
`proj_head` (HEAD `bbf4084`). Batteries: `cases.json` (58), `cases_extra.json` (9),
`cases_leak.json` (4), `cases_edge.json` (20), `cases_e10.json` (6), `cases_keep.json` (20).

**Result: `proj_pre` 24 mismatches → `proj0` 0**, plus the two named over-refusals in `cases_edge`
(below) which are identical in both twins. The same batteries under `tool_name: "PowerShell"`:
identical verdicts (the verifier had not measured that side).

### V1 — a quoted metacharacter in a filename was a word end for this reader

`_readings_of` (then `_quoting_resolved`) removed the quote marks before any reader looked, so the
text lost the one thing that tells a word END from a metacharacter INSIDE a filename.

| line | HEAD | before | after |
|---|---|---|---|
| `python "scripts/ledger_add.py evil.py" ledger/2026.csv && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `python 'scripts/ledger_add.py(1).py' ledger/2026.csv && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `python 'scripts/ledger_add.py>evil' …`, `…py<evil`, `…py  evil.py`, `…py'evil.py` | rc 2 | rc 0 | rc 2 |
| `python "scripts/harness.py evil.py" evidence --summary "x ledger/2026.csv" && git commit` | rc 2 | rc 0 | rc 2 |
| `python "scripts/ledger_add.py" --validate ledger/2026.csv && git commit -m x` (control) | rc 0 | rc 0 | rc 0 |

**The verifier's own candidate could not work, and the reason matters:** it kept `word` where the
reading carried a boundary character — but `_compat.shell_words` builds `ShellWord` FROM the
quote-removed text, so `word` and `reading` are the same string whenever no backslash is involved.
His edit was a no-op on exactly the cases it aimed at.

The construction here is `_as_one_word`: a value the shell BUILT (quote marks removed, or a
backslash consumed) is re-emitted WITH a quote mark whenever it carries a word-end character; a
value the text spells literally is passed through, because there the character really is the
shell's own separator. Condition and character class are both derived — `_WORD_END_CHARS` is the
single statement of the set, `_WORD_END` and `_A_WORD_END_CHAR_RX` are built from it.

What it does **not** buy is stated in its docstring and measured: `_SEGMENT_SPLIT_RX` and the `|`
split in `_stages_beside_the_vouched_runs` are plain text splits and still cut at a quoted `;`/`|`
(`--summary "reversed; see scripts/ledger_add.py"` and `--note "a|b"` are rc 2 before and after).
That is over-refusal and fail-closed; making those splits quote-aware would swallow the separator
`_SUBSTITUTION_OPEN_RX` deliberately injects inside a quoted span and reopen `BUG-0065`.

### V2 — the exemption vouched for a MENTION, not a RUN

`_only_the_bare_validator` asked only whether the segment named `ledger_add.py` without a directory
part. Every segment carrying the bare name as a **target** was therefore free.

| line | HEAD | before | after |
|---|---|---|---|
| `cd scripts && cp ../evil.py ledger_add.py` (also `mv`, `curl -o`, `tee`, `sed -i`, `install`, `rm`) | rc 2 | rc 0 | rc 2 |
| `cd scripts ; cp …`, `cd ./scripts && cp …`, `… && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd scripts && sed -i s/119/150/ ../ledger/2026.csv ledger_add.py && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd scripts && cp evil.csv ../ledger/2026.csv ledger_add.py && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x` (control) | rc 2 | rc 0 | rc 0 |

End to end with real hook processes and a real bash (`attack_e1.py`): on `proj_pre`, STEP 1 commit
with a broken ledger rc 2 → STEP 2 `cd scripts && cp ../evil.py ledger_add.py` rc 0, really
executed, the judge is now `import sys / sys.exit(0)`. On `proj0` the same STEP 2 is rc 2 for all
three write shapes and STEP 3 stays rc 2.

`_BARE_VALIDATOR_RUN_RX` is not a second pattern: `_canonical_run` grew a `directory` parameter and
the bare form is that same construction with an empty one. A **leading `./` is not a directory
part** — the run pattern always accepted it while the name half rejected it, a dead branch reading
as a handled case; the two halves agree now.

### V3 — `cd` into any name that starts with `scripts`

`\b` after `scripts` is satisfied before `-`, `.` and `/`.

| line | HEAD | before | after |
|---|---|---|---|
| `cd scripts-evil && python ledger_add.py ledger/2026.csv && git commit -m x` | rc 2 | rc 0 | rc 2 |
| `cd scripts.bak && …`, `cd scripts/../evil && …`, `cd scripts-evil && cp … ledger_add.py && …` | rc 2 | rc 0 | rc 2 |

The anchor is `_WORD_END`, the set the file already has, and the test is parametrised over the 84
characters that are **not** a word end — a longer directory name is any name that continues past
this one.

### V4 — the gate refused the remedy in the spelling it prints

`VALIDATOR` was `os.path.join("scripts", "ledger_add.py")`, so on Windows the message read
`python scripts\ledger_add.py --validate …` beside a findings list naming `ledger/2026.csv`.

Measured by reading the refusal the gate actually printed and feeding it straight back
(`printed.py`): HEAD printed `scripts\ledger_add.py` and accepted it (rc 0); the tree as the
verifier found it printed the same and **refused** it (rc 2); `proj0` prints
`scripts/ledger_add.py` and accepts it (rc 0). `VALIDATOR` is now spelled with a forward slash —
one place, and `os.path.join(root, …)` takes it unchanged.

**Not closed, named:** a hand-typed `python scripts\ledger_add.py --validate ledger/2026.csv &&
git commit` stays rc 2. The POSIX reading of that word eats the backslash, and this gate refuses if
ANY reading says "write" — the deliberate direction. What is fixed is that the gate no longer
*advertises* a line it refuses.

### V5 — the monotonicity test could not fail

The old cut ran over lines with no backslash, so every line had exactly one reading, and it fed the
single reading back into a judge that resolves again: `judge(line) or not judge(line)`.

The test now runs over four lines the two shells really read differently, asserts `len(readings)
== 2` first (so the tautology cannot return silently), and judges the single reading with the
per-reading predicate.

**The property was FALSE when it was finally measured.** `_readings_of` joined its readings into
one text; `inside_scripts` was computed over that text, so a `cd scripts` present only in the POSIX
reading exempted the PowerShell reading too:

| line | HEAD | before | after |
|---|---|---|---|
| `echo start ; c\d scripts ; python ledger_add.py --validate ledger/2026.csv ; git commit -m x` | rc 2 | rc 0 | rc 2 |
| `echo start ; c\d scripts ; python ledger_add.py ledger/2026.csv ; git commit -m x` | rc 2 | rc 0 | rc 2 |

PowerShell's `;` runs the rest whatever the failed `cd` did, so this is a chain, not a curiosity.
Both predicates are now `any(<per reading>)` over `_readings_of`.

### V6 — the comment claimed a holes-list entry that does not exist

The expansion gap sentence pointed at `docs/POST_V2_WISHLIST.md`. It now says the gap is open and
points at nothing this task does not write. F13 above is corrected in the same direction.

### V8 — the third dead test pointer

§6c/F2 named a test that does not exist. Corrected, and the red **re-measured** rather than
re-worded. An AST scan (`deadpointers.py`, every backticked `test_…` in the gate, in this protocol
and in `tools/test_hooks_v2.py`, resolved against the two test modules) shows **0 dead pointers in
the gate**; the remaining hits in this protocol are the F14 sentences that name the dead pointers
they corrected, and the hits in the test module are pre-existing fixture filenames.

### One of my own, found while hunting for it: the pre-filter was narrower than the decision

`handle_pre_tool_use` asked `_PROTECTED_RX`/`_PROTECTED_DIR_RX` of the **raw** command and only
then called `_writes_protected`, which resolves quoting first. A quote mark between a copy verb and
its destination is invisible in the raw view — the copy branch of `_PROTECTED_DIR_RX` has no place
for one while the flag branch does — so the branch that would have refused was never reached:

| line | HEAD | before | after |
|---|---|---|---|
| `cp -r evil/. "scripts/" && git commit -m x` | rc 0 | rc 0 | rc 2 |
| `rsync -a evil/ "scripts/"`, `cp evil.py "scripts/"`, `mv evil.py "scripts/"` | rc 0 | rc 0 | rc 2 |
| `ruff check "scripts/" && git commit -m x` (control) | rc 0 | rc 0 | rc 0 |
| `python "scripts/ledger_add.py" --validate ledger/2026.csv && git commit -m x` (control) | rc 2 | rc 0 | rc 0 |

`_writes_protected` answered True the whole time. The pre-filter now reads the raw text **and**
every reading; adding views can only make the branch run more often, and what it refuses is still
the decision's answer.

### Red seen — fresh clone per mutation, outside the repo (`rework4\redproof.py`)

| mutation | what it puts back | red |
|---|---|---|
| `v1_plain_words` | quote removal spells every value plainly again | **22 failed** (`test_a_quoted_word_end_character_does_not_end_the_word`) |
| `v2_mention` | the exemption vouches for a mention | **12 failed** (11 × `test_the_step_inside_forgives_a_run_and_not_a_target`, 1 × `…asks_for_a_run_and_not_for_a_mention`) |
| `v3_cd_prefix` | `\b` after `scripts` | **20 failed** (`test_only_the_validators_own_directory_forgives_the_bare_name`) |
| `v4_join` | `os.path.join` for the printed validator path | **1 failed** (`test_the_remedy_this_gate_prints_is_one_it_accepts`) |
| `v5_joined` | the readings judged as one joined text | **2 failed** (`test_a_second_shell_reading_can_only_add_refusals`) |
| `v5_one_reading` | only the first reading reaches the judges | **5 failed** (4 × the same, 1 × `test_the_resolved_view_keeps_every_reading_the_shells_disagree_about`) |
| `dotslash` | the two halves disagreeing about `./` | **1 failed** (`test_the_step_inside_asks_for_a_run_and_not_for_a_mention`) |
| `prefilter_raw` | the pre-filter on the raw text only | **4 failed** (`test_the_prefilter_sees_everything_the_decision_sees`) |

And the **older** tripwires, re-anchored and re-measured against this state so the rework did not
quietly disarm them: `anchor10` → **36 failed**, `cdwide` → **3 failed**, `wordend_lt` → **1
failed**.

### Runtime

Real hook process, adversarial inputs up to 110 000 characters (`timing.py`): **0.14–0.35 s** per
call after the rework, **0.13–0.34 s** before it. No backtracking outlier.

## 6f. Rework after the verifier's round-5 FAIL (P1–P5)

The verifier's report is `…\_round-scratch\TSK-0083\verify5\REPORT-5.md`. His two withdrawals
(the V1 candidate, the size of V4) are accepted as written and nothing was changed for them.

### P1 (blocking) — an exemption given to a SEGMENT vouches for the whole pipeline

**Mechanism.** `_only_the_bare_validator` was asked of the whole segment at three call sites
(`:658`, `:711`, `:730`) and its `continue` skipped the segment. A segment is a whole PIPELINE —
`|` is deliberately not a separator in `_SEGMENT_SPLIT_RX` — so every neighbouring stage came free
with it. That is the same class `_stages_beside_the_vouched_runs` was built for; the third
exemption, which this task made load-bearing, had the defect again.

**Before.** Verifier battery `cases_s.json` through the FULL registered chain of a scaffolded
office project: **7 of 12 mismatches**, e.g.

```
cd scripts && python ledger_add.py --validate ../ledger/2026.csv | tee ledger_add.py && git commit -m x   rc 0
cd scripts && python ledger_add.py --validate ../ledger/2026.csv | tee ../ledger/2026.csv && git commit -m x   rc 0
```

**Built.** The third exemption became a STAGE exemption like the other two:
`_stages_beside_the_vouched_runs(segment, inside_scripts)` drops a stage that runs the entry
point, the canonical validator, or — after a step into `scripts/` — the bare validator. The three
`continue`s are gone, and the second decoy check in `_a_reading_writes_the_ledger` now asks the
stages instead of the segment. `inside_scripts` is a required parameter, not a default, so a
caller cannot silently lose or widen the exemption.

**After.** `cases_s` **7 → 0 mismatches**, `cases_q` 3 → 0, under `tool_name: "Bash"` and
`"PowerShell"` alike. The verifier's own end-to-end rig `attack_q21.py` (real hook processes, real
`bash`, file witness): STEP 2 gate **rc 0 → rc 2**, so the line that truncated the judge from
32 823 to 0 bytes no longer passes the chain. Two FURTHER holes of the same class were found by
this rework and are closed with it, both measured against the round-5 shipped hooks:

```
cd scripts && tee ledger_add.py | python ledger_add.py --validate ../ledger/2026.csv && git commit -m x
    round 5 rc 0 -> now rc 2     (the vouched stage standing LAST in the pipeline)
cd scripts && python ledger_add.py --validate ../ledger/2026.csv | python ledger_add.py --validate ../ledger/2026.csv | rm ledger_add.py && git commit -m x
    round 5 rc 0 -> now rc 2
```

**Red seen** (clone outside the repo, `…\rework6\clone`, the three `continue`s put back and the
third exemption removed from the stage list):

```
python -B -m pytest tools/test_hooks_v2.py -q -k "…"   ->  10 failed, 218 passed
   all ten: test_a_vouched_run_frees_its_own_stage_and_not_its_neighbours[the bare validator …]
```

The test is a property over the stages, not a list of spellings: three vouched runs × five writing
neighbours × two targets (the judge, the ledger) × both pipeline orders, and each neighbour is
asserted refused ON ITS OWN first, so an entry that stopped being a write shows up instead of
passing quietly. Its counter-end is
`tools/test_hooks_v2.py::test_a_reading_neighbour_of_a_vouched_run_is_still_allowed` (nine cases),
without which the property could be satisfied by refusing every pipeline.

### P2 (blocking) — the docstring claimed the protection P1 refuted

`_stages_beside_the_vouched_runs`'s "a write into it from any other stage is refused" named two
tests. **Measured**: with the P1 defect restored, both stay green — the same selection of 131
pre-existing cases (`same_constructs`, `prose_about_the_ledger`, `step_inside`, `stepping_into`,
`only_the_validators_own`, `remedy_typed`) is **131 passed** under `p1_segment_wide`. They could
not measure the property, because none of them drives the bare exemption inside a pipeline. The
sentence now says what the code does — the other stage is left in the list for the callers to
judge — and names the test that goes red without it as well as the two that were there.

### P3 (claim defect) — `_as_one_word` described a mechanism the code does not have

`_WORD_END` does go on treating a quoted metacharacter as a boundary; what protects is that the
two VOUCHING anchors (`_canonical_run`, `_CD_SCRIPTS_RX`) press the path straight against `\s+`
and leave no room for a quote mark, while the word `_as_one_word` builds now BEGINS with one. The
paragraph says that, and it says the trap: `_PROTECTED_DIR_RX` carries a `["']?` in that position
and is right to, being a refusing reader — copying it into a vouching anchor reopens V1.

**Red seen**, both halves of the trap, in the clone:

```
["']? inserted after cd\s+ in _CD_SCRIPTS_RX
   -> 16 failed  (all of test_a_quoted_directory_name_does_not_forgive_the_bare_validator, new)
["']? inserted after \s+ in _canonical_run
   -> 22 failed  (all of test_a_quoted_word_end_character_does_not_end_the_word, pre-existing)
```

The new test probes its characters off `_WORD_END` (16 of them) rather than listing them.

### P4 — the no-directory half of `_only_the_bare_validator` was load-bearing and unmeasured

The docstring's justification (`python ledger_add.py && rm ledger_add.py`) is refuted by the
caller: `&&` splits that into two segments before this predicate sees either. Replaced by the
shape a split cannot take apart — a decoy handed to the canonical run as an ARGUMENT — and pinned.

**Red seen** in the clone, the half removed:

```
module view:  5 failed  (test_a_validator_with_a_directory_part_loses_the_step_inside, all five)
full chain :  cd scripts && python ledger_add.py --validate ../ledger/2026.csv ../tools/ledger_add.py && git commit -m x
              rc 2 -> rc 0   (cases_s S8, verifier's finding reproduced)
```

The five parametrised directory parts are generated around one directory word (`tools/`,
`../tools/`, `./tools/`, `/tmp/evil/`, `a/b/`), and the same case asserts the counter-end: the
bare spelling of that run is the advertised remedy and stays rc 0.

### P5 (pre-existing) — a precondition in a comment that no code path states

`_SHELL_WRITE_RX` was defined and read by nothing (AST check over the module: the name occurs in
no `Name` node). The read-only allowlist replaced it a round earlier. The constant is **deleted**
and the sentence rewritten to name what really bounds `_LEDGER_PATH_RX`: `_verb_only_reads` over
the stages beside the vouched runs, plus the redirect targets of the same segment.

**No red test, and that is stated rather than papered over**: deleting dead code cannot make a
test fail, and inventing one would be the "test that cannot fail" this repo keeps finding. What is
measured is the deadness (AST) and that the full suite is green without it.

### The behaviour this rework WIDENS

Measured against the round-5 shipped hooks in a twin of its own (`cases_widen.json`, 16 cases):

- **A DECOY PATH INSIDE A VOUCHED STAGE IS NOT A DECOY ANY MORE.** That is the mechanism, and it
  is stated as one because it has two spellings and a third would otherwise arrive unrecognised:
  the decoy path may be the vouched stage's OWN argument prose, or it may stand in a neighbouring
  stage that only reads. Both are "inside the region vouching frees"; neither is refused now.
  Measured (round 5 → now, verified again after the round-6 rework):

  ```
  python scripts/ledger_add.py --validate ledger/2026.csv tools/ledger_add.py && git commit -m x   HEAD 2 / R5 2 / now 0
  cd scripts && python ledger_add.py --help | cat ../tools/ledger_add.py && git commit -m x        HEAD 2 / R5 2 / now 0
  python scripts/harness.py doctor | cat tools/ledger_add.py && git commit -m x                    now 0
  ```

  The two spellings are NOT the same size, and that was re-measured rather than assumed. Inside the
  vouched stage's own arguments the decoy always survives — the segment has no stage left to judge.
  In a neighbouring stage it survives only while that stage reads AND the segment names no ledger
  path: a ledger path brings the per-segment decoy check in `_a_reading_writes_the_ledger` back
  into play. Counter-half, all rc 2 now:

  ```
  python scripts/ledger_add.py --validate ledger/2026.csv | cat tools/ledger_add.py && git commit -m x     (a read, but a ledger path)
  python scripts/ledger_add.py --validate ledger/2026.csv | tee tools/ledger_add.py && git commit -m x     (a write)
  python scripts/ledger_add.py --validate ledger/2026.csv | python tools/ledger_add.py && git commit -m x  (a run)
  python scripts/harness.py doctor | tee tools/ledger_add.py && git commit -m x                            (a write, no ledger path)
  ```

  `_only_the_bare_validator` holds a stricter line for its OWN exemption — every validator mention
  on that stage must be bare
  (`tools/test_hooks_v2.py::test_a_validator_with_a_directory_part_loses_the_step_inside`) — and
  the same rule cannot be applied to the other two runs without giving that half up.
- **`H62` in `docs/POST_V2_WISHLIST.md` is PARTLY closed — two of its three vouched runs, not the
  third.** The second decoy check now asks the stages, which is the one-line candidate that entry
  describes; what it does not reach is the bare validator, where `_only_the_bare_validator` still
  requires every validator mention on the stage to be bare, so a decoy path in the prose drops the
  vouching and the line stays refused. Measured (`cases_h62.json`, verifier's numbers reproduced):

  ```
  python scripts/harness.py submit-result --summary 'moved tools/ledger_add.py, …'   HEAD 2 / R5 2 / now 0   closed
  python scripts/ledger_add.py --validate ledger/2026.csv --note 'see tools/…'       HEAD 2 / R5 0 / now 0   closed
  cd scripts && python ledger_add.py --validate ../ledger/2026.csv --note 'tools/…'  HEAD 2 / R5 2 / now 2   OPEN
  ```

  The open third is not closable with the same line: the half that would have to go is the one
  `test_a_validator_with_a_directory_part_loses_the_step_inside` pins as load-bearing (P4). Six
  counter-cases (decoy run, decoy write, decoy beside a real ledger write, …) stay rc 2. **The
  holes list was NOT edited** — it is the lead's this round; this is reported, not changed.

### Everything the verifier confirmed, re-measured after the change

`cases_a` 2/19, `cases_b` 1/20, `cases_d` 2/13 — the SAME residuals he names as pre-existing
(A5/A14, R1, P2/P3), no new ones. `cases_c` 0/16, `cases_y` 0/4, `cases_r` 0/18, `cases_m` 0/5,
`cases_fp` 0/20, `cases_fp2` 0/24. Runtime on adversarial input up to 143 000 characters:
**0.13–0.51 s**, with the 4 000-stage pipeline form at 0.21 s — the form this round makes the gate
look at per stage.

## 7. Mirrors, stamps, suites

- **Mirrors:** `gate_ledger_valid.py` ships in `office-team` **only**. `tools/test_hooks.py::_assert_mirrored`
  skips a name that exists in fewer than two kits (`len(copies) < 2`), so no mirror copy and no
  `KIT_SPECIFIC_HOOKS` entry is due; `tools/test_hooks.py::test_shared_kit_files_identical` passed
  in the full run below. (That name was wrong here for two rounds — it read
  `test_every_shipped_hook_is_mirrored_across_the_kits`, which exists nowhere in the repo. F14.)
- `python tools/bump_kit_version.py` → office-team `2026.08.23-3` → `2026.08.23-9` (round 3) →
  `2026.08.24-1` (round 4) → `2026.08.24-2` → `2026.08.24-3` (round 5 rework) → `2026.08.24-4` →
  `2026.08.24-5` → **`2026.08.24-6`** (round 6 rework; each of the last two bumps followed a
  docstring correction. The first whole-suite run of that rework was made on a stale stamp and
  reported 10 failures — nine installer/scaffold tests plus `test_validate_py_is_green`, all of
  them the stamp and none of them the change. That is rule 7 of `CLAUDE.md` measured once more);
  dev-team and research-team unchanged at `2026.08.23-3`.
- `python -m ruff check .` → All checks passed (last run after every edit).
- `python tools/validate.py` → all structural checks passed (last run after every edit).
- `python -m pytest tools/ -q` at stamp `2026.08.24-6`: **3754 passed, 14 skipped in 2415.43 s**,
  exit 0 (`impl7\full-suite3.log`; `full-suite2.log` is the identical 3754/14 run at `-5`). The
  DELIVERED tree is `2026.08.24-7`, which differs from that one by a single docstring paragraph
  and its stamp; on it, the affected suite `tools/test_hooks_v2.py` was run in full — **2042
  passed in 938.65 s**, exit 0 (`impl7\hooks-v2-final.log`). The whole-suite run on the delivered tree is the lead's, bundled
  across rounds — a round-time decision, taken by the lead, not a measurement skipped here.
  Round-1 was 3011/14, round-2 3026/14, round-3 3053/14, the
  round-3 final 3245/14, round-4 3384/14, round-5 3444/14; the growth is the cases each round
  added, all named above — round 5's **+60** are 30 (the stage property, three hook calls each) +
  9 (its reading counter-end) + 5 (the directory part) + 16 (the quoted directory name), and round
  6's **+310** are the ones §11 names.
- `.claude/hooks/test_gates.py` **not run**: `.claude/**` is forbidden scope here and was not
  touched, so the gates' derivation surface did not move.

## 8. Changed files (this task)

```
team-kits/office-team/hooks/gate_ledger_valid.py
team-kits/office-team/VERSION            (bump_kit_version.py)
tools/test_hooks_v2.py
```

Everything else `git status` shows under `project_memory/` was there before this task started.

## 9. Named, not closed

**Round 5 rework additions:**

- **A decoy path INSIDE a vouched stage is not a decoy any more** — the mechanism, its two
  measured spellings and its counter-half are in §6f. It writes nothing and runs nothing; a write
  and a run in that position are both still rc 2. Named here because it is a refusal this rework
  removes, not one it adds.
- **`H62` is PARTLY closed by this rework** — for the entry point and the canonical validator, not
  for the bare validator run from inside `scripts/`; the residual line and why it is not closable
  without giving up P4 are in §6f. Its entry in `docs/POST_V2_WISHLIST.md` therefore needs
  narrowing, **not** deleting. Measured, **not edited** — the holes list belongs to the lead this
  round; this is a hand-back, not a change.
- **The `.csv` working-directory fallback at the end of `_a_reading_writes_the_ledger` still asks
  `_verb_only_reads` of the whole segment**, not per stage. It is the last reader in this function
  that is not stage-wise. Its direction is over-refusal (the first verb of a pipeline decides), so
  it is not a hole; it is unchanged from HEAD and untouched here.
- **The PostToolUse branch is still unmeasured** in this rework, as in rounds 4 and 5.
- **`gate_ledger_valid.py` sits in the working copy with CRLF line endings** while its sibling
  hooks are LF. Not from this rework — the round-5 copy the verifier kept
  (`verify5\repo\…\gate_ledger_valid.py`) is already CRLF, and the HEAD blob is LF. `.gitattributes`
  declares `* text=auto eol=lf`, so what gets committed is LF either way, and
  `kernel.hashing.kit_hash` normalises CRLF before stamping. Named, not changed: rewriting the file
  to fix it would be a whole-file diff for a difference git removes.

**Round 4 additions, each measured in all three twins:**

- **A hand-typed backslash in the validator path is refused**:
  `python scripts\ledger_add.py --validate ledger/2026.csv && git commit -m x` → rc 2 (rc 0 at
  HEAD). One of the two shell readings consumes the backslash and the canonical path is gone in
  that reading; this gate refuses if any reading says "write", which is the direction it is built
  in. What V4 closed is the gate ADVERTISING that spelling. The uniform spellings are rc 0.
- **A quoted `;` or `|` still cuts a segment / a pipeline stage**:
  `python scripts/harness.py evidence --summary "reversed; see scripts/ledger_add.py" && git
  commit -m x` and `python scripts/ledger_add.py --validate ledger/2026.csv --note "a|b" && git
  commit -m x` are rc 2 before and after this round. `_SEGMENT_SPLIT_RX` and the `|` split in
  `_stages_beside_the_vouched_runs` are plain text splits. Over-refusal, fail-closed, and the
  obvious fix is measured to be wrong: a quote-aware split would swallow the separator
  `_SUBSTITUTION_OPEN_RX` injects inside a quoted span and reopen `BUG-0065`.
- **The expansion gap** (`cp evil.py scripts/$f` with `f` unset) is unchanged and now says so in
  the code without pointing at a document. It is the lead's to enter in the holes list.
- **A decoy or sibling run with no blocked operation in the same call** stays rc 0 — confirmed
  again in this round's `attack_e1.py` run: `python "scripts/ledger_add.py evil.py"
  ledger/2026.csv` alone is rc 0 while the same line with `&& git commit -m x` is rc 2.
  `_writes_ledger` is only consulted when a blocked operation is present. Pre-existing at HEAD.
- **`.claude/hooks/test_gates.py` not run**, and the reason is the same as in round 3: `.claude/**`
  is forbidden scope here, `git status` shows it unchanged, and the gates' derivation surface
  (`tools/bump_kit_version.py`, `kernel.hashing`, `CLAUDE.md`) was not touched either.

**From round 3:**

- ~~**The gate refuses its own advertised remedy**: `cd scripts && python ledger_add.py --validate
  ../ledger/2026.csv && git commit -m x`, rc 2 at HEAD and here, because the `_DECOY_VALIDATOR_RX`
  check stands before the `inside_scripts` exemption. Not fixed here.~~ **Closed in round 3** by
  F11 (`_only_the_bare_validator` at all three exemption sites) and pinned by
  `tools/test_hooks_v2.py::test_the_remedy_typed_from_inside_the_validators_directory_still_works`:
  that line is rc 0 from round 3 on. Left visible because reversing it is what opened V2 and V3 —
  the exemption became load-bearing the moment the over-refusal in front of it went away.
- ~~`_writes_protected` carries a run of stray spaces mid-expression. Cosmetic.~~ **That diagnosis
  was wrong** and is corrected in §6d/F15: the line held two literal U+0008 bytes where `\b`
  belongs, so the regex could not match any command line and the exemption was dead code. Fixed
  this round, together with the rule that makes repairing it safe.
- `python scripts/ledger_add.py -o scripts/` is now allowed (§5). It writes nothing, because the
  shipped validator's argparse rejects `-o` — but the GATE does not know that; it vouches for the
  invocation, not for the option list. The bound is that the canonical file is protected against
  replacement. Not turned into a test, because a test that enumerated the validator's options would
  be exactly the enumeration this round removed.

## 10. Scratch artefacts (outside the repo, to be cleaned at round close)

`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0083\`

- `repro.py` — the 12-case matrix of §1/§6 against the repo's shipped hook
- `inspect_rx.py` — the module-level view of §1
- `what_the_lookahead_catches.py` — §2
- `pipeline_probe.py` — the four pipeline shapes of §2
- `flip_probe.py` — §5
- `f2_probe.py`, `f3_probe.py`, `f4_probe.py`, `why.py` — §6b
- `chainrun.py` — syncs the repo's hooks into the verifier's scaffolded project and drives its
  `verify/chain.py` (the FULL registered chain) over a case file; `cases_r3.json` — the §6c
  regression and counter-direction battery; `selfaudit.py` — the self-audit that opened §6c
- `redproof.py` — one fresh clone per mutation, prints the tests that go red (§6c)
- `make_clone.py`, `restore_defect.py`, `naive_fix.py`, `mutate.py` — how each clone state of §4
  and §6b is re-created (`mutate.py <clone> letters|anchor|redirect`)
- `clone/` — left carrying the **F4 candidate**, NOT the repo's state
- `full-suite.log`, `full-suite-2.log`, `rest-suite.log`, `hook-suite-2.log`, `rest-suite-2.log`
  — the runs of §7 (`full-suite-3.log` is the killed run, incomplete, kept for the record)

Round 4 (`…\_round-scratch\TSK-0083\rework4\`):

- `scaffold.sh` — builds an office project from a copy of this tree; `repo0` is that copy as the
  verifier found it, `repo_now` the copy with this rework in it
- `proj0` / `proj_pre` / `proj_head` — the three twins (this tree, the pre-rework tree, HEAD
  `bbf4084`); `proj_e1`, `proj_e1_pre`, `proj_fix` are throwaways of the chain runs
- `chain.py` — the verifier's chain driver with `CHAIN_TOOL` added, so the same battery runs under
  `tool_name: "PowerShell"`
- `cases.json`, `cases_extra.json`, `cases_leak.json`, `cases_edge.json`, `cases_e10.json`,
  `cases_keep.json` — the batteries of §6e
- `attack_e1.py` — the end-to-end chain (broken ledger → replace the judge → commit), real hook
  processes plus real bash
- `printed.py` — reads the remedy the gate PRINTS out of its own refusal and feeds it back (V4)
- `probe.py` — module view: readings, segments, stages, predicates, pre-filter
- `redproof.py` — one fresh clone per mutation, prints what goes red (`REDPROOF_TAIL` to see all)
- `deadpointers.py` — AST scan for dead backticked test names (V8)
- `timing.py`, `timing_pre.py` — runtime on adversarial input, both twins
- `full-suite.log` — the run of §7

Round 5 rework (`…\_round-scratch\TSK-0083\rework6\`):

- `run_cases.py` — syncs a hook directory into a scaffolded twin and drives the verifier's
  `verify5\chain.py` (the FULL registered chain) over a case file, under either tool name
- `mutate.py` — the four mutation tables of §6f; restores the clone afterwards.
  `mutate_chain.py` — the same mutations, driven through the registered chain instead of pytest
- `clone/` — the repo copy the red proofs run in, left in its RESTORED (unmutated) state
- `cases_widen.json` — the 16 cases of "what this rework widens", run against round-5 and now
- `cases_h62.json` — the eight cases that measure `H62` closed and its counter-direction
- `full-suite.log` — the run of §7

## 11. Round 6 rework — R1 to R5 of the round-6 verifier report

Twins for everything below: `proj_before` (this tree as the round-6 verifier found it, office
`2026.08.24-3`) and `proj_after` (with this rework, office `2026.08.24-4`), each scaffolded from
its own repo copy with `scaffold_team.sh`; `proj_head` is the verifier's HEAD twin, reused. Every
verdict is a REAL hook process; where a line says "chain", it is the full `PreToolUse` registration
read out of that project's own `settings.json`, both under `tool_name: Bash` and `PowerShell`
(`impl7\chain.py`, `impl7\sweep.py`). Rig: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0083\impl7\`.

### R1 (blocking) — a WRITING stage could BE the vouched stage

**The property that now holds:** a vouched run is the BEGINNING of the stage it vouches for.
`_canonical_run`'s prefix was the class `(?:^|[;&|(])`. Every reader of the three patterns it
builds is handed ONE pipeline stage, and by then `;`, `&` and `\n` are cut by `_SEGMENT_SPLIT_RX`
and `|` by the stage split — so three of the four class members were dead, and the fourth, `(`, is
the one character that can still stand anywhere inside a stage, quoted argument prose included.
The fix is the anchor, not a list of the spellings that were measured:

```python
r"^[\s(]*(?:python[0-9.]*|py)\b"        # was r"(?:^|[;&|(])\s*(?:python[0-9.]*|py)\b"
```

(The rework below replaces `[\s(]*` with `_STAGE_OPENING`, which is the same class minus the line
breaks the cut removes — see F3.)

This is the verifier's own minimal fix, re-measured here rather than adopted on his word. All
three vouching patterns come from `_canonical_run`, so `_LEDGER_ADD_RUN_RX`, `_ENTRY_POINT_RUN_RX`
and `_BARE_VALIDATOR_RUN_RX` are corrected by the one line.

**Before / after, full registered chain, identical under both tool names** (`impl7\cases_r1.json`,
and the verifier's own `cases_u.json` **8 → 0** and `cases_z.json` **7 → 2**, the remaining two
being the R3 residue):

```
cd scripts && tee ledger_add.py '(python ledger_add.py --validate ../ledger/2026.csv)' < /dev/null && git commit --allow-empty   0 -> 2
tee scripts/ledger_add.py '(python scripts/ledger_add.py --validate ledger/2026.csv)' < /dev/null && git commit --allow-empty    0 -> 2
cd scripts && rm -f ledger_add.py '(python ledger_add.py --validate ../ledger/2026.csv)' && git commit --allow-empty             0 -> 2
cd scripts && tee ../ledger/2026.csv '(python ledger_add.py --validate ../ledger/2026.csv)' < /dev/null && git commit --allow-empty  0 -> 2   (the LEDGER)
cd scripts ; tee ledger_add.py '(python …)' ; git commit --allow-empty                                                          0 -> 2
cd scripts && sed -i 's/x/(python …)/' ledger_add.py && git commit -m x                                                         0 -> 2
curl -o scripts/ledger_add.py 'http://x/(python scripts/ledger_add.py --validate ledger/2026.csv)' && git commit -m x            0 -> 2
tee scripts/ledger_add.py '(python scripts/harness.py doctor)' < /dev/null && git commit --allow-empty                           0 -> 2
cd scripts && tee ledger_add.py '(python …)' < /dev/null              (no commit in the line)                                   0 -> 2
control, same write without the paren prose                                                                                     2 -> 2
```

**The counter-end, unchanged rc 0** — the subshell spelling of a vouched run is still a vouched
run, which is what stops the fix from being "refuse every paren":

```
(python scripts/ledger_add.py --validate ledger/2026.csv) && git commit --allow-empty            0 -> 0
cd scripts && (python ledger_add.py --validate ../ledger/2026.csv) && git commit --allow-empty   0 -> 0
((python scripts/ledger_add.py --validate ledger/2026.csv)) && git commit --allow-empty          0 -> 0
cat ledger/2026.csv | (python scripts/ledger_add.py --validate ledger/2026.csv) && git commit …  0 -> 0
python scripts/ledger_add.py --validate ledger/2026.csv --note '(cp backup.py scripts/)' && …    0 -> 0
python scripts/harness.py submit-result --summary 'ok' && git commit --allow-empty               0 -> 0
```

**The chain end to end, one session, real hook processes + real `bash` + file witness**
(`impl7\attack_chain.py`; the shell only ever runs what the gate ALLOWED):

```
                                        proj_before                proj_after
size of the judge                       32823                      32823
STEP 1  git commit -m x                 rc 2 (ledger INVALID)      rc 2 (ledger INVALID)
STEP 2  the line above                  rc 0                       rc 2  CHAIN STOPPED
        bash / size afterwards          rc 1 / 0 bytes             never ran
STEP 3  git commit -m x                 rc 0                       --
```

**Red seen** — the defect restored in a clone OUTSIDE the repo (`impl7\redrepo`, `impl7\red.py`
asserts the replacement really happened and reverts afterwards), whole file, no `-k`: see the
table at the end of this section.

### The same question asked of EVERY anchor with that prefix class

Not only the one that was reported. The rule that decides it: **on a VOUCHING reader, every
character of a prefix class that the caller has not already cut is a forgery surface, because
argument prose may contain it; on a REFUSING reader the same character can only add refusals.**

| anchor | direction | asked of | verdict |
|---|---|---|---|
| `_canonical_run` (3 patterns) | vouching | one stage | **fixed** — see R1 |
| `_INTERPRETER_SCRIPT_RX` | vouching (it REMOVES text from the pre-filter's view) | the whole reading | `;&|` are real separators there, `(` a real subshell opening; forging it would require the stripped path to BE the write target directly after `python `, which no write spelling produces. Its measured defect was a different one — see below |
| `_INLINE_CODE_RX` | refusing (a match keeps the view unstripped) | the whole reading | a forged match can only add refusals |
| `_CD_SCRIPTS_RX` | vouching | the whole reading | **forgeable, pre-existing, NOT closed here** — see §11 "named, not closed" |
| `_CD_LEDGER_RX` | refusing (it turns the `.csv` working-directory fallback on) | the whole reading | a forged match can only add refusals |

### R1b — the pre-filter was narrower than the decision it guards (found here, not reported)

`_INTERPRETER_SCRIPT_RX` strips the script argument out of the view the judge-write branch
pre-filters on. Its token was `\S+\.(?:py|pl|rb|js)`, and `\S+` runs straight through a glued `>`:

```
python scripts/ledger_add.py>scripts/ledger_add.py && git commit -m x    gate_ledger_valid alone: rc 0 -> rc 2
python scripts/ledger_add.py > scripts/ledger_add.py && git commit -m x  (spaced control)         rc 2 -> rc 2
python scripts/harness.py>.claude/ledger_state.json && git commit -m x   alone: rc 0 -> rc 2
```

Both the run and the redirect TARGET disappeared from `scanned`, so no protected path was left in
it and the refusing branch was never reached — while `_writes_protected` answered True the whole
time. The token now ends where a shell word ends, derived from the same `_WORD_END` the vouching
anchor uses. **This was never a complete chain**: the full registered chain refuses those lines at
`gate_write_scope.py` (rc 2 before and after). What it WAS is a claim the code did not build —
the comment above the pre-filter and `test_the_prefilter_sees_everything_the_decision_sees` both
say a pre-filter must not be narrower than its decision.

Direction of the change: the strip only ever REMOVES text, so a narrower strip can only make the
branch RUN more often, and what it then refuses is `_writes_protected`'s own answer. Two lines in
the verifier's `cases_d.json` move with it, both attack shapes without a commit in the line:
`python scripts/ledger_add.py.bak ledger/2026.csv` and
`python "scripts/ledger_add.py evil.py" ledger/2026.csv`, **rc 0 → rc 2** (the sibling is no longer
stripped out of the view, and `_writes_protected` calls an unvouched interpreter run on a protected
path a write). Counter-direction measured and still rc 0:
`python scripts/ledger_add.py --validate ledger/2026.csv>/tmp/out && git commit -m x`,
`python "scripts/ledger_add.py" --validate ledger/2026.csv && git commit -m x`,
`ruff check "scripts/" && git commit -m x`.

### R2 (blocking, claim) — the docstring said what R1 refuted

`_stages_beside_the_vouched_runs` claimed "keeping it canonical is what the rest of this gate
does". It now states what the code builds — the run has to be the stage's own opening word — and
adds the half that is NOT bought, which is R3's mechanism. The sentence is pinned by
`tools/test_hooks_v2.py::test_a_vouched_run_is_the_start_of_the_stage_it_frees`.

### R3 — the widening is now written as a mechanism, not as two spellings

§6f, first bullet: "a decoy path INSIDE a vouched stage is not a decoy any more", with both
spellings (the vouched stage's own argument prose, and a read-only neighbour) as instances of it.

### R4 — "H62 is closed" corrected to "partly closed"

§6f, second bullet, with the three measured lines and the reason the third is not closable without
giving up the half `test_a_validator_with_a_directory_part_loses_the_step_inside` pins (P4).
Re-measured on `proj_after` after this rework: **unchanged** (2 closed, 1 open).

### R5 (nit) — the byte count is out of the test docstring

`test_a_vouched_run_frees_its_own_stage_and_not_its_neighbours` now says "truncated the ledger's
own judge to zero bytes". The size belongs to the file, and to this report: it was 32823 bytes at
the time of the measurement.

### Tests added

- `tools/test_hooks_v2.py::test_only_a_group_opening_stands_in_front_of_a_vouched_run` — the
  property, sampled over `string.printable` (100 characters) × the three vouching patterns. The
  expectation is stated INDEPENDENTLY of the pattern, so the two can disagree; `iff`, so it
  measures both ends at once. (The rework below replaces the rule it was stated as with a
  measurement against the gate's own cut — see F3.)
- `tools/test_hooks_v2.py::test_every_vouching_run_pattern_is_named_here` — the tripwire the table
  of three owes: it fails both on a dead entry and on a fourth exemption arriving without one, and
  asserts each named pattern still matches its own run. (Round 7 asked this of the `*_RUN_RX`
  NAMES; the rework below asks it of the exemption's parsed code — see F4.)
- `tools/test_hooks_v2.py::test_a_vouched_run_is_the_start_of_the_stage_it_frees` — the same
  property through the running hook, over the three vouched runs × the judge and the ledger, plus
  the subshell counter-end in the same case.
- two cases in `test_the_prefilter_sees_everything_the_decision_sees` for R1b, plus one
  counter-direction case.

### Red seen (clone outside the repo, whole file, no `-k`)

Each defect restored in `impl7\redrepo` by `impl7\red.py`, which asserts the replacement really
happened (`count(good) == 1`) and writes the original back afterwards. Baseline of the file with
both fixes in place: **2042 passed** (round 5: 1732; the +310 are 300 = 3 patterns × 100 sampled
characters, 6 = 3 vouched runs × 2 targets, 1 = the table tripwire, 3 = the pre-filter cases).

| defect restored | whole file | which tests |
|---|---|---|
| D1 `(?:^\|[;&\|(])\s*` back on `_canonical_run` | **16 failed**, 2026 passed (15:17) | 9 × `test_only_a_group_opening_stands_in_front_of_a_vouched_run` (the characters `;`, `&`, `\|` × the three patterns), 6 × `test_a_vouched_run_is_the_start_of_the_stage_it_frees` (**all six**), 1 × `test_validate_py_is_green` |
| D2 `(\S+\.(?:py\|pl\|rb\|js))\b` back on `_INTERPRETER_SCRIPT_RX` | **3 failed**, 2039 passed (15:01) | 2 × `test_the_prefilter_sees_everything_the_decision_sees` (the two glued-redirect cases), 1 × `test_validate_py_is_green` |

`test_validate_py_is_green` is the RIG, not a finding: mutating a kit file breaks its own VERSION
stamp, and the clone is not re-stamped. It fails identically under both mutations and passes on
the delivered tree.

The clone these runs used carries the gate at stamp `2026.08.24-5`; the delivered gate differs
from it in two docstring paragraphs and nothing else — the two lines the mutations restore are
byte-identical in both.

The counts are split per test by re-running the same mutation with `-k` on each name
(`impl7\red_names.py`): 9 and 6 for D1, 2 for D2 — and
`test_only_a_group_opening_stands_in_front_of_a_vouched_run` passes 300/300
on the delivered tree, so the 291 that stay green under the mutation are the characters the
property expects to be refused either way.

### What this rework does NOT close (named, measured, not entered in the holes list)

- **`_CD_SCRIPTS_RX` can be forged from quoted argument prose, and it is PRE-EXISTING.** The
  anchor is asked of the whole reading, where `;`, `&` and `|` really are separators — but the
  segment split is deliberately quote-blind (`BUG-0065`), so a separator inside a quoted argument
  opens a segment for this reader too. Measured through the full chain, HEAD and now identical:

  ```
  python ledger_add.py --note '; cd scripts' && git commit -m x     HEAD 0 / before 0 / after 0
  python ledger_add.py --note 'x & cd scripts' && git commit -m x   HEAD 0 / before 0 / after 0
  python ledger_add.py --note 'x | cd scripts' && git commit -m x   HEAD 0 / before 0 / after 0
  control, same line without the forged step                        HEAD 2 / before 2 / after 2
  ```

  What it buys the attacker: a DECOY validator run in the same line as a commit stops being
  refused. What bounds it: **nothing in this gate** — the sentence that stood here through round 7
  claimed that creating a file called `ledger_add.py` is refused, and that is one SPELLING, not a
  bound. `_PROTECTED_RX` reads the command TEXT, so it refuses the decoy's creation exactly where
  the line spells the name; every construction that produces the name without spelling it is rc 0
  through the full registered chain, on the delivered state and under both tool names
  (`rework7\m_f1.py`):

  ```
  tee ledger_add.py < evil.py                  rc 2   the name is in the line
  cat evil.py > ledger_add.py                  rc 2   "
  n=ledger_add.py; printf 'x' > $n             rc 2   " (the assignment spells it)
  printf 'x' > $(echo ledger_add.py)           rc 0   an expansion builds the name
  cp evil.py $(echo ledger_add.py)             rc 0   "
  tar -xf evil.tar                             rc 0   the archive carries the name
  unzip -o evil.zip                            rc 0   "
  git checkout evil -- .                       rc 0   the tree carries the name
  ```

  So the chain runs through, in TWO gated calls inside one session, measured end to end against
  real bash with a git witness on the delivered state (`rework7\m_f1chain.py`):

  ```
  1  printf '%s' "$PAY" > $(echo ledger_add.py)                        gate rc 0, bash rc 0
  2  python ledger_add.py ledger/2026.csv --note '; cd scripts' && git commit -am poisoned
                                                                      gate rc 0, bash rc 0
  git show HEAD:ledger/2026.csv
    L2026-0001,NOT-A-DATE,,expense,invoice,ACME,R-1,999999.00,19.00,1.00,standard,tools,,,
  ```

  Running a decoy is only ever refused when a blocked operation stands in the same line — `python
  tools/ledger_add.py` on its own is rc 0 at HEAD and here — which is why step 2 carries the
  commit. The re-validation at gate time does not bound this chain either: the books are still
  correct when the gate reads them, and step 2 breaks and commits them in the same call. What that
  re-validation does bound is the other order — a commit while the ledger is ALREADY invalid stays
  rc 2, forged step or not (measured). Not closed here because the honest fix is a word-level
  `inside_scripts` per reading —
  a redesign of `_readings_of`'s interface — and this round had one blocking finding to close
  cleanly.
- **The same anchor has no `(`, so the remedy inside a subshell is over-refused**, also
  pre-existing: `(cd scripts && python ledger_add.py --validate ../ledger/2026.csv) && git commit`
  is rc 2 at HEAD, before and after. Deliberately NOT widened here: adding `(` to a vouching
  anchor asked of a whole reading is the R1 mechanism, and the plain spelling of the remedy works.
- Everything §9 already names stays named: the `H22` read-only classification (`awk
  'BEGIN{system(…)}'`, `sed -n 'w …'` alone are rc 0 in all three twins), the quoted separator,
  the expansion gap, the `PostToolUse` branch (untouched here).

### Round 6 rework scratch (`…\_round-scratch\TSK-0083\impl7\`)

- `clone.py` — copies the working tree out (`repo_before`, `repo_after`, `redrepo`);
  `scaffold.sh` — builds an office project plus its ledger and validator from such a copy
- `chain.py` (the verifier's driver, reused), `sweep.py` — runs a case file against two twins and
  prints only the DIFFERENCES, under both tool names; `one.py` — one hook, one line
- `cases_r1.json` (R1 and its counter-end), `cases_pf.json` (R1b), `cases_cd.json` (the
  `_CD_SCRIPTS_RX` residue); the verifier's `cases_*.json` were run unchanged from `..\verify6\`
- `attack_chain.py` — the end-to-end chain, executing only what the gate allowed
- `red.py` — restores each defect in `redrepo`, runs the whole hook-suite file, reverts;
  `red_names.py` — the same mutations with `-k`, to NAME what went red. `red3.log` is the run
  quoted above (`red.log`/`red2.log` are the earlier ones, kept: `red.log` is the run before the
  second pre-filter case was swapped for a spelling that is actually red)
- `dp.py` — the dead-pointer AST scan (gate: 29 mentions, 0 dead)
- `sweep2.log`, `sweep3.log` — the battery diffs quoted above; `full-suite3.log` — the §7 run
  (`full-suite.log` is the run on the stale stamp, kept for the record; `full-suite2.log` the
  identical run one docstring earlier)
- reused from the verifier: `verify5\chain.py`, `attack_q21.py`, `timing.py`, `cases_*.json`,
  and the twins `proj` (this tree), `proj_mut` (a throwaway for mutated hooks)

## 11. Rework of round 7 (F1–F5)

Rig: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0083\rework7\`. Two office projects built with
`scaffold.py` from a copy of the tree — `proj_before` (the state the verifier judged) and
`proj_after` (this delivery). Every rc below is the FULL PreToolUse chain of the project's own
`settings.json` (`run.py`, the verifier's driver, reused), under both `Bash` and `PowerShell`,
unless a line says otherwise.

### F1 — the bound in §10 was a spelling (document fix)

Corrected in place, in the bullet it stood in. What replaced it is measured above: the creation of
a decoy `ledger_add.py` is refused exactly where the line SPELLS the name, and the two-step chain
runs to a poisoned `git HEAD` on the delivered state. No code changed for this finding.

### F2 — the docstring promised a refusal that does not fall (document fix + test)

`gate_ledger_valid._stages_beside_the_vouched_runs` said "a neighbour that writes or runs it is
refused". Measured, `rework7\m_f2.py`, identical at `proj_before` and `proj_after`:

```
python scripts/ledger_add.py --help | tee tools/ledger_add.py                    rc 2
python scripts/ledger_add.py --help | tee tools/ledger_add.py && git commit -m x rc 2
python scripts/ledger_add.py --help | python tools/ledger_add.py                 rc 0   <-- claimed 2
python scripts/ledger_add.py --help | python tools/ledger_add.py && git commit -m x  rc 2
python scripts/ledger_add.py --help | cat tools/ledger_add.py && git commit -m x rc 0
python scripts/ledger_add.py --validate ledger/2026.csv | cat tools/ledger_add.py && git commit -m x  rc 2
```

The paragraph now separates the two: WRITING the decoy is refused unconditionally
(`_writes_protected` is asked of every shell line), RUNNING it only with a blocked operation in the
same line (the decoy check lives in `_a_reading_writes_the_ledger`, which `handle_pre_tool_use`
asks under `blocked_op`). The claim is a test rather than prose:
`test_a_decoy_run_beside_a_vouched_run_is_refused_only_with_a_blocked_op`, nine lines, three rows
whose answers differ.

### F3 — a carriage return is a statement separator for one of the two gated shells (CLOSED)

Measured on the shells themselves (`rework7\m_shells.py`):

```
echo one<CR>echo two    bash rc 0 -> "oneecho two"   ONE command
echo one<CR>echo two    powershell rc 0 -> two lines  TWO statements
```

`_SEGMENT_SPLIT_RX` knew `\n` and not `\r`, so the write behind the CR was argument text of the
vouched run in front of it. Chain at `proj_before`, one gated PowerShell call, git witness
(`rework7\m_chain.py`):

```
python scripts/ledger_add.py --validate ledger/2026.csv<CR>Set-Content -Path ledger/2026.csv
 -Value 'id,doc_date,x'<CR>git commit -am poisoned
  proj_before  gate rc 0 -> powershell rc 0 -> git HEAD:ledger/2026.csv == "id,doc_date,x"
  proj_after   gate rc 2 (gate_ledger_valid.py)
```

**Closed**, and not with the one-character fix. `_normalise_pipeline` rewrites `\r\n?` into `\n`
AFTER the continuation join, so the CR becomes the line break it is and every rule that already
knows a line break keeps working. Why not `\r` in `_SEGMENT_SPLIT_RX`: that cuts between a verb and
the flag that makes it a write — measured, `find ledger<CR> -delete && git commit -m x` goes rc 2 →
rc 0 with the separator-class spelling (mutation `F3-M2`). Why after the join: each gated shell
continues a line over its OWN continuation character followed by a CRLF (measured, `m_shells.py`:
bash over `\`, PowerShell over the backtick — the pair `_compat._CONTINUATION_RX` reads), so a
token joined back together must not then be split by the newline that join leaves.

`rework7\m_f3.py`, twelve lines × two tool names, `proj_before` → `proj_after`:

```
chain, vouched run CR Set-Content CR commit             0 -> 2
chain, vouched run CR tee CR commit                     0 -> 2
chain, vouched run CR write to the judge CR commit      0 -> 2
CRLF spelling of the same                               2 -> 2
sed -i s/a/b/ <CR> ledger/2026.csv && git commit        2 -> 2
find ledger<CR> -delete && git commit                   2 -> 2
cat ledger/2026.csv<CR>| tee ledger/2026.csv && commit  2 -> 2
git status<CR><LF>git diff && git commit                0 -> 0   (false-alarm end)
vouched run alone, CRLF formatted                       0 -> 0   (false-alarm end)
```

**The price, measured, not argued:** the segment split is deliberately quote-blind (`BUG-0065`), so
a CR inside a quoted argument now cuts there too. `python scripts/ledger_add.py --summary
'reversed<CR>see scripts/ledger_add.py' && git commit -m x` is 0 → 2. That is the same
over-refusal the quoted `;` already had (`--summary "reversed; see scripts/ledger_add.py"` is rc 2
before and after), it is fail-closed, and it needs a carriage return INSIDE an argument that also
names a protected path.

**Side effect, taken the way the verifier asked:** the anchor's opening class is no longer `[\s(]*`
but `_STAGE_OPENING = r"(?:[^\S\r\n]|\()*"` — whitespace that is not a line break, or a group
opening. A line break cannot reach that position (the cut removes it), so accepting one was an
answer about an unreachable input, and the property test was pinning it. The test's expectation is
now measured against the gate's own cut (`_may_open_a_vouched_stage`) instead of asserting
`char.isspace()`.

### F4 — the tripwire hung on the NAME (test fix)

`test_every_vouching_run_pattern_is_named_here` compared `dir(gate)`'s `*_RUN_RX` names. It now
reads the patterns the exemption's own code consults, off the parsed source and transitively
through the helpers it calls (`_patterns_consulted_by`), and compares that against the vouching
list plus the one refusing helper the same code reads (`_ANY_VALIDATOR_PATH_RX`). Measured both
ways (mutations below): a fourth exemption CONSULTED by `_stages_beside_the_vouched_runs` under the
name `_EXTRA_VOUCH` is now red; the same pattern merely DEFINED and never consulted stays green,
which is what the docstring says — a pattern nobody reads frees no stage.

### F5 — the quantifier had no case (test added)

`test_stage_openings_stack_in_front_of_a_vouched_run`: every PAIR of stage openings, over the
opening set the character test measures, in front of each of the three vouched runs. With
`(?:…)?` in place of `(?:…)*` it is red on `((` — and every failure of that mutation is a case of
this one test (`F5-M` below, 3 failed), so before it existed the quantifier was unmeasured.

### Red seen — clone OUTSIDE the repo (`rework7\redrepo`, built by `mut.py`, run by `m_red.py`)

Selection: the eight test names this rework touches. Base on the delivered tree: `350 passed,
1705 deselected`.

```
F3-M1  the CR normalisation removed                12 failed
         6 x test_a_carriage_return_ends_a_stage_the_way_powershell_ends_a_statement
         3 x test_only_a_group_opening_stands_in_front_of_a_vouched_run  (\r reaches a stage again)
         3 x test_stage_openings_stack_in_front_of_a_vouched_run
F3-M2  \r in _SEGMENT_SPLIT_RX instead              1 failed
         test_a_carriage_return_does_not_tear_a_command_off_its_own_flag
F3-M3  _STAGE_OPENING back to r"[\s(]*"             6 failed
         test_only_a_group_opening_stands_in_front_of_a_vouched_run (\r and \n, three patterns)
F5-M   _STAGE_OPENING quantifier * -> ?             3 failed
         test_stage_openings_stack_in_front_of_a_vouched_run
F4-M   fourth vouch, consulted, not *_RUN_RX        1 failed
         test_every_vouching_run_pattern_is_named_here
F4-M2  the same pattern, never consulted            0 failed  (deliberate: it frees nothing)
```

### NOT closed, named: the SAME carriage return defeats `gate_write_scope` outright

Found while measuring F3, in a file this round does not touch. `gate_write_scope` rewrites a
newline into `; ` before it tokenises (`gate_write_scope.py:1298`,
`_compat.join_line_continuations(code_view).replace("\n", " ; ")`) and its own comment says why a
newline must not be a token. A bare CR is not rewritten, and `shlex` treats it as ordinary
whitespace — so the line becomes ONE pipeline whose verb is the harmless first one. Measured,
`rework7\m_scope_probe.py`, full registered chain, both tool names, `proj_before` and `proj_after`
identical:

```
tee .claude/settings.json                                          rc 2
echo hello; tee .claude/settings.json                              rc 2
echo hello && tee .claude/settings.json                            rc 2
echo hello<LF>tee .claude/settings.json                            rc 2
echo hello<CR><LF>tee .claude/settings.json                        rc 2
echo hello<CR>tee .claude/settings.json                            rc 0   <--
Get-Content README.md<CR>Set-Content -Path .claude/settings.json …  rc 0   <--
```

One gated PowerShell call, file witness (`rework7\m_cr_scope_chain.py`, real powershell.exe,
`proj_after`):

```
Get-Content README.md<CR>Set-Content -Path .claude/settings.json -Value 'POISONED …'
  gate rc 0 -> powershell rc 0 -> .claude/settings.json == "POISONED BY A CARRIAGE RETURN"
```

That is the file the provider reads to learn WHICH hooks run. The chain runs in one call and one
session, so by CLAUDE.md it blocks the package — it is named here, not closed, and the reason is
the blast radius, not the difficulty: `gate_write_scope.py` is mirrored across all three kits, so
the fix restamps all three and its verification is the full suite, which DEC-0050 makes the lead's
run at delivery. The candidate is the exact analogue of F3 — rewrite `\r\n?` into `\n` before that
`.replace`, one line — and it is deliberately NOT applied here.

`gate_commit_evidence` was not measured the same way: it is not in the office kit's registration
at all — read out of the scaffolded project's own `settings.json`, its `Bash|PowerShell` chain is
`guard_fs_tripwire`, `gate_ledger_valid`, `gate_write_scope`, `gate_push_token`,
`gate_shell_hygiene` and `gate_filing`. Whether the repo's own `.claude/` gates read a CR is
outside this item's scope (forbidden area) and was not measured.

### Rework scratch (`…\_round-scratch\TSK-0083\rework7\`)

- `scaffold.py`, `run.py`, `reset.py` — the verifier's drivers, reused unchanged
- `m_shells.py` — what bash and powershell do with a CR, a CRLF and each continuation
- `m_f1.py` — the decoy-creation spellings; `m_f1chain.py` — the two-step chain with a git witness
- `m_f2.py` — the neighbour × decoy matrix; `m_f3.py` — the CR battery incl. its counter-ends
- `m_chain.py` — one line, gate then real shell, git witness; `m_bs.py` — the `\`+CRLF question
- `mut.py` + `m_red.py` — the mutation clone and the red runs above

---

## Nachtrag 2026-08-24 — der hier benannte, nicht geschlossene CR-Rest ist geschlossen

Der Abschnitt oben nennt eine Lücke, die dieses Item nicht geschlossen hat: `gate_write_scope`
schreibt vor dem Tokenisieren nur den Zeilenumbruch in einen Trenner um, also bleibt ein blankes CR
für `shlex` gewöhnlicher Leerraum, während PowerShell dort eine Anweisung beendet. Das ist
`BUG-0066` geworden und in `TSK-0084` geschlossen — samt zweier Nachbarn, die dabei gemessen
wurden. Kurz, damit dieses Protokoll nicht als offener Stand gelesen wird:

- **Der genannte Kandidat wurde nicht so gebaut, wie er hier stand.** Statt der einen Zeile in
  `gate_write_scope` sitzt die Umschreibung in der geteilten Vorbereitung
  (`_compat.join_line_continuations`), damit **kein** Aufrufer den Join ohne sie bekommen kann.
  Welche Zeichen ein Anweisungstrenner sind, ist gegen echte Shell-Prozesse gemessen (genau LF für
  beide, CR nur für PowerShell) statt aufgezählt.
- **Der hier vermutete Grund für das Nichtschließen — „der volle Suitenlauf gehört dem Lead" —
  trug nicht.** Nach `DEC-0050` reichen die betroffenen Suiten; die Runde hat sie gefahren
  (2930 grün) und den vollen Lauf dem Lead gelassen.
- **`gate_ledger_valid` hat seine eigene Kopie der Regel abgegeben.** Der F3-Fix dieses Items
  (`_CARRIAGE_RETURN_RX` in diesem Gate) ist entfernt; die Regel steht jetzt an einem Ort, und ein
  Test verbietet jedem Aufrufer der Vorbereitung eine zweite kompilierte Kopie.
- **Zwei Nachbarn, die dieses Item nicht sah, sind mitgeschlossen:** ein blankes CR verschweißt
  unter der Bash-Schiene zwei Wörter zu einem Pfad (die Zeile wird jetzt verweigert), und die
  Fortsetzungsregel war die Vereinigung beider Shell-Escapes (jetzt werkzeugabhängig).

Messungen, Rot-Beweise und die benannten Reste: `project_memory/staging/TSK-0084/acceptance.md`.
Die Messvorrichtung dieses Items (`…\_round-scratch\TSK-0083\rework7\`) wurde dort
weiterverwendet.

### Nachtrag 2, 2026-08-24 — der Stolperdraht dieses Items steht jetzt auf zwei Lesern

Der Draht `test_every_vouching_run_pattern_is_named_here`, den dieses Item eingeführt hat, hat in
zwei Prüfrunden dreimal eine Vollständigkeit behauptet, die er nicht baute — jedes Mal, weil die
Antwort eine **Aufzählung von Schreibweisen** war. Reihenfolge der Widerlegungen: ein viertes Muster
unter beliebigem Namen; dann ein Muster in einem Container bzw. hinter einem Lambda; dann die
**Kreuzung** beider, ein Container von Prädikats-Funktionen.

Der Draht fragt jetzt zwei Fragen und nimmt die Vereinigung: `_patterns_consulted_by` folgt Namen
durch den geparsten Quelltext (alle Pfade, nur auflösbare Namen), `_patterns_called_by`
instrumentiert jedes modulweite `re.Pattern` und schreibt mit, welche beim Laufen wirklich gefragt
werden (alle Namen, nur die gelaufenen Pfade). Gemessen im Klon mit echtem pytest: alle fünf
Muster-Konstruktionen rot, „definiert aber nie gelesen" korrekt grün. Der eine benannte Rest ist
gemessen: eine Ausnahme, die gar kein Muster befragt.

Einzelheiten und Zahlen: `project_memory/staging/TSK-0084/acceptance.md`, Abschnitt „Durchgang 4".
