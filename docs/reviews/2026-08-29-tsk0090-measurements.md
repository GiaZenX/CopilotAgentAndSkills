# TSK-0090 — what a run of `.claude/hooks/test_gates.py` costs, and what the cut bought

Round of 2026-08-29, item TSK-0090, derived from FR-0011. Everything here was taken on the user's
host (16 logical cores, Windows 11, Git for Windows `bash`, Python 3.13.0) with the command the
constitution prints:

    python -B -m pytest .claude/hooks/test_gates.py -q

## 0. The load condition of every number below

The host was **not** quiet for this round. The user stated mid-round that at least one parallel
Claude session was working in another repo, plus a radar-watcher run earlier in the night. Process
creation is exactly what this suite is bound by (section 4), so every absolute wall number here
carries its window:

* **window A** — the first two hours of the round. No deliberate neighbour from this round; whether
  the parallel session was already running is not known.
* **window B** — from the first A/B onwards. The parallel session was named by the user; this
  round's own benchmarks were also running back to back.

Between the two windows the same benchmark script measured 3.6× fewer shell lines per second
(section 4). **Absolute before/after wall times taken in different windows are therefore not a
comparison.** What is load-robust is an **alternating** A/B in one window, and that is what
section 5 and section 6 are.

The quiet-window re-run this round could not take is named in section 7 as a single command.

## 1. The premise, and what it is worth today

FR-0011 and TSK-0090 state a factor-11 rise: 358 s for 134 tests on 2026-08-07 against 4101.94 s
for 143 tests on 2026-08-13. BUG-0033 carries the provenance of the second number — it is the run
that failed twice **"under the verifier's parallel load"** — and beside it a third: a *clean idle*
full run of the same tree at **4512.42 s**.

Measured this round, window A, the same command on the same host: **511.66 s, 243 passed**.

The rise is not in the suite's code. Every heavy path is byte-identical to the version that
measured 4101.94 s:

| compared | 2026-08-08 `b32ec98` | 2026-08-13 `e92511d` | working tree today |
|---|---|---|---|
| `test_gate1_places_a_tilde_word_where_the_shell_puts_it` | same | same | (this round's change) |
| `test_gate1_refuses_a_line_exactly_where_the_shell_would_write` | same | same | (this round's change) |
| `test_the_shell_writes_where_the_table_of_line_shapes_says` | same | same | (this round's change) |
| `_in_parallel`, `_changes_the_protected_file`, `run`, `_registrations`, `_refused_for_the_deadline` | same | same | (this round's change) |
| `_quotings`, `_tilde_subjects`, `_crossed` (the check-set sizes) | same | same | unchanged |

Compared by parsing both files and stripping docstrings, so a reworded comment does not count as a
change. What DID change after 2026-08-13 is `_can_arbitrate` and the session guard (`54c0807`,
BUG-0051) — neither of which touches the count or the shape of the processes the heavy tests start.

So the check sets are the same size they were: 1449 line shapes, 7527 tilde subjects, 160 lead
subjects, 157 tilde prefixes.

What I can show instead is that this host's process throughput swings by more than a factor of
three inside one day (section 4), and that the 4101.94 s run is documented as having been taken
under a parallel load. **The 4512.42 s "idle" run I cannot explain**; nothing I could measure
reproduces it, and nothing in the code accounts for it. That is stated as an open end, not as a
solved one.

## 2. The profile before the cut (window A)

Full run, `--durations=0`: **511.66 s**, 243 tests. The per-test durations sum to 509.95 s, so
collection and import are 1.7 s — everything is in the tests.

| s (call+setup) | share | test |
|---|---|---|
| 118.42 | 23.2 % | `test_gate1_places_a_tilde_word_where_the_shell_puts_it` |
| 96.26 | 18.9 % | `test_gate1_refuses_a_line_exactly_where_the_shell_would_write` |
| 32.52 | 6.4 % | `test_gate1_answers_before_its_registration_gives_up` (21.03 s of it the `unreachable_cost` fixture) |
| 28.59 | 5.6 % | `test_the_shell_writes_where_the_table_of_line_shapes_says` |
| 19.88 | 3.9 % | `test_every_subcommand_the_gate_calls_an_author_authors_one` (15 cases) |
| 16.33 | 3.2 % | `test_a_gate_whose_shared_body_is_gone_still_refuses` (11 cases) |
| 16.20 | 3.2 % | `test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_that_names_another_tree` |
| 14.09 | 2.8 % | `test_gate1_answers_for_a_tilde_that_does_not_start_its_word` |
| 9.41 | 1.8 % | `test_gate1_refuses_a_protected_path_however_the_filesystem_spells_it` (3 cases) |

46 of the 102 test FUNCTIONS cost less than 0.5 s including their fixtures, 6.64 s together --
counted per function, with every parametrised case of a function added up. Per CASE the same file
cannot answer: `--durations=0 --durations-min=0` reported 193 of the 243 node ids, so the 50 that
are missing are missing from any per-case count. Of the 193 that are there, 116 cost under 0.5 s,
27.71 s together. (An earlier draft carried the per-function figures under the word "cases".)

**Process counts**, taken by wrapping `subprocess.Popen` for one full run (counting only; the call
is passed through unchanged):

| program | started in one run |
|---|---|
| `bash` | 9082 |
| `python` (gate processes and kernel calls) | 2090 |
| `git` | 604 |
| `cmd`, `icacls` | 7 |
| **total** | **11 783** |

Attributed to the tests that start them:

| bash | python | git | test |
|---|---|---|---|
| 7530 | 139 | 0 | `test_gate1_places_a_tilde_word_where_the_shell_puts_it` |
| 0 | 1449 | 0 | `test_gate1_refuses_a_line_exactly_where_the_shell_would_write` |
| 1209 | 0 | 0 | `test_the_shell_writes_where_the_table_of_line_shapes_says` |
| 164 | 161 | 0 | `test_gate1_answers_for_a_tilde_that_does_not_start_its_word` |
| 160 | 0 | 0 | `test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads` |
| 0 | 0 | 204 | `test_every_subcommand_the_gate_calls_an_author_authors_one` |
| 0 | 0 | 201 | `test_the_commands_the_gate_leaves_open_author_nothing` |

Fixture costs, window A: `build_project` **1.97 s**, one `shutil.copytree` of the finished stand-in
**1.22 s**. The suite makes about thirty such copies; eleven of them are the eleven cases of
`test_a_gate_whose_shared_body_is_gone_still_refuses` (`len(REGISTERED_PAIRS) == 11`, derived from
`.claude/settings.json`), which differ in nothing but the gate and the payload.

That they can share one copy is not stated anywhere any more, it is CHECKED: the fixture
`without_the_shared_body` takes a picture of every file in the copy before the pairs run and again
in its finalizer, and a file that moved fails it. Red seen rather than claimed -- with a write
planted where a gate process makes it (`project_memory/.audit/hook_events.jsonl`, the very file the
kernel appends to when a gate refuses), the eleven cases stay **11 passed** and the run is
**1 error**, which is the whole point: nothing else in the file can see it.

## 3. Where the ceiling is

The executor was already there (`AT_ONCE = 10`) and the naive widening does not pay. Window A, same
work at rising widths:

| work | width 1 | 4 | 10 | 16 | 24 | 32 |
|---|---|---|---|---|---|---|
| gate process (`run`, one payload) | 4.7/s | 13.0/s | **15.8/s** | 15.3/s | 13.9/s | 14.4/s |
| shell line (`_changes_the_protected_file`) | 21.2/s | 45.9/s | 57.2/s | **63.5/s** | 64.6/s | 62.0/s |
| `bash -c :` (nothing but the start) | 32.9/s | 61.2/s | 69.6/s | **79.3/s** | 79.3/s | 78.2/s |

The third kind, the git scenario repositories, was **not** scanned. Its width is the gate width,
and the only thing measured about it is what pooling the scenarios bought at that width (section 5);
whether 10 is where it saturates is unknown and is not claimed anywhere.

Two things follow and both were measured, not assumed:

* the gate pool is already at its saturation point at 10 and **loses** time past it;
* the shell pool gains 11 % from 10 to 16 and nothing after that.

It is not the driver. The same shell line with the environment precomputed and the module lookup
taken out runs at the same rate (48.1/s vs 48.0/s vs 45.3/s for spawn-only, width 16, window B), so
the Python side of the loop is not what is waiting. And moving the fan-out **into** a shell — one
`bash` starting the children with `&` — is 19.3/s against 45–48/s from this process, so that door is
closed by measurement.

## 4. Two kinds, two widths — and how far the host itself moves

`AT_ONCE` is now a number per kind, and these are the rates it was chosen from (section 3 for
window A). The same script, run again in window B:

| measure | window A | window B | factor |
|---|---|---|---|
| shell line, width 1 | 21.2/s | 9.6/s | 2.2 |
| shell line, width 16 | 63.5/s | 17.7/s | **3.6** |
| `bash -c :`, width 16 | 79.3/s | 33.6/s | 2.4 |
| gate process, width 1 | 4.7/s | 3.7/s | 1.3 |
| gate process, width 10 | 15.8/s | 11.0/s | 1.4 |
| `build_project` | 1.97 s | 2.55 s | 1.3 |

This is the quantity FR-0011's factor-11 has to be read against, and it is also why the widths were
not re-tuned in window B: a saturation point measured on a host that is 3.6× slower than it was two
hours earlier is not a property of the suite.

## 5. The cut, and the A/B that decides it

The cut is: **the kinds of process run at the same time.** Batches of one kind share that kind's
pool and its slots; the kinds run beside each other (`_all_at_once`). The cell measurements of the
four heaviest tests are taken in one such run (`cells`), the four git scenario tables in another
(`authored`), and each test still asserts its own property against its own subjects.

A/B over the real work — 2509 tilde subjects through a real shell plus 483 line shapes through a
real gate process, the stand-in project where `outside_the_home_directory` puts it and the
sandboxes where `tmp_path` puts them. Three configurations, **interleaved** over three rounds so
that a drifting host cannot decide the comparison. Window B:

| configuration | round 0 | round 1 | round 2 | median |
|---|---|---|---|---|
| one after the other, shell 10 / gate 10 (the shape before) | 192.41 s | 189.96 s | 172.59 s | **189.96 s** |
| together, shell 16 / gate 10 (the shape now) | 116.95 s | 138.02 s | 146.41 s | **138.02 s** |
| together, shell 10 / gate 10 | 124.21 s | 134.98 s | 154.68 s | 134.98 s |

Running the kinds together is **27 % off the median** and wins in every one of the three rounds.
The width is inside the noise of this window, which is the honest reading: the gain is the
overlap, not the number.

An earlier run of the same A/B with both trees in the round's scratch directory gave 96.03 s
against 78.93 s (18 %) at a much lower absolute rate — the directory the sandboxes stand in changes
the rate by more than the configuration does, which is why the second run put them where the suite
puts them.

Measured beside it, same window: 150 gate processes and 600 shell lines run **alone** cost
10.15 s + 10.31 s = 20.47 s; run **together** the wall is 15.01 s (gates 14.8/s → 10.0/s, shell
lines 58.2/s → 41.5/s). The kinds do compete — they just do not compete for all of it.

What the shared copies bought, window B: the eleven cases of
`test_a_gate_whose_shared_body_is_gone_still_refuses` cost 3.99 s of fixture and eleven gate runs
instead of eleven copies of the stand-in (16.33 s in window A). The four git scenario tables cost
16.53 s in one pooled fixture, against **35.43 s** over their forty cases in window A (19.88 +
6.79 + 3.73 + 5.03, recomputed from `before_durations.txt`) -- a saving of 53 %, not the 63 % an
earlier draft got from a wrong sum of 44.3 s.

And what a run that selects ONE of the four cell tests pays, measured in both trees in one window,
twice, `-k does_not_start_its_word`:

| round | before | after |
|---|---|---|
| 1 (cold) | 80 s | 60 s |
| 2 | 34 s | 28 s |

That is what `CELL_COLUMNS` is for, and the other end of it was measured too. In a copy of the repo
outside it, the column selection was taken out again -- the fixture's list comprehension left to
run every batch -- and the same `-k` was timed three times in a row, with the selection, without
it, with it again:

| | wall |
|---|---|
| with the selection | 23.37 s |
| **without the selection** | **789.09 s** |
| with the selection | 25.34 s |

A factor of 33. Without that filter the phase would have made every `-k` naming one of these four
tests a full-table run, which is the opposite of what this round is for.

## 6. The deadline measurements, and why they were left alone

The timing tests keep the shape they had: they run in pytest's own order, one after the other, with
no batch of this suite beside them — the cell phase and the scenario phase are session fixtures and
are finished before the first of them starts.

That is a property of the INVOCATION FORM the constitution prints, one pytest process, and inside
it it is structural rather than lucky: `_all_at_once` joins every thread it starts and every pool
is closed by its `with`, so the thread count is back where it began before the fixture returns
(measured by the verifier: threads before 1, after 1). What it does NOT cover is a second runner.
`pytest -n` would put the phase of one worker beside the deadline test of another — `xdist` is
importable on this host — and so would a second concurrent run of the suite by hand. Nothing here
protects against either, and this round did not build any: the table below is what such a
neighbour costs, and a run of this suite is a heavier neighbour after this round than before it
(peak child processes 10 → 26 at equal totals).

That is not a preference. Both columns below are the quantities the assertions in
`test_gate1_answers_before_its_registration_gives_up` compare, read through the suite's own helpers,
12 iterations each, window B:

| | no batch beside it | this suite's cell batch beside it |
|---|---|---|
| margin to the registration, worst | **1.20 s** | **0.19 s** |
| margin to the registration, best | 1.37 s | 1.28 s |
| every run refused *for the deadline* | yes (12/12) | yes (12/12) |
| bare process start, worst | 0.55 s | 1.10 s |
| this host's own timing noise, worst | 0.32 s | 0.83 s |
| widest band minus that noise, worst | **+0.23 s** | **−0.38 s** |
| runs where the band was under the noise | **0 of 12** | **4 of 12** |

The last row is the assertion `margin > noise`. Under the cell batch it fails in a third of the
runs — which is BUG-0033's failure mode exactly, produced on demand. So overlapping the timing
tests with the cell phase would not have cost accuracy in the abstract: it would have turned a
third of the runs red for the machine's mood. Both halves of that stay measured and stay named: the
first column is what ships, the second is why nothing was moved next to it.

Note what the second column also shows: the refusal itself never failed. Under load the gate still
answered *for its deadline* in 12 of 12 runs; what the load eats is the room the test needs to
**prove** the floor.

**The suite still catches what it exists to catch.** In a copy of the repo outside it, the bound
beside the decision was disabled (`_harness._the_budget_is_spent`, the `left <= -_WATCH_STEP`
branch made unreachable). Unmutated the five deadline tests are green in 50.01 s; mutated, two of
them fail — `test_gate1_answers_before_its_registration_however_long_the_line_takes_to_read` and
`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`, the latter with
"the gate answered after 10.80s while its registration gives it 3.50s".

## 7. Full-suite before and after, and the run that is still owed

In the repo itself, the runs that exist:

| run | window | wall | result |
|---|---|---|---|
| before the cut | A | **511.66 s** | 243 passed |
| before the cut, with `Popen` counted | A | 598.79 s | 243 passed |
| after the cut | B | **1116.36 s** | 245 passed |

**These are not a comparison** and are not offered as one: section 4 shows the host moved by 3.6x
between the windows, and the cell phase alone took 746.78 s in the second run against 257.36 s for
the same four tests in the first. (The two tests more are this round's own,
`test_the_run_that_measures_the_cells_holds_a_slot_answers_every_subject_and_raises` and
`test_every_column_of_the_cell_phase_is_owned_by_a_test_that_asks_for_it`.)

The load-robust before/after is the same command run **alternately** in two copies of this repo
outside it, one carrying `HEAD`'s `test_gates.py` and one carrying this round's, everything else
byte-identical. Window B; the second `after` ran on its own a few minutes behind its `before`,
because the driver was stopped mid-round:

| round | before | after | difference |
|---|---|---|---|
| 0 | 1076.85 s (243 passed) | 941.47 s (245 passed) | **-12.6 %** |
| 1 | 1266.87 s (243 passed) | 1186.54 s (245 passed) | **-6.3 %** |
| both | 2343.72 s | 2128.01 s | **-9.2 %** |

The wall time falls, in both rounds, on a loaded host -- and by less than the 27 % the phase itself
gains (section 5), which is what the arithmetic says it should be: the phase is about half the run,
and under load the two kinds compete for more of the same bottleneck.

What is owed is a quiet-window run, and it is two commands:

    python tools/gate_suite_rates.py
    python -B -m pytest .claude/hooks/test_gates.py -q --durations=0 --durations-min=0

The first is what makes the second comparable rather than merely new, and it is a tool in this repo
rather than a script in a scratch directory that gets cleaned up. Measured here: **66 s** for the
three rates at the widths the suite uses, and **427 s** for `--scan`, which is section 3's whole
table. Report the rates beside the wall time. A run whose shell-line rate at width 16 is near 63/s
is in window A's condition; one near 10/s is in the condition the rework of this round was measured
in.

The same quiet window is what the margins of section 6 want, and they have a tool too:
`python tools/gate_suite_margins.py 12` reproduces that table's first column,
`python tools/gate_suite_margins.py 12 --neighbours` its second.

## 8. Delivery checks

Window B, on the working tree as it ships:

* `python -m ruff check .` -- clean.
* `python tools/bump_kit_version.py` -- `dev-team`, `office-team`, `research-team` all *unchanged*;
  this round touches no kit content.
* `python tools/validate.py` -- `all structural checks passed`.
* `python -B -m pytest .claude/hooks/test_gates.py -q` -- **245 passed** in 1116.36 s.
* `python -m pytest tools/ -q` -- **3890 passed, 14 skipped** in 2153.07 s.

## 9. What this round did not close, and says so

* **The 4512.42 s idle run of 2026-08-13 stays unexplained** (section 1). The code is identical, the
  host moves by 3.6x, and neither of those adds up to a factor of nine on an idle machine.
* **The check sets were not cut.** 1449 line shapes, 7527 tilde subjects and 160 lead subjects are
  what they were; their size is pinned by entries of `docs/POST_V2_WISHLIST.md`, which is outside
  this item's scope. The floor of a run is therefore still about 9000 shell lines and 1600 gate
  processes.
* **The four git scenario tables have no column selection.** `authored` measures all forty
  scenarios whenever any one of its four tests is in the run: 16.53 s in window B, against 12.09 s
  for the single most expensive case (`filter-branch`) in window A. The cell phase has that
  selection (`CELL_COLUMNS`) because there the penalty was the whole phase; here the penalty is
  bounded by one pooled fixture and it was left open rather than given a second table to keep in
  step.
* **`docs/POST_V2_WISHLIST.md` H45 cited `test_gates.py:131-135`** -- CORRECTED, not by this round:
  one import line of it moved the block down by one, the file is outside this item's scope, so it
  was handed back and the lead has since written `test_gates.py:132-136` there with this round
  named beside it. The class stays open: a pointer that carries line numbers is a pointer nothing
  checks, and the next round that adds a line above that fixture will have to be told again.
* **The `unreachable_cost` fixture still costs a whole cold UNC lookup** (21.03 s of the deadline
  test's setup in window A). It could be prefetched beside the cell phase; it is not, for the reason
  in section 6 -- the deadline measurements get no neighbours.
* **Nothing here protects the deadline phase from a SECOND runner** (section 6). One pytest process
  cannot put a batch beside a timing test; `pytest -n` and a second concurrent run of the suite can,
  and after this round such a neighbour is heavier than it was (peak child processes 10 -> 26). No
  guard was built and none is claimed.
* **The width of the third kind is not scanned** (section 3). `AT_ONCE[REPOSITORIES]` is derived
  from the gate width so that it cannot drift away from the one measurement it stands on, but where
  those scenarios saturate is unknown.

The open remainders above are carried as **H74** in `docs/POST_V2_WISHLIST.md` (with the quiet-window
run as the accepted DEC-0053 residue); that entry and this document name each other so neither can
drift alone.
