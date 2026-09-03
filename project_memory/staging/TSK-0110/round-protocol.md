# TSK-0110 — stream J "hygiene" (FR-0036), second DEC-0057 generation

Worktree `C:\Offline Repos\v2-testbed\_worktrees\g2-hygiene` on branch `g2/hygiene` at `6d18407`
(release `2026.09.02-10`). Scratch `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0110\`.
No commit, no install, no kit file touched, no hole number written.

---

## 1. Wishlist pass, sections 1-10

Delivered as its own file: `project_memory/staging/TSK-0110/wishlist-pass.md`. **The verdict per
section is that file's summary table, and no count is repeated here** — the distribution is counted
off that table in section 9 below. `FR-0003` folds in — and it already
did, in the state: `archive/FR/2026/FR-0003.yaml` is `MERGED` with `resulting_item: FR-0036`.

The wishlist itself is untouched, as ordered — six other streams append to it.

---

## 2. Docs cleanup, measured

### 2.1 The wire definition that was applied, and how it differs from the order's

The order names four wires: a test that reads it, a hole entry, an EVD `artifact_ref`, a living
item. The measurement added a fifth and one closure rule, and both changed the outcome:

- **KIT — a shipped kit file names the path.** Found by measurement, not assumed:
  `team-kits/dev-team/skills/frontend-design/SKILL.md` cites
  `docs/research/2026-07-27-adoption-anthropic.md`, and `team-kits/dev-team/skills/webapp-testing/
  SKILL.md` cites `docs/research/2026-08-31-skill-survey.md`. Both skills were vendored in the FIRST
  stream generation (`DEC-0060`). A move would leave a shipped file pointing at nothing.
- **A test that reads a DIRECTORY wires everything under it.** No path search can see this one:
  `tools/test_repo_hygiene.py` holds `RESEARCH = os.path.join(ROOT, "docs", "research")`, and
  `test_every_research_role_report_is_named_after_the_role_its_own_text_is_about` walks that
  directory and asserts a floor of six role reports. This is exactly the house rule "a check must
  read the part that RUNS" turned against the measurement instrument itself.
- **Closure, one hop and then judgement:** a file named by a file that is itself kept for a wire
  reason stays. Not transitively — over prose, transitive closure makes every document reachable
  and the measurement meaningless. Where the chain was longer than one hop the file was LEFT and
  listed, never moved.

Net effect: the applied rule for moving is strictly stronger than the order's — **nothing in the
repo or in canonical state names the file, by path or by name**. Everything the order's bare
definition would have allowed to move but this round did not is listed in 2.3 with its reason.

### 2.2 The move set — one file

| from | to |
|---|---|
| `docs/pilot/2026-08-09-drehbuecher.md` | `docs/archive/2026/pilot/2026-08-09-drehbuecher.md` |

Zero references in the whole tree. Measured with a full-tree scan over `docs/`, `tools/`,
`.claude/hooks/`, `team-kits/`, `.github/`, `radar/`, `user/`, `CLAUDE.md`, `README.md`,
`NOTICES.md` and the MAIN repo's `project_memory/` (active and archive), by path and by file name.

Index written to `docs/archive/2026/README.md`, with the reason per move and — deliberately — the
list of what was measured and NOT moved, so the next round does not repeat the pass.

### 2.3 Measured, and deliberately NOT moved

| file(s) | why it stays |
|---|---|
| `docs/research/2026-07-27-*` (12 files) | TWO independent reasons. (a) `tools/test_repo_hygiene.py` reads the DIRECTORY `docs/research`; the role-report test's subject is what lives there. (b) The hole list, section 1, records that these files are `Belege` and that a `git mv` on them is **the user's decision** — this stream may not take it. |
| `docs/research/2026-08-16-model-downgrade-and-tier-pinning.md` | Zero references — the order's definition would move it. It stays because it lies UNDER `docs/research`, which the reader above wires as a whole. Moving it would mean overruling my own measurement instrument for one file. **This is the one file where the stream deliberately under-delivers, and it is the lead's call.** |
| `docs/research/2026-07-27-adoption-anthropic.md`, `docs/research/2026-08-31-skill-survey.md` | Cited by a SHIPPED kit skill (see 2.1). |
| `docs/handback/HANDBACK.md` + its two patches | A pending instruction to the USER. It names `BUG-0012` and `BUG-0014`; both are still `TRIAGED` in the store. Archiving it would remove a user's to-do. See finding F1 below for what is nevertheless wrong with it. |
| `docs/pilot/2026-08-09-pilot-1-vokabeltrainer.md`, `docs/pilot/2026-08-10-auswertung.md` | Cited by `docs/reviews/2026-08-13-tsk0055-assessment.yaml`, which is itself named by `docs/reviews/2026-08-13-tsk0055-closure-round.md`, which IS an EVD `artifact_ref`. Two hops — doubt, so they stay. |
| `docs/pilot/2026-08-14-drei-piloten-vergleich.md` | Named by `docs/pilot/2026-08-14-pilot-3-rechnungswerkzeug.md`, which is an EVD `artifact_ref` (EVD-0033, EVD-0034). One hop from a wire. |
| `docs/pilot/2026-09-01-research-pilot.md` | Named by `staging/TSK-0104/merge-protocol.md`, which is itself an EVD `artifact_ref` (EVD-0075). And one day old. |
| `docs/archive/staging-of-archived-items/**` (4 files) | Already in the archive. A second move inside the archive changes nothing and breaks the pointers archived items hold on them. |
| `docs/reviews/**`, `docs/POST_V2_WISHLIST.md`, `docs/HARNESS_V2_SPEC.md` | Forbidden scope. Findings about them are in section 5. |

---

## 3. The hint: a docs file nothing reads, older than N days, is REPORTED

Built in `tools/test_repo_hygiene.py`:
`test_docs_prose_nothing_reads_any_more_is_reported_not_failed`. Fail-open per `DEC-0056` — it
emits a `UserWarning`, it never fails a round. Its subject is derived (`_docs_candidates`,
`_wire_class`, `_wires_over`, `_joined_literals`), not listed.

### N = 60 days, and where the number comes from

Measured, not chosen. For every file under `docs/`, the date of its first commit and the date of the
first commit of any file that names it. Only the cases where the NAMING file was itself created
AFTER the document give a usable interval — for the other 35 the pointer's date is not derivable
this way, and the protocol says so rather than counting them.

Three such cases exist, and their intervals are **1, 2 and 33 days**:

| document | born | first wired by | interval |
|---|---|---|---|
| `docs/pilot/2026-08-14-pilot-3-rechnungswerkzeug.md` | 2026-08-14 | `team-kits/kernel/presets.py` | 1 day |
| `docs/research/2026-08-31-skill-survey.md` | 2026-08-31 | `team-kits/dev-team/skills/webapp-testing/SKILL.md` | 2 days |
| `docs/research/2026-07-27-adoption-anthropic.md` | 2026-07-31 | `team-kits/dev-team/skills/frontend-design/SKILL.md` | **33 days** |

The 33-day case is the one that decides N: that report lay unreferenced for a month and then became
the source a SHIPPED skill cites. A grace period at or below 33 days would have named it as clutter
in mid-August. 60 gives a margin of roughly 1.8x over the single long case and is also longer than
the age of everything currently unwired, so the hint is silent today by measurement rather than by
luck. The number lives in exactly one place — `_DOCS_GRACE_DAYS` — and the comment beside it points
at `FR-0036` instead of repeating this table.

**Silent today, measured** (the class counts in this paragraph are the reader as it stood at
11:55; §8 re-measures them after the corpus was widened, and the two unwired files are the same
ones): with the hint's own reader, 100 candidates under `docs/` (excluding
`docs/archive/`), 98 wired, 2 unwired — `docs/handback/HANDBACK.md` (20 days) and
`docs/reviews/2026-07-24-harness-v2-review.md` (39 days). Both are under the grace period, so the
warning does not fire. Wire classes found on the running tree: PROSE 65, ITEM 59, TEST 29, HOLE 20,
KIT 13.

---

## 4. The red tests — measured, not claimed

Mutation harness: a copy of `tools/test_repo_hygiene.py` in
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0110\mutation\`, **outside both repos**. The two
probe tests use a corpus they write themselves, so they run against a bare tree. Full log:
`_round-scratch\TSK-0110\mutations.txt`.

| mutation (the defect restored) | result |
|---|---|
| M1 directory wires dropped from the reader | RED |
| M2 archived items count as readers again | RED |
| M3 grace period ignored | RED |
| M4 the hint speaks with an empty list | RED |
| M5 prose reclassified as the hole list | RED |
| M6 decisions stop counting as readers (**order item 4**) | RED |
| M7 the name reader is emptied | RED |
| M8 left name boundary dropped (a suffix counts as a pointer) | RED |
| M9 right name boundary dropped (a prefix counts as a pointer) | RED |
| M10 a document counts as a reader of itself | RED |
| M11 the literal run does not stop at a variable | RED |
| RESTORED | GREEN |

The tests that go red: `test_the_docs_wire_reader_answers_both_ways` (M1, M2, M5, M6, M7, M8, M9,
M10), `test_the_docs_hint_fires_only_past_the_grace_period` (M3, M4),
`test_the_directory_reader_takes_the_literal_run_and_stops_at_the_first_hole` (M11).

`test_the_running_tree_shows_every_wire_kind_this_reader_claims_to_see` was measured separately, in
process against the real tree with `_wire_class` blinded: blind to `team-kits/` → RED ("no file
under docs/ is reached by a KIT pointer any more"), blind to the hole list → RED, unmutated → PASS.

### Order item 4, answered directly

"A DEC's `source:` pointing at docs prose is a wire — measure it." Measured on the store:
`decisions/active/DEC-0042.yaml` (`source: docs/POST_V2_WISHLIST.md ...`) and
`decisions/active/DEC-0046.yaml` (`source: TSK-0069 / docs/reviews/2026-08-16-tsk0069-ii12-side-
check.md ...`). Built into `_wire_class` as class ITEM, with `project_memory/**/archive/**`
deliberately excluded — an archived item RECORDS a decision, it does not read the file, and without
that exclusion nothing under `docs/` could ever be archivable. Both halves are load-bearing: M6 and
M2 above.

---

## 5. What was found and NOT closed — named, with the measurement

**F1 — the handback's patches no longer apply.** `docs/handback/HANDBACK.md` tells the user to run
`git apply -p1 docs\handback\gate-fixes.patch` and `...\ci-gate-suite.patch` from a shell outside
Claude Code. Measured in the worktree: `git apply --check -p1 --ignore-whitespace` returns rc 1 for
both — `gate-fixes.patch` fails against `.claude/hooks/_harness.py:1983`,
`gate_commit_evidence.py:98` and `test_gates.py:2988`; `ci-gate-suite.patch` fails against
`.github/workflows/ci.yml:26`. `BUG-0012` and `BUG-0014` are both still `TRIAGED`. A probe of the
BUG-0012 shape (a shell function definition carrying a `PYTHONPATH=` assignment) came back rc 0,
i.e. the symptom does not reproduce in that form any more — but that probe is WEAKER than the item's
repro, whose function body writes canonical state and is refused today on the body's own merits, so
the original repro cannot be re-run cleanly. **Not claimed: that BUG-0012 is fixed.** What is
claimed: the user cannot follow this handback as written. The remedy touches `.claude/` and the item
store, both outside this stream. Left for the lead.

**F2 — a number in the hole list has rotted.** Section 1 of `docs/POST_V2_WISHLIST.md` says of
`docs/research/`: "Die zwölf Dateien dort sind sechs Rollenberichte (alle dev), vier Themenberichte
und zwei Synthesen". The directory holds 15 files today (three added on 2026-08-15, 2026-08-16 and
2026-08-31). The sentence was true when written and is a count copied into a second place — the
class `SR-0008` is about. This stream may not edit the wishlist; the lead owns the correction.

**F3 — 445 KB of raw logs under `docs/reviews/` are cited only by prose.** The five `.jsonl` files
in `docs/reviews/2026-08-13-tsk0054-live-logs/` are named by
`docs/reviews/2026-08-13-tsk0054-live-confirm.md` (which IS an EVD `artifact_ref`, `EVD-0023`) and,
for `apr-live2.jsonl`, by `docs/POST_V2_WISHLIST.md`. They are wired and stay — but they are
the largest single block of unread bytes in `docs/`, and `docs/reviews/**` is forbidden to this
stream. Named for whoever gets that scope.

**F4 — `docs/reviews/2026-07-24-harness-v2-review.md` (39 days) has no wire at all.** The oldest
genuinely unread document in the tree. Forbidden scope here; it is what the hint will name first
once it crosses 60 days.

**F5 — `artifact_ref` values are written against two different roots.** Measured over the store,
and the figure depends on WHICH store: in the worktree at `6d18407` it is 80 refs, 21 of them
repo-relative (`docs/reviews/...`) and 59 rooted at `project_memory/` (`staging/...`,
`../docs/...`); the MAIN repo carried 81 at the same hour, because it holds one EVD more. The
numbers in section 6 are the worktree's, the ones here were the main repo's -- re-measured in the
rework (section 9). Nothing enforces either. The reference check built for this round accepts both
and reports which answered — but a store with two conventions is a defect waiting for the first
tool that only knows one. Not closed; no item written (this stream writes no items).

**F6 — the reporter's own limits, in the code and not only here.** A pointer built at run time is
invisible to it, except the one built form it reads (`os.path.join` of literals). A FIXTURE path is
read the same way as a real one, so a fixture naming a real directory would over-wire it. A file
named in a sentence that calls it obsolete counts as read. All three make the hint say LESS, which
is the direction a fail-open hint may err in, and all three are written into the docstrings rather
than left to be discovered.

---

## 6. Verification per move set

### Move set 1 — `docs/pilot/2026-08-09-drehbuecher.md`

**EVD reference check.** Tool: `_round-scratch\TSK-0110\evd_refcheck.py` (read-only; resolves every
`artifact_ref` under a state root against a subject tree, exits 1 on a dangling one).

| run | refs | dangling | rc |
|---|---|---|---|
| before the move (`evd-0-baseline.txt`) | 81 | 0 | 0 |
| after the move (`evd-1-moveset1.txt`) | 81 | 0 | 0 |

**The check was blind at first, and the defect is recorded because it is the interesting part.** Its
first version resolved a state-relative ref against the state root without asking whether the ref
STAYS inside that root — so `../docs/...` escaped into the MAIN repo, whose `docs/` this round never
touches, and every removed file still resolved. Sensitivity probe: a subject tree holding only
`docs/pilot` and `docs/reviews`, with the EVD-referenced
`docs/pilot/2026-08-14-pilot-3-rechnungswerkzeug.md` deleted. **Before the fix: `dangling: 0`,
rc 0** — a check measuring its own environment instead of the change. **After the containment
clause: `dangling: 6`, rc 1**, naming EVD-0033 and EVD-0034 for the deleted report and four EVDs for
the wishlist that partial tree also lacks (`evd-sensitivity.txt`).

**Stamper and validator.** `python tools/bump_kit_version.py` → all three kits unchanged at
`2026.09.02-10` (this stream touched no kit file, so no provisional stamp was minted).
`python tools/validate.py` → all structural checks passed. `python -m ruff check .` → all checks
passed.

**Full `tools/` suite.** Gefahren in Abschnitt 8.5 (nach der letzten Nacharbeit, wie DEC-0050 es verlangt): 4161 bestanden, 14 uebersprungen, 0 fehlgeschlagen.

There is no move set 2: the second candidate the order's bare wire definition allowed
(`docs/research/2026-08-16-model-downgrade-and-tier-pinning.md`) was withdrawn for the reason in 2.3.

---

## 7. Wall clock and process honesty

- Round start (first read in the main repo) ≈ 11:20.
- Erster Umsetzer: 11:20 bis 13:0x (Nutzer-Stopp). Zweiter Umsetzer: 13:50 bis 17:2x, davon rund 2 Stunden reine Laufzeit der Suiten; ein Sitzungslimit hat den zweiten Lauf gegen 16:35 unterbrochen, die Hintergrundlaeufe liefen weiter und wurden danach gemessen (siehe 8.7).

**Two suite runs were started and killed, and both were my error, not the tree's.**
1. A baseline run was started before the edits and I then edited `tools/test_repo_hygiene.py` while
   it was still collecting — the run was no longer a baseline of anything. Killed at 27%; the
   partial log is kept as `suite-0-baseline-ABORTED.txt`. Consequence: **there is no independent
   pre-change baseline from this stream.** The comparable number is the merge round's run on this
   very commit (`DEC-0060`: 4151 passed, 14 skipped, 0 failed on release `2026.09.02-10`).
2. A first move-set-1 run was started and killed at 1% on purpose: the mutation sweep had just shown
   that one branch of the reader could be deleted with every test still green (the file-name half),
   so the file under measurement was known to be incomplete. Measuring it would have produced a
   green number for a version that was replaced ten minutes later.

**Two defects of my own were found by my own measurements before the verifier saw them**, and both
are recorded above rather than quietly fixed: the blind reference check (section 6) and the
extension enumeration in the wire reader, whose alternation put `json` before `jsonl` so that
`run.json` matched inside `run.jsonl` — which made five log files look unread while a review
protocol cited every one of them. The enumeration is gone; the alternation is now built from the
candidates themselves and bounded at both ends (M8/M9).

---

## 8. Fortsetzung nach dem Nutzer-Stopp (zweiter Umsetzer, ab 13:50)

Der erste Lauf wurde vom Nutzer gestoppt, nicht wegen eines Fehlers. Übernommen wurde der Stand auf
der Platte: ein gestagter Umzug, `tools/test_repo_hygiene.py` geändert, `docs/archive/2026/README.md`
neu, beide Protokolldateien. Was hier steht, ist geprüft und nicht geerbt.

### 8.1 Was am Stand des Vorgängers geprüft wurde, und was daran nicht stimmte

**Der Umzug ist sauber.** Gegenprobe unabhängig vom Protokoll: eine Volltextsuche nach
`drehbuecher` über den ganzen Arbeitsbaum (ohne `.git`) und über den kanonischen Zustand des
Hauptbaums findet genau zwei Treffer, den neuen Archiv-Index und dieses Protokoll. Kein Test, kein
Loch-Eintrag, kein `artifact_ref`, kein Item, keine Kit-Datei.

**Vier Befunde am Paket, alle behoben oder benannt:**

1. **Der ausgelieferte Leser war schmaler als die Messung, die den Umzug entschieden hat** — und
   schmaler in der lauten Richtung. `_reference_corpus` las fünf benannte Verzeichnisse (`tools`,
   `.claude/hooks`, `team-kits`, `docs`, `project_memory`), während der Handdurchgang
   (`_round-scratch/TSK-0110/wire_scan.py`) den ganzen Baum las. Ein Dokument, das nur `README.md`,
   `HARNESS_LOG.md`, eine Rollendefinition unter `.claude/agents/` oder `install.sh` nennt, wäre
   dem Melder als ungelesen erschienen. Gemessen mit `_round-scratch/TSK-0110/corpus_breadth.py`
   (Ausgabe `corpus-breadth.txt`): am Baum von heute ändert die Verbreiterung **eine** Antwort
   (`docs/reviews/2026-08-29-ci-red-classification.md`: `ITEM` zu `ITEM,PROSE`) und **keine**
   Umzugsentscheidung — der Grund, es trotzdem zu ändern, ist die Fehlerrichtung, nicht die Antwort
   von heute. Der Korpus ist jetzt die Antwort von git selbst auf die Frage, ob eine Datei zum Repo
   gehört (`git ls-files -c -o --exclude-standard`), also keine Verzeichnisliste mehr.
2. **Eine Behauptung im Kommentar, die der Code nicht baute.** Der Rumpf von `_ref_candidates`
   (aus dem Scratch-Werkzeug übernommen) sagte, ohne die Einschluss-Klausel könne die Prüfung gar
   nicht scheitern. Im Repo-internen Fall ist das falsch: `project_memory/../docs/x` ist `docs/x`,
   und die Klausel ändert dort nichts. Gemessen: die Mutation **M-K** (Klausel entfernt) lief
   **grün** durch. Die Behauptung ist jetzt ein Test
   (`test_a_ref_that_climbs_out_of_the_repo_resolves_nowhere`), und M-K ist danach rot.
3. **Der Wunschlisten-Durchgang war in Abschnitt 3 um ein Item daneben** (die Zeile sagte, kein Item
   enthalte `drawio`). Nachgemessen 2026-09-02: `mindmap` in keinem Item, `drawio` in genau einem
   (`bugs/active/BUG-0074.yaml`, dort als Dateiname `WFR-000n.drawio.svg`). Das Format ist in den
   Kits für Wireframes und Architekturbilder bereits in Gebrauch; das dünne FR erweitert es, es
   führt es nicht ein. `wishlist-pass.md` Abschnitt 3 ist entsprechend korrigiert — die übrigen
   Zusagen des Durchgangs wurden stichprobenartig gegen den Zustand geprüft (`FR-0021`, `FR-0024`,
   `FR-0032`, `FR-0047`, `FR-0074` TRIAGED; `FR-0045`, `FR-0003` MERGED; `DEC-0058` VALID; die
   Rückverweise auf Abschnitt 2 und Abschnitt 6 stehen wirklich in `FR-0024` bzw. `FR-0021`).
4. **Ein Suite-Lauf des Vorgängers lief noch** (pid 35504, gestartet 13:09, bei rund 77 %). Er maß
   einen Baum, der sich danach änderte, und wurde beendet. Der Lauf, der zählt, ist der in 8.5.

### 8.2 Der Stolperdraht, der den Archivordner kennt (Auftragspunkt 3)

Die Frage, was dort liegen darf und was nicht, ist als Eigenschaft gebaut, in zwei Teilen:

**(a) Jede Datei unter `docs/archive/` steht in genau einem Index — und jede Zeile eines Index
nennt eine Datei, die da ist.** `test_every_archived_file_is_named_by_the_index_above_it`. Ein
Index ist eine Aufzählung, und die Hausregel für eine Aufzählung ist ein Draht an **beiden** Enden:
der tote Eintrag und der Eintrag, den nie jemand geschrieben hat. Zuständig ist der **nächste**
Index über der Datei, damit keine Datei doppelt und keine gar nicht geführt wird.
Der Fall ist nicht hypothetisch: der Test war beim ersten Lauf **rot** und nannte vier Dateien —
`docs/archive/staging-of-archived-items/TSK-0018|0020|0021|0029/*` —, die seit 2026-08-13 ohne
jeden Eintrag im Archiv lagen; ihr Grund musste aus
`docs/reviews/2026-08-13-tsk0055-closure-round.md` zurückgeholt werden. Dafür ist
`docs/archive/README.md` neu geschrieben.

**(b) Kein `artifact_ref` des Zustands zeigt ins Leere.**
`test_every_artifact_ref_still_resolves_where_it_points` — der Beweis-Referenz-Check, den das Item
verlangt, jetzt als laufender Test statt nur als Skript im Scratch. Er liest den ganzen Speicher
(80 Refs im Arbeitsbaum, gemessen 2026-09-02), löst gegen **beide** Wurzeln auf, die der Speicher
wirklich benutzt, und verlangt, dass überhaupt eine geantwortet hat — ein Leser, der nichts findet,
würde sonst stumm bestehen. Dass beide Wurzeln ERREICHBAR sind, steht seit der Nacharbeit auf
synthetischer Eingabe im Nachbartest und nicht mehr am Speicher (Abschnitt 9, M1).
Der gemessene Fehlerfall (DEC-0056 verlangt für einen neuen Draht einen wirklich vorgekommenen
Fehler, und Punkt (c) derselben Entscheidung nimmt archivierte Dokumente ausdrücklich von der
Sparsamkeit aus): am 2026-08-13 zog die Staging-Ablage von TSK-0022 ins Archiv und musste zurück,
weil EVD-0001/0002/0003 ihre `artifact_refs` dorthin führen und ein EVD unveränderlich ist.
`FR-0036` nennt einen zweiten Vorfall; den hat diese Runde nicht nachgemessen und behauptet ihn
nicht.

**Ausdrücklich NICHT gebaut, mit Grund:** ein Draht, der jede Nennung eines Archivpfads verbietet.
Ein Rundenprotokoll oder ein Loch-Eintrag darf einen Umzug beschreiben und dabei den Pfad nennen —
gerade dieses Protokoll tut es. Was nicht ins Leere zeigen darf, ist ein Verweis, der **auflösen
muss**; das ist (b). Gemessen wurde auch der naheliegende Namens-Leser: er ist für das Archiv
untauglich, weil der Index `README.md` heißt und über 40 lebende Dateien dieses Wort nennen
(`_round-scratch/TSK-0110/archive-probe.txt`).

### 8.3 Weitere Änderungen am Leser, jede mit ihrer roten Mutation

- **`_is_a_record`** — eine Regel für beide Archive dieses Repos (Item-Speicher und `docs/archive/`)
  statt einer Sonderregel für eines. Ein Verweis **aus** einem Archiv ist ein Protokoll, kein Lesen;
  sonst hielte der Index seinen eigenen Gegenstand am Leben und nichts wäre je archivierbar.
- **Staging ist `PROSE`, nicht `ITEM`** — `project_memory/staging/` ist laut `CLAUDE.md` kein
  Zustand. Für den Hinweis ändert das nichts (jede Klasse hält eine Datei heraus); geändert wird,
  was die Fehlermeldung behauptet.
- **Alles, was das Repo sonst trägt, ist `PROSE`** statt „kein Verweis" — siehe 8.1 Punkt 1.
- **`_TOO_BIG_FOR_PROSE`** — die Größe, ab der eine Datei keine Prosa mehr ist, steht an einer
  Stelle und wird von zwei Lesern benutzt.

### 8.4 Die roten Läufe (Sandkasten außerhalb beider Repos)

Kopie des Arbeitsbaums unter `_round-scratch/TSK-0110/mutation2/`, Treiber
`_round-scratch/TSK-0110/mutate2.py`, volles Protokoll `mutations2.txt`. Jede Zeile: Defekt
hergestellt, `tools/test_repo_hygiene.py` gefahren, zurückgesetzt. Basislauf 18 (nach dem Nachtrag
19) grün, Schlusslauf grün.

| Defekt | rot geworden ist |
|---|---|
| M1 Verzeichnis-Drähte entfernt | `test_the_docs_wire_reader_answers_both_ways` |
| M2 ein Archiv zählt wieder als Leser | dito |
| M3 Karenzzeit ignoriert | `test_the_docs_hint_fires_only_past_the_grace_period` |
| M4 der Hinweis spricht mit leerer Liste | dito |
| M6 ein lebendes Item zählt nicht mehr | `test_the_docs_wire_reader_answers_both_ways` |
| M7 der Namensleser ist leer | dito |
| M8 / M9 linke / rechte Namensgrenze weg | dito |
| M10 ein Dokument liest sich selbst | dito |
| M11 der Literal-Lauf hält nicht an der Variablen | `test_the_directory_reader_takes_the_literal_run_and_stops_at_the_first_hole` |
| M-I Halter außerhalb der fünf Verzeichnisse fallen ins Leere | `test_the_docs_wire_reader_answers_both_ways` |
| M-J der Korpus liest wieder fünf benannte Verzeichnisse | `test_the_corpus_drops_a_carried_file_only_where_it_cannot_be_read` |
| M-D der Index-Vergleicher antwortet nichts | `test_the_index_reader_answers_both_ways` |
| M-E der Index-Leser nimmt die falsche Spalte | `test_every_archived_file_is_named_by_the_index_above_it` |
| M-G der Ref-Leser kennt nur eine Wurzel | `test_every_artifact_ref_still_resolves_where_it_points` |
| M-H der Ref-Leser ist leer | dito |
| M-K die Einschluss-Klausel fällt weg | `test_a_ref_that_climbs_out_of_the_repo_resolves_nowhere` (vorher: **grün**, siehe 8.1 Punkt 2) |
| M-B eine Datei liegt ohne Zeile im Archiv | `test_every_archived_file_is_named_by_the_index_above_it` |
| M-A der Index nennt eine Datei, die nicht da ist | dito |
| M-C ein neuer Archivordner ohne eigenen Index | dito |
| **M-F der gemessene Fall: ein EVD-referenzierter Bericht wird ins Archiv verschoben** | dito (`-x` bricht vor dem Ref-Test ab; dessen Empfindlichkeit misst M-G/M-H) |

### 8.5 Läufe am Arbeitsbaum

- `python -B -m ruff check tools/` — alle Prüfungen bestanden.
- `python tools/validate.py` — alle strukturellen Prüfungen bestanden.
- `python tools/bump_kit_version.py` — alle drei Kits **unverändert** bei `2026.09.02-10`; diese
  Runde fasst keine Kit-Datei an, es wird also kein Stempel geprägt.
- `python -B -m pytest tools/test_repo_hygiene.py -q` — 19 grün.
- Melder am laufenden Baum nach der Verbreiterung, **gemessen 2026-09-02 um 13:59 im Arbeitsbaum
  `g2-hygiene`** mit `_round-scratch/TSK-0110/reader_report.py` (`reader-report-after.txt`): Korpus
  1027 Dateien, 100 Kandidaten, 98 verdrahtet, 2 nicht — `docs/handback/HANDBACK.md` (21 Tage) und
  `docs/reviews/2026-07-24-harness-v2-review.md` (40 Tage), beide unter der Karenz, der Hinweis
  schweigt. Klassen: PROSE 81, ITEM 45, TEST 29, HOLE 20, KIT 13. **Diese Zahlen sind der Stand vor
  der Nacharbeit** — sie wandern mit jedem Kommentar, der einen Dateinamen nennt; der Stand danach
  steht in Abschnitt 9, und die Klasse `TEST` heißt dort `CODE`.
- **Volle `tools/`-Suite: 4161 bestanden, 14 uebersprungen, 0 fehlgeschlagen.** In drei Teilen
  gefahren, zusammen der ganze Baum `tools/`, jede Datei genau einmal:
  `tools/test_hooks.py` (900 bestanden, 13 uebersprungen, 29:42, `suite-3a-hooks.txt`);
  `tools/test_kitupdate.py tools/test_hooks_v2.py tools/test_e2e.py` (2234 bestanden, 1
  uebersprungen, 50:50, `suite-3c-heavy.txt`); der Rest ueber `tools/` mit `--ignore` fuer diese
  vier Dateien (1027 bestanden, 41:19, `suite-3b-rest.txt`). Die Summe stimmt gegen den
  Vergleichslauf der Merge-Runde auf demselben Commit (`DEC-0060`: 4151 bestanden, 14
  uebersprungen) plus die **zehn** Tests, die diese Runde hinzufuegt — fuenf vom ersten, fuenf vom
  zweiten Umsetzer.
  **Warum drei Teile und nicht einer:** ein einzelner Lauf ueber `tools/` lief 74 Minuten bis 86 %
  (ohne einen einzigen Fehlschlag) und wurde dann von der Umgebung beendet, nicht vom Baum
  (`suite-2-final-stdout.txt`). Zur selben Zeit liefen auf diesem Host vier weitere pytest-Sitzungen
  anderer Stroeme (gemessen in der Prozessliste um 16:17: `g2-kernel`, `TSK-0109/verify-3`, zwei
  Gate-Laeufe). Der geteilte Lauf misst denselben Umfang und haelt jeden Teil unter der Grenze.
- **Gate-Suite** (`python -B -m pytest .claude/hooks/test_gates.py -q` im Arbeitsbaum, 37:47,
  `gates-worktree.txt`): **488 bestanden, 1 fehlgeschlagen** —
  `test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`, und der
  Fehlschlag gehoert **nicht** dieser Runde. Siehe F7 in 8.7.

### 8.6 Warum die Umzugsliste eine Datei lang bleibt

Nach dem Umzug sagt das ausgelieferte Instrument selbst, was noch ohne Draht ist: genau zwei
Dateien, und beide werden nicht bewegt — `docs/handback/HANDBACK.md` ist eine offene
Handlungsanweisung an den Nutzer (F1), `docs/reviews/2026-07-24-harness-v2-review.md` liegt in
verbotenem Bereich (F4). Alles andere unter `docs/` hat mindestens einen Verweis. Die vier
Pilot-Dateien, die die nackte Definition des Auftrags noch zuließe, sind je einen oder zwei
Schritte von einem Beweisverweis entfernt (2.3); sie zu bewegen hieße, dem eigenen Instrument zu
widersprechen, und im Zweifel bleibt die Datei stehen. Das ist die Ausbeute, und sie ist gemessen,
nicht geschätzt.

### 8.7 Der rote Gate-Test, gemessen statt eingeordnet (F7)

`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge` ist im Arbeitsbaum
rot: die Verweigerung kam nach 4,59 s, während die Registrierung 4,50 s gibt — 2 % darüber. Der Test
sagt in seiner eigenen Meldung, wie er einzuordnen ist: solo ein echter Rückschritt, unter paralleler
Last `BUG-0033`. Also gemessen, nicht eingeordnet — dieselbe einzelne Prüfung, sechs Läufe, in drei
Bäumen:

| Baum | Ergebnis |
|---|---|
| Arbeitsbaum `g2-hygiene` (mit den Änderungen) | rot 4,59 s · rot · rot 4,69 s |
| **Sauberer Auszug von `6d18407`, ohne jede Änderung dieser Runde** (`_round-scratch/TSK-0110/base-full/`) | **grün · rot 4,54 s · grün · rot 5,56 s · rot 4,58 s** |
| Hauptbaum `C:\Offline Repos\AgentAndSkills` | grün |

Der unveränderte Basisbaum ist in vier von sechs Läufen rot, mit demselben Abstand von 1 bis 4 %.
Damit ist der Fehlschlag **nicht dieser Runde zuzurechnen**: er tritt ohne ihre Änderungen genauso
auf. Nichts an dieser Runde fasst `.claude/`, die Registrierung oder eine Frist an — der Umfang
sind `docs/**` und `tools/test_repo_hygiene.py`.

Was der Lead damit tun sollte, steht ihm zu und nicht mir: entweder auf einem ruhigen Host
nachmessen (dann ist die Frage in einer Minute beantwortet) oder den Befund an `BUG-0033` hängen.
Diese Runde behauptet **nicht**, dass die Gate-Suite grün ist, und ebenso wenig, dass hier ein
Rückschritt vorliegt.

### 8.8 Zwei Unterbrechungen, und was sie am Ergebnis geändert haben

1. **Nutzer-Stopp gegen 13:0x** — Ende des ersten Umsetzers, kein Fehler. Sein Stand lag auf der
   Platte und ist in 8.1 geprüft.
2. **Sitzungslimit gegen 16:35** (zweiter Umsetzer). Zu dem Zeitpunkt liefen drei Läufe im
   Hintergrund (Gate-Suite, Suite-Teil B, Suite-Teil C); sie liefen weiter und wurden nach dem
   Wiederaufsetzen um 17:16 vollständig ausgelesen — die Zahlen in 8.5 stammen aus diesen
   abgeschlossenen Läufen, nicht aus einer Schätzung. Am Arbeitsbaum wurde nach der Unterbrechung
   nichts mehr geändert: der um 16:18 erzeugte Patch ist byte-gleich mit einem frisch erzeugten
   (gemessen 17:2x), und `git status` zeigt dieselben vier Einträge.

### 8.9 Übergabe

- Patch: `_round-scratch/TSK-0110/stream-hygiene.patch` (48.857 Bytes, vier Dateien: zwei neue
  Index-Dateien, die Umbenennung mit `rename from`/`rename to`, und
  `tools/test_repo_hygiene.py` mit +760 Zeilen).
- **Der Patch ist auf einem sauberen Auszug von `6d18407` angewandt worden, nicht nur geprüft:**
  `git apply --check -p1` rc 0, danach `git apply -p1` rc 0 in
  `_round-scratch/TSK-0110/applycheck/`; danach liegt `2026-08-09-drehbuecher.md` unter
  `docs/archive/2026/pilot/` und nicht mehr unter `docs/pilot/`. Die Umbenennung überlebt den Patch
  also, die Historie bleibt.
- `_round-scratch/TSK-0110/git-status.txt` — vier Einträge plus
  `project_memory/.audit/hook_events.jsonl`, das eine Haken-Nebenwirkung ist und **nicht** im Patch
  steht (der Patch ist auf `docs` und `tools` begrenzt).
- Kein Commit, kein Push, kein Stempel, kein Eintrag in der Löcherliste, kein Item geschrieben.

---

## 9. Nacharbeit 1 (nach dem Prüfbericht: B 2, M 1, N 7)

Rig: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0110\rework1\` — eine Kopie des Arbeitsbaums,
zu einem **eigenständigen** git-Repo gemacht (`git init` + `git add -A`, kein Commit), weil beide
blockierenden Punkte an git hängen und ein Klon, dessen `.git` auf den echten Arbeitsbaum zeigt,
die falsche Frage beantwortet.

**Ein Nebeneffekt dieses Rigs, offen gesagt:** in ihm ist
`test_the_known_out_of_scope_trace_is_still_the_only_exception` konstant rot — ein frisches
`git add -A` verfolgt die ignorierte Datei `project_memory/.audit/hook_events.jsonl` nicht, die im
echten Repo historisch verfolgt ist, und genau deren Ausnahme prüft dieser Test. Er ist im
Arbeitsbaum grün (21 von 21) und in jeder Zeile unten als konstanter Untergrund vorhanden; die
Mutationsurteile lesen sich deshalb am **Namen** des zusätzlich gefallenen Tests, nicht am rc.

### 9.1 B1 — die Summenzeile des Wunschlisten-Durchgangs war falsch

Nicht zwei Zeilen fehlten, die Zahl war falsch. Gezählt wird jetzt **aus der Tabelle**, mit
`rework1/count_pass.py` (liest ausschließlich die Tabelle unter „## Summary for the lead", damit die
neue Zeiger-Tabelle sie nicht verfälscht — nachgemessen: vor und nach dem Anhängen dasselbe
Ergebnis):

```
rows: 14
pointer exists     5
superseded         2
thin FR needed     7
```

`wishlist-pass.md` trägt diese Zahlen jetzt als **gezählte** Zahlen mit Datum und Werkzeug;
`round-protocol.md` §1 wiederholt gar keine Zahl mehr, sondern zeigt auf die Tabelle. Zusätzlich
(N6) hängt am Durchgang eine Tabelle **„Was der Lead eintragen soll"**: je Abschnitt der Anker
(Überschrift, Zeilennummer als Beigabe) und der exakte Satz, der in den Abschnitt gehört, mit
Status. Alle darin genannten Status sind am 2026-09-02 im Speicher gemessen (`FR-0017`, `FR-0030`,
`FR-0053`, `DEC-0034`, `DEC-0059`, `FR-0040`, `FR-0002` in dieser Nacharbeit nachgezogen).

### 9.2 B2 — der Archiv-Draht las die Platte, nicht das Repo

Gemessen **vor** dem Fix (`rework1/b2_ignored.py`, Ausgabe `b2-before.txt`): eine **ignorierte**
Datei unter `docs/archive/2026/` macht `test_every_archived_file_is_named_by_the_index_above_it`
hart rot — `build.log` (`.gitignore` Zeile 23, `*.log`) und `Thumbs.db` (Zeile 3), beide mit
`git check-ignore` als ignoriert bestätigt. Das ist kein Angriff: `Thumbs.db` legt der Explorer an,
`*.log` fällt aus Werkzeugen.

| Lauf | vor dem Fix | nach dem Fix |
|---|---|---|
| `build.log` unter `docs/archive/2026/` | **RED** | GREEN |
| `Thumbs.db` unter `docs/archive/2026/` | **RED** | GREEN |
| Basis / wiederhergestellt | GREEN | GREEN |

Fix: **beide** Gegenstände lesen jetzt dieselbe Tür wie der Korpus — `_carried_under(prefix)` über
`_carried_files()`, also git. Das behebt auch den Widerspruch im eigenen Paket (`_carried_files`
argumentierte „git's own answer … rather than a walk with a skip list", während zwei Nachbarn
genau so eine Liste führten). `_docs_candidates` ist mitgezogen, obwohl es dort fail-open war.

**Der Draht dagegen ist jetzt gebaut und nicht nur repariert:**
`test_the_subjects_are_what_the_repo_carries_not_what_lies_on_the_disk` schiebt eine synthetische
Trägerliste unter und prüft beide Gegenstände daran — ein Lauf über die Platte ignoriert diese
Liste und antwortet mit dem echten Baum, also fällt er auf. Nichts in der Suite legt eine ignorierte
Datei an, deshalb hätte ohne diesen Test niemand gemerkt, wenn der Lauf zurückkommt.

**Gegenprobe, dass der Fix nicht blind macht:** MR12 unten legt eine **unverfolgte, nicht
ignorierte** Datei ins Archiv — git trägt sie (`-o --exclude-standard`), und der Draht wird
weiterhin rot. Der Fix nimmt dem Draht die ignorierten Dateien, nicht die neuen.

### 9.3 M1 — die Ref-Prüfung machte F5 tragend

Gemessen **vor** dem Fix (`rework1/m1_refs.py`, `m1-before.txt`): die **richtige** Reparatur von F5
— alle `artifact_ref` auf EINE Wurzel normalisiert, 57 Dateien / 59 Refs — macht
`test_every_artifact_ref_still_resolves_where_it_points` rot, und die Meldung schickt den Leser zum
Test statt zum Speicher. **Nach** dem Fix (`m1-after.txt`): grün.

Der Fix nimmt die speichergekoppelte Zeile heraus (`assert answered == {"state", "repo"}` →
`assert answered`, also nur noch die Leere-Sperre) und setzt die Erreichbarkeit **beider** Wurzeln
auf synthetische Eingabe in `test_a_ref_that_climbs_out_of_the_repo_resolves_nowhere`:

```
assert [rooting for rooting, _ in _ref_candidates("staging/…")]   == ["state", "repo"]
assert [rooting for rooting, _ in _ref_candidates("../docs/…")]   == ["state"]
```

Was die alte Zeile exklusiv gefangen hätte, war ein vertauschtes Etikett; den Verlust einer Wurzel
im Leser fangen weiterhin zwei Tests (MR3 unten: beide fallen).

### 9.4 Der Sweep der Nacharbeit — jeder Defekt rot am richtigen Test

`rework1/mutate3.py`, Ausgabe `mutations3.txt`. **Die Tabelle IST die Liste; hier steht keine Zahl
daneben** — die erste Fassung sagte „16" und zählte MR11 doppelt, weil dieser Defekt zweimal
gemessen wurde (erst grün, nach dem neuen Test rot). Untergrund je Zeile ist der Rig-Nebeneffekt
oben; genannt ist der Test, der **zusätzlich** fällt.

| Defekt | zusätzlich rot |
|---|---|
| MR1 der Archiv-Gegenstand läuft wieder über die Platte | `test_the_subjects_are_what_the_repo_carries_not_what_lies_on_the_disk` |
| MR2 der docs-Gegenstand läuft wieder über die Platte | dito |
| MR3 der Ref-Leser verliert die `state`-Wurzel | `test_every_artifact_ref_still_resolves_where_it_points` **und** `test_a_ref_that_climbs_out_of_the_repo_resolves_nowhere` |
| MR4 der Ref-Leser ist leer (Leere-Sperre) | `test_every_artifact_ref_still_resolves_where_it_points` |
| MR5 die Einschluss-Klausel fällt weg | `test_a_ref_that_climbs_out_of_the_repo_resolves_nowhere` |
| MR6 der Index-Vergleicher antwortet nichts | `test_the_index_reader_answers_both_ways` |
| MR7 der Index-Leser nimmt die falsche Spalte | `test_every_archived_file_is_named_by_the_index_above_it` + `test_the_index_reader_answers_both_ways` |
| MR8 der Korpus liest wieder fünf benannte Verzeichnisse | `test_the_corpus_drops_a_carried_file_only_where_it_cannot_be_read` |
| MR9 ein Archiv zählt wieder als Leser | `test_the_docs_wire_reader_answers_both_ways` + der Gegenstands-Test |
| MR10 Halter außerhalb der offensichtlichen Verzeichnisse fallen ins Leere | `test_the_docs_wire_reader_answers_both_ways` |
| MR11 ein git-Fehlschlag wird verschluckt statt gesagt | `test_a_corpus_that_cannot_be_listed_says_so_instead_of_reading_as_empty` |
| MR12 eine unverfolgte, **nicht** ignorierte Datei landet im Archiv | `test_every_archived_file_is_named_by_the_index_above_it` |
| MR13 der Index nennt eine Datei, die nicht da ist | dito |
| MR14 ein neuer Archivordner ohne eigenen Index | dito |
| MR15 **der gemessene Fall:** ein EVD-referenzierter Bericht zieht ins Archiv | `test_every_artifact_ref_still_resolves_where_it_points` |

MR11 war im ersten Durchgang **grün** — die Zeile „ein git-Fehlschlag wird gesagt statt
verschluckt" war eine Behauptung ohne Draht. Daraufhin ist
`test_a_corpus_that_cannot_be_listed_says_so_instead_of_reading_as_empty` entstanden (schiebt ein
`subprocess` unter, das rc 128 meldet); danach ist MR11 rot, wiederhergestellt grün.

### 9.5 Die niedrigen Punkte

- **N1** Der Korpus ist, was **git trägt**. Das steht jetzt als Grenze im Docstring des Melders:
  behaupten darf er „nichts, was git trägt, nennt die Datei" — nicht „nichts nennt sie". Gemessen
  auf diesem Baum (`rework1/n1_ignored_corpus.py`, `n1-uncarried.txt`): **außerhalb der
  Werkzeug-Caches gibt es keine einzige nicht getragene Datei**, das blinde Feld ist heute also
  leer und nicht bloß klein. **Rest für die Merge-Runde** (dieser Strom nummeriert keine Löcher):
  eine Nennung in einer ignorierten Datei — Laufprotokoll, `project_memory/.audit/`, ein
  generiertes Dashboard — sähe der Melder nicht; Kette: ignorierte Datei nennt `docs/x.md` → kein
  anderer Verweis → nach 60 Tagen nennt der Hinweis `docs/x.md` als ungelesen → eine Runde
  verschiebt sie → die Nennung in der ignorierten Datei zeigt ins Leere. Folgenlos, solange nichts
  Ignoriertes Dokumente nennt.
- **N2** Der Index-Leser nimmt eine **feste** zweite Spalte und parst keine Kopfzeile; der Kommentar
  sagt das jetzt so und nennt die Kopfzeile eine Zusage **an** den Leser, nicht eine Prüfung.
- **N3** Die Klasse heißt jetzt **`CODE`**, nicht `TEST`: „Code unter `tools/` oder
  `.claude/hooks/`, der den Namen nennt — ein Test ist davon nur ein Fall". Gemessen
  (`rework1/n3_code_class.py`, `n3-code-class.txt`): zwei Dokumente unter `docs/` verdanken ihre
  CODE-Klasse **keinem Test** — `docs/reviews/2026-08-05-tsk0007-measurements.md` (Drähte
  `CODE, PROSE`; genannt von `.claude/hooks/_harness.py` und `gate_lead_write_scope.py`) und
  `…-tsk0013-…` (Drähte `CODE, HOLE, PROSE`; genannt **nur** von `_harness.py`, dem gemeinsamen
  Rumpf der Gates, der selbst kein Gate ist). Beide tragen daneben andere Drähte; was ihnen fehlt,
  ist ein Test. Docstrings, Meldungstexte und `docs/archive/2026/README.md` sind nachgezogen (dort
  auch „kein Test" → „kein Code" in der Umzugsbegründung).
- **N4** Die beiden wachsenden Zahlen sind aus den Kommentaren heraus (`five 445 KB log files`,
  `75 documents carry it`); sie stehen hier, wo eine Messung hingehört: 75 Dokumente des Speichers
  tragen `artifact_ref(s)` (gemessen 2026-09-02 im Arbeitsbaum).
- **N5** Zahlen mit Baum und Zeitpunkt, siehe unten; die alten Angaben sind als „Stand vor der
  Nacharbeit" gekennzeichnet, und der Widerspruch 81/80 ist aufgelöst: **80** im Arbeitsbaum
  (21 `repo` / 59 `state`), **81** im Hauptbaum, der ein EVD mehr führt.
- **N6** siehe 9.1.
- **N7** `project_memory/.audit/hook_events.jsonl` bleibt unangetastet und ist nicht im Patch.

### 9.6 Stand nach der Nacharbeit, gemessen

Alles am 2026-09-02 im Arbeitsbaum `g2-hygiene` nach der letzten Änderung:

- `python -B -m pytest tools/test_repo_hygiene.py tools/test_disposition.py -q` → **29 grün**
  (Hygiene 21, Disposition 8).
- `--collect-only` auf `tools/test_repo_hygiene.py`: **21** Tests (vorher 19; die Nacharbeit legt
  zwei dazu). Zur Erinnerung an die Rechnung aus 8.5: der Basisstand hatte 9.
- `python -B -m ruff check .` → bestanden. `python tools/validate.py` → bestanden.
- `python tools/bump_kit_version.py` → alle drei Kits unverändert `2026.09.02-10`; kein Kit
  berührt, kein Stempel.
- Melder am laufenden Baum (`rework1/reader-report-rework1.txt`): Korpus **1028** Dateien,
  100 Kandidaten, 98 verdrahtet, 2 nicht (dieselben zwei), Klassen **CODE 30, HOLE 20, ITEM 45,
  KIT 13, PROSE 81**. Der Unterschied zu 8.5 (1027 / TEST 29) ist erklärt und nicht kosmetisch:
  die Docstrings dieser Nacharbeit nennen Dateinamen, also verdrahten sie — der Melder misst auch
  sich selbst.
- `artifact_ref`s im Speicher des Arbeitsbaums: **80**, davon 21 über die Wurzel `repo`, 59 über
  `state`; 75 Dokumente tragen den Schlüssel.

**Die volle `tools/`-Suite ist NICHT erneut gefahren**, und das ist eine Entscheidung mit Grund:
die Forderung des Items gilt den **Umzügen**, und die Nacharbeit bewegt keine Datei — der
Umzugssatz ist unverändert der eine aus 2.2, `git status` zeigt dieselbe Umbenennung. Geändert sind
`tools/test_repo_hygiene.py` und zwei Index-Dateien unter `docs/archive/`. Ändert eine spätere
Runde einen Umzug, gilt die Forderung wieder. Der letzte gemessene volle Lauf steht in 8.5
(4161 grün, 14 übersprungen); er beschreibt den Stand vor den zwei neuen Tests.

### 9.7 Übergabe nach der Nacharbeit

- `_round-scratch/TSK-0110/stream-hygiene.patch` — neu erzeugt, **54.083 Bytes**, vier Dateien
  (+911/−1): `tools/test_repo_hygiene.py`, die beiden Index-Dateien, die Umbenennung.
- **Auf zwei Basen angewandt, nicht nur geprüft:** `6d18407` und `c4f3cc0`, je
  `git apply --check -p1` rc 0 und danach `git apply -p1` rc 0
  (`rework1/apply1/`, `rework1/apply2/`). In beiden liegt `2026-08-09-drehbuecher.md` danach unter
  `docs/archive/2026/pilot/` und nicht mehr unter `docs/pilot/` — die Umbenennung überlebt den
  Patch auf beiden Basen.
- Im Patch kommt `.audit` **nicht** vor (geprüft: der einzige Treffer auf „audit" ist das Wort in
  einem Kommentar). `git-status.txt` dagegen bleibt die **rohe** Ausgabe von
  `git status --porcelain` und führt `M project_memory/.audit/hook_events.jsonl` weiterhin auf.
  Das ist Absicht und der einzige Punkt, an dem diese Nacharbeit vom Wortlaut des Auftrags
  abweicht: eine Statusdatei, aus der eine geänderte Datei herausgeschnitten ist, behauptet einen
  Baum, den es nicht gibt — und genau das ist die Klasse Fehler, die diese Runde sonst verfolgt.
  Die Datei ist eine Haken-Nebenwirkung, sie gehört nicht zum Strom, und sie ist nicht im Patch.
- Kein Commit, kein Push, kein Kit angefasst, kein Stempel, kein Loch nummeriert, kein Item
  geschrieben.

---

## 10. Nacharbeit 2 (Nachprüfung: M 1, N 3 — Behauptungsebene)

Rig: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0110\rework2\` (der Baum ohne `.git`),
Mutationen weiter in `rework1\`.

### 10.1 NF1 — „fail-open" war auf einem Baum ohne `.git` falsch

Der Melder sagt von sich „deliberately FAIL-OPEN: it never blocks a round". Gemessen auf einem
`git archive`-Auszug des Arbeitsbaums, also einem Baum **ohne `.git`**
(`rework2/nogit-before.txt`):

```
4 failed, 15 passed, 2 skipped
FAILED test_docs_prose_nothing_reads_any_more_is_reported_not_failed
FAILED test_the_running_tree_shows_every_wire_kind_this_reader_claims_to_see
FAILED test_every_archived_file_is_named_by_the_index_above_it
FAILED test_the_corpus_drops_a_carried_file_only_where_it_cannot_be_read
```

Die zwei, die **sauber übersprungen** haben, sind die beiden älteren Mitglieder derselben Datei:
sie fragen `git rev-parse --is-inside-work-tree` und nicht nur „liegt git im PATH". Zwei Antworten
auf dieselbe Frage, und die zugesagte Hälfte war die falsche.

Fix: `_require_git()` trägt jetzt die **ganze** Frage (PATH **und** Arbeitsbaum), und die beiden
älteren Mitglieder fragen sie dort statt sie zu wiederholen — eine Antwort an einer Stelle. Danach
auf demselben Baum (`rework2/nogit-after.txt`):

```
15 passed, 6 skipped        SKIPPED [6] tools/test_repo_hygiene.py: not a git work tree
```

(Der Lauf ist am Ende der Nacharbeit 2 gegen die **ausgelieferte** Datei wiederholt worden, damit
das Protokoll nicht den Rig-Stand zitiert; die Zeilennummer aus der pytest-Ausgabe steht hier
bewusst nicht — sie wandert mit jeder Einfügung, der Testname und der Skip-Grund nicht.)

Vier Fehlschläge sind vier Übersprünge geworden; die zwei alten sind dieselben geblieben.
**MR11 behält seine Bedeutung** — dort liegt git im PATH, der Arbeitsbaum existiert, und
`ls-files` scheitert trotzdem: nach dem Fix erneut gemessen, RED, wiederhergestellt GREEN.

### 10.2 NF2 — die Zahl neben der Liste, zum zweiten Mal

§9.4 sagte „16 Defekte", die Tabelle führt 15: MR11 war doppelt gezählt, weil er zweimal gemessen
wurde (erst grün, nach dem neuen Test rot). Die Zahl ist gestrichen — die Tabelle ist die Liste.

### 10.3 NF3 — „wirklich da" ist seit B2 nicht mehr der Gegenstand

Selbst nachgemessen im Rig: eine archivierte Datei gelöscht, Löschung **nicht** gestaged →
`git ls-files` listet sie weiter → Test **grün**; Löschung gestaged → Test **rot**. Der Gegenstand
ist seit B2 „was das Repo trägt", nicht „was auf der Platte liegt". Beide Index-Dateien und die
Fehlermeldung sagen das jetzt so („eine Datei, **die das Repo trägt** … eine Löschung fällt auf,
sobald sie gestaged ist"). Eine zweite Prüfung gegen `os.path.exists` ist bewusst **nicht** gebaut:
die Platte ist nicht der Gegenstand, und das Fenster schließt beim Stagen.

### 10.4 NF4 — der CODE-Satz überzog

Gemessen je Datei: `docs/reviews/2026-08-05-tsk0007-measurements.md` trägt `CODE, PROSE` und wird
von `.claude/hooks/_harness.py` **und** `gate_lead_write_scope.py` genannt;
`…-tsk0013-measurements.md` trägt `CODE, HOLE, PROSE` und wird **nur** von `_harness.py` genannt —
dem gemeinsamen Rumpf der Gates, der selbst kein Gate ist. Richtig ist also nicht „hängen allein an
einem Gate", sondern: **beide verdanken ihre CODE-Klasse keinem Test**. Docstring, Protokoll und
`docs/archive/2026/README.md` sagen jetzt das.

### 10.5 Läufe und Übergabe

- `python -B -m pytest tools/test_repo_hygiene.py tools/test_disposition.py -q` → **29 grün**
  (21 + 8). `python -B -m ruff check .` → bestanden. `python tools/validate.py` → bestanden.
  `python tools/bump_kit_version.py` → alle drei Kits unverändert `2026.09.02-10`, kein Kit
  berührt, kein Stempel.
- Patch neu: **57.260 Bytes**, vier Dateien (+936/−11). Auf **beiden** Basen angewandt, nicht nur
  geprüft: `6d18407` und `c4f3cc0`, je `--check` rc 0 und `apply` rc 0; danach liegt
  `2026-08-09-drehbuecher.md` unter `docs/archive/2026/pilot/` und nicht mehr unter `docs/pilot/`.
  Kein `.audit`-Pfad im Patch (die zwei Treffer auf „audit" sind eine Kontextzeile und ein
  Kommentarwort).
- **Die volle `tools/`-Suite ist wieder NICHT gefahren**: die Forderung des Items gilt den
  **Umzügen**, und auch diese Nacharbeit bewegt keine Datei — der Umzugssatz ist unverändert der
  eine aus 2.2. Ändert eine spätere Runde einen Umzug, gilt die Forderung wieder. Der letzte
  gemessene volle Lauf steht in 8.5.
