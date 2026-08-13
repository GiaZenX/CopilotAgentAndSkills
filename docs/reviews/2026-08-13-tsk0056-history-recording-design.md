# TSK-0056 / BUG-0034 (H2) — step 1: what the running git names, and what the gate will ask

Everything below was measured on this host before a line of the gate was written. Git is
`git version 2.47.1.windows.1`. The scripts that produced the tables are throwaway (scratchpad,
outside the repo); the measurements they produced are ported into `.claude/hooks/test_gates.py`
as the tripwire, so the numbers here are reproducible by the suite and not only by this note.

## 1. Does git NAME its history-recording subcommands? — measured: no

`git --list-cmds=<group>` is the only place git names groups of its own commands.

| asked | answer |
|---|---|
| `git --list-cmds=list-history` | `backfill branch commit merge rebase reset switch tag` |
| `git --list-cmds=list-mainporcelain` | 46 names (`add … worktree`, plus `gitk scalar`) |
| `git --list-cmds=main` | 176 names, every builtin including `commit-tree`, `fast-import`, `subtree`, `svn`, `p4`, `citool`, `gui` |

`list-history` is git's help grouping ("grow, mark and tweak your common history"). It is **not**
the property SR-0009 clause 3 asks about, and it fails in both directions at once:

* it CONTAINS `branch`, `switch`, `reset`, `tag`, `backfill` — measured below to author no commit
  at all, and three of them are exactly what AC-2 requires to stay open;
* it MISSES `revert`, `cherry-pick`, `am`, `pull`, `commit-tree`, `fast-import`, `filter-branch`,
  `subtree`, `stash`, `notes`, `replay` — measured below to author commits.

So the answer to the item's first question is a measured **no**: the running git does not name the
set. The form is therefore a **tripwired enumeration** — but not a bare one, because one half IS
derived from the running git: `git --list-cmds=main` decides whether a resolved verb is a git
command at all (section 5), and `--list-cmds=list-history` is one of the two ends of the tripwire
(section 7).

## 2. The property the gate asks — and why it is not SR-0009's parenthesis word for word

SR-0009 clause 3 states the subject as "a new commit object that HEAD or a ref under refs/heads
comes to point at". Measured, that reading leaves a hole that runs in **one tool call**:

```
git update-ref refs/heads/main $(git commit-tree -m x HEAD^{tree})
```

measured: 1 commit object authored, `HEAD` and `refs/heads/main` point at it afterwards. The same
with `git stash create` in place of `commit-tree` (2 objects authored, ref moved). Neither
`update-ref` nor `commit-tree` is a recorder by the parenthesis alone; together they are.

Closing that at the MOVER end would mean refusing `update-ref`, `branch -f`, `reset --hard`,
`checkout -B` — and AC-2 keeps `branch`/`checkout`/`switch` open, so the mover end is not
available. The gate therefore refuses at the **author** end:

> **AUTHORS A COMMIT** — a git subcommand that can author a NEW commit object out of the state at
> hand, whatever ref that object lands under (or none).

That is also exactly the set for which "the digest cannot exist before the command runs" holds,
which is the reason clause 3 gives for refusing rather than gating. A ref move stays open: the
object it names already exists and could have been certified when it was authored.

The refined SR-0009 (post-verifier F1) states this property directly and names the **plumbing**:
the set "covers the plumbing that writes a commit object (commit-tree, hash-object -t commit,
fast-import and import kin) as much as the porcelain". The verifier's F1 chain is the reason:

```
git update-ref refs/heads/main $(printf 'tree %s\n...\n' $(git rev-parse HEAD^{tree}) \
                                 | git hash-object -t commit -w --stdin)
```

measured rc 0 at the pre-fix gate, no verdict in the tree, `refs/heads/main` moved onto a freshly
authored commit object. `git hash-object -t commit -w --stdin` writes a commit object out of an
existing tree exactly as `commit-tree` does; it is in the refusal set now (section 3.2), and the
verb is the subject — `hash-object` is refused whole, not only with `-t commit`, because the type
can be spelled where the gate cannot see it (over-refusal named in section 8).

What that reading does NOT reach is named rather than implied: a commit object authored
**elsewhere** (`git fetch`, `git clone`, and the object-installers `git unpack-objects` /
`git index-pack` / `git bundle`) and then pointed at by an open ref mover. AC-2 keeps `fetch` open;
section 8.1 carries the measured chain and why the one-call *fabricate-and-install* route stays
closed even though the *install-a-real-commit* route does not.

## 3. Measured classification (real git, fresh repo per row, outside the repo)

"authored" counts commit OBJECTS that did not exist before the command
(`git cat-file --batch-all-objects`); "branch ref at a new one" asks whether `HEAD` or a
`refs/heads/*` came to point at one of them.

### 3.1 Authors, and makes it branch history in the same step → REFUSED

| line | rc | authored | branch ref at a new one |
|---|---|---|---|
| `git merge --no-ff --no-edit other` | 0 | 1 | yes |
| `git merge --no-edit other` (non-ff) | 0 | 1 | yes |
| `git merge -m "--no-commit" other` | 0 | 1 | yes |
| `git revert --no-edit HEAD` | 0 | 1 | yes |
| `git cherry-pick other` | 0 | 1 | yes |
| `git rebase other` | 0 | 1 | yes |
| `git rebase --no-commit other` | 0 | 1 | yes |
| `git am patch.mbox` | 0 | 1 | yes |
| `git am --no-commit patch.mbox` | 0 | 1 | yes |
| `git pull --no-rebase … origin main` | 0 | 1 | yes |
| `git commit -qm next` | 0 | 1 | yes |
| `git commit --amend --no-edit` | 0 | 1 | yes |
| `git filter-branch -f --msg-filter … HEAD~1..HEAD` | 0 | 1 | yes |
| `git subtree add --prefix=sub . other` | 0 | 1 | yes |
| `git fast-import` (stream on stdin, bytes) | 0 | 1 | yes |

### 3.2 Authors a commit object that lands OUTSIDE branch history → REFUSED (author end)

| line | rc | authored | where it landed |
|---|---|---|---|
| `git stash` | 0 | 2 | `refs/stash` |
| `git stash create` | 0 | 2 | nowhere (printed) |
| `git commit-tree -m x HEAD^{tree}` | 0 | 1 | nowhere (printed) |
| `git hash-object -t commit -w --stdin` (fabricated commit on stdin, bytes) | 0 | 1 | nowhere (printed) |
| `git notes add -m x` | 0 | 1 | `refs/notes/commits` |
| `git replay --onto main main..other` | 0 | 1 | nowhere (prints ref updates) |

`hash-object` (F1) authors a commit object from a tree that already exists plus a fabricated
header on stdin — the one-call chain in section 2 installs it onto `refs/heads/main`. Measured
with a **byte** stdin: the text form is rc 128 (`bad sha1`, this host's CRLF in the tree line),
the byte form authors. Refused at the author end; the over-refusal of `git hash-object -w <blob>`
(a blob, not a commit) is in section 8.

DEC-0042 asks for stash explicitly: **stash authors** (2 objects, measured) and its object is one
`git update-ref refs/heads/main $(git stash create)` away from branch history — measured, ref
moved. So it is refused at the author end like the rest of this table. The cost is over-refusal of
`git stash list`/`show`/`pop`, named in section 8.

### 3.3 Authors nothing (authoring measurement — refusal is a SEPARATE axis)

The `authored` column is the measured authoring, NOT the gate's decision. A `merge` line is
exempt from refusal ONLY where `--no-commit` is the first argument with no `--commit` beside it;
every other `merge` spelling authors nothing yet is **still refused** (`merge` is in the author
set — over-refusal by subcommand, named in §8.2). The `refused?` note marks which rows the gate
lets through and which it refuses despite the zero.

| line | rc | authored | refused? / note |
|---|---|---|---|
| `git merge --ff-only other` | 0 | 0 | **refused** (no `--no-commit` first) — over-refusal, §8.2; ref would move to an EXISTING commit — DEC-0042's fast-forward question |
| `git merge --no-commit --no-ff other` | 0 | 0 | allowed — "stopped before committing as requested" |
| `git merge --no-commit other` (ff-able) | 0 | 0 | allowed — fast-forwards to an existing commit |
| `git merge --squash other` | 0 | 0 | **refused** (no `--no-commit` first) — over-refusal, §8.2 |
| `git merge --commit --no-commit --no-ff other` | 0 | 0 | **refused** (`--commit` present / suppressor not first) — over-refusal, §8.2 |
| `git merge --no-commit -m x other` | 0 | 0 | allowed (suppressor first) |
| `git revert --no-commit HEAD` | 0 | 0 | |
| `git cherry-pick --no-commit other` | 0 | 0 | |
| `git pull --no-commit --no-rebase …` | 0 | 0 | authors nothing, but is **refused anyway** — see §4 (pull is not a produce-first form) |
| `git apply patch.mbox` | 0 | 0 | the produce-first route for `am` |
| `git fetch origin` | 0 | 0 | AC-2 |
| `git add -A`, `git status`, `git diff`, `git log` | 0 | 0 | AC-2 |
| `git branch newbranch`, `git branch -f side other` | 0 | 0 | AC-2 |
| `git checkout -b fresh`, `git switch -c fresh2` | 0 | 0 | AC-2 |
| `git checkout -B main other` | 0 | 0 | ref moved to an existing commit |
| `git reset --hard HEAD~1` | 0 | 0 | ref moved to an existing commit |
| `git update-ref refs/heads/side other` | 0 | 0 | ref moved to an existing commit |
| `git tag -a v1 -m x` | 0 | 0 | a TAG object under `refs/tags`, not a commit |
| `git replace HEAD HEAD~1` | 0 | 0 | `refs/replace/*`, no new object of any kind |
| `git worktree add ../wt -b wtb` | 0 | 0 | |
| `git restore .`, `git checkout other -- c.txt`, `git clean -fd`, `git mv`, `git rm` | 0 | 0 | move the tree, author nothing |
| `git describe`, `format-patch`, `bundle create`, `archive`, `gc`, `range-diff`, `shortlog`, `show`, `submodule status`, `bisect start` | 0 | 0 | |

### 3.4 In the set without a demonstration, and why

`quiltimport`, `svn`, `p4`, `citool`, `gui`. Each is a name `git --list-cmds=main` knows on this
host and each authors commits by construction (a quilt series applied and committed; a foreign-SCM
bridge; a commit GUI). This suite cannot drive them: `citool`/`gui` need a display, `svn`/`p4`
need a foreign server, and `quiltimport` did not apply a series in the harness (rc 0, nothing
authored, twice). They are IN the refusal set and the tripwire pins this bucket exactly, so a new
entry cannot join it silently (section 7, T2).

### 3.5 F2 — the produce-first option a subcommand can talk its way back out of

The refined SR-0009 (post-verifier F2) exempts a produce-first form ONLY where the option
suppresses recording for **every spelling and every configuration** of the same invocation. `pull`
fails that bar, measured against a diverged shared-base remote:

| line | rc | authored | branch ref at a new one |
|---|---|---|---|
| `git pull --no-commit --no-rebase origin main` | 0 | 0 | no (merge mode) |
| `git pull --no-commit --rebase origin main` | 0 | 1 | **yes** |
| `git pull --no-commit -r origin main` | 0 | 1 | **yes** |
| `git pull --no-commit --rebase=true origin main` | 0 | 1 | **yes** |
| `git -c pull.rebase=true pull --no-commit origin main` | 0 | 1 | **yes** |

`--no-commit` suppresses pull's MERGE mode only; under any rebase spelling or `pull.rebase=true` it
records. So `pull` is **not** in the exempt set, and its produce-first remedy routes through a
subcommand that suppresses unconditionally: `git fetch`, then `git merge --no-commit`. The cost is
over-refusal of `git pull --no-commit --no-rebase` (authors nothing) — named in section 8.

## 4. The produce-first remedy has to be runnable, so its shape is measured too

Clause 3's remedy is "produce the state first WITHOUT recording (`--no-commit` and kin), obtain the
verdict, record through `git commit`". A refusal whose remedy is itself refused is the failure mode
this repo's own `UNRESOLVED_VERB_NOTE` was written for. So the gate lets ONE shape through, and
every part of that shape is a measurement:

* only for the verbs where the option was MEASURED to suppress authoring for EVERY spelling and
  configuration: `merge`, `revert`, `cherry-pick`. **`rebase --no-commit` and `am --no-commit`
  still record**, and **`pull --no-commit` records under any rebase spelling** (§3.5) — so none of
  those three is exempt, and each is a tripwire cell, not a comment.
* the option must be the FIRST argument token of that invocation. Reason, measured:
  `git merge -m "--no-commit" other` really records (1 object, ref moved) while the token
  `--no-commit` stands in the line. A token-anywhere rule would have allowed it. Nothing can
  swallow the token immediately after the subcommand, because the subcommand takes no value.
* no `--commit` anywhere in the same invocation. Reason, measured:
  `git merge --no-commit --commit --no-ff other` records (1 object, ref moved), and so do
  `git revert --no-commit --commit HEAD` and `git cherry-pick --no-commit --commit other`, while
  `git merge --commit --no-commit --no-ff other` does not. Git spells a negation with a `no-`
  prefix and the last spelling wins; the counterpart is derived from the option by stripping that
  prefix, not listed.

Over-refusal this shape costs: `git merge --no-ff --no-commit other` (suppressor not first) is
refused. The refusal prints the accepted shape.

## 5. The alias hole the verb-only reading leaves — measured, and closed by derivation

The kits' reader hands back the SUBCOMMAND. Measured through `_compat.git_invocations`:

```
git -c alias.z='!git merge --no-ff other' z   ->  [('z', resolved=True, [])]
git z                                          ->  [('z', resolved=True, [])]
```

The inner `git merge` is invisible — one word of quoting and a verb-only classification is past.
`git config alias.z '!git merge --no-ff other'` (an allowed line: `config` authors nothing) plus
`git z` is the same chain in two calls. Both run inside one session.

Closed by asking the running git: a resolved verb that `git --list-cmds=main` does not name is not
a git command — it is an alias, an external `git-foo`, or a typo — and the gate cannot see what it
runs, so it is refused with "spell the git command out". This is the DERIVED half SR-0009 asks
for, and it follows a git that gains or loses commands on the day it is installed.

Cost, measured on this host: `git --list-cmds=main` costs **0.042 s** (five further calls 0.248 s
total, i.e. ~0.05 s each). It is asked at most ONCE per gate process, and only for a line that
invokes git with a resolved verb outside the author set. Against the registration's 120 s (budget
~96 s after `_harness.Deadline`'s reserve) that is 0.04 % of the budget. There is no cache to
invalidate: a gate process answers one call and exits, so the memo lives exactly as long as the
question does.

What it costs when git does not answer: `_harness._git` raises and `guarded()` turns that into a
refusal, so on a host without git every git-naming line with an unknown verb is refused. Named,
not hidden.

## 6. Interaction with what already runs

* **`_moves_the_tree_first` (H22, the kits' classification) needs no widening.** Measured through
  `gate_write_scope._stage_is_read_only`: `git merge --no-commit --no-ff other` is
  `read_only=False`, `git add -A` and `git status` are `read_only=True`. So the one line the new
  exemption makes reachable in front of a commit — `git merge --no-commit --no-ff other &&
  git commit -m wip` — is already rc 2 today for the tree-move reason, measured through the real
  gate process with a valid verdict in the tree. It is pinned as a test, and it is a PIN, not a
  red-without-fix.
* **The kits' `_READ_ONLY_GIT` is not the set to derive from.** Its complement holds `branch`,
  `checkout`, `switch`, `fetch`, `reset`, `push` — AC-2's open path. It answers "does this stage
  modify anything", which is a different question.
* **Command substitution (TSK-0019 lineage)**: the applicability question is asked of the RAW
  command through `compat.git_invocations`, exactly as `runs("commit")` is today, so an invocation
  a substitution introduces is one of the invocations. Measured: the one-call chain in section 2
  is seen as two invocations and refused for `commit-tree`.
* **Prose removal (H34/H38)**: applicability is decided on the raw command, so the message-argument
  and heredoc spans that `_prose_removed` deletes do not hide a git verb from THIS decision — they
  still hide one from `_moves_the_tree_first`, which is where H34/H38 already live.
* **What the exemption's tokens are**: the kits' RESOLVED words, not the raw text. Measured through
  `_compat.git_invocations`: `git merge "--no-commit" …`, `'--no-commit'` and `--no-com"mit"` all
  arrive as the token `--no-commit` (the same resolution that makes `git pu''sh` a push), while
  `git merge $FLAG …` arrives as `$flag`. So every spelling the shell turns into the option is the
  produce-first form, and one the text does not fix is not — measured rc 0 and rc 2 respectively
  through the real gate. What a resolution this reader gets wrong costs is bounded by git: a word
  the shell does not turn into `--no-commit` reaches git as an unknown option and git exits
  without recording. (An earlier draft of this note claimed the opposite — that a quoted spelling
  is refused — and the measurement is what corrected it.)
* **Deadline (H35/H36)**: the new work per call is one `git --list-cmds=main` (0.042 s) plus, for
  each author invocation that carries the suppressor, one scan of its segment
  (`Invocation.arguments`). The second is the O(k·n) shape `_compat.GIT_READ_LIMIT` documents for
  `gate_push_token`; the gate short-circuits on the FIRST non-exempt author, so the pathological
  line has to be built entirely out of exempt invocations to reach it, and what answers there is
  `_the_budget_is_spent` — a refusal, not an allow. Measured in the suite.

## 7. The tripwire, both ends

In `test_gates.py`, reading the sets OUT of the gate module (imported, not string-searched):

* **T1 (a dead entry says so)** — every author entry with a scenario is driven against the
  installed git and must author ≥ 1 commit object.
* **T2 (an undemonstrated entry cannot join silently)** — the entries without a scenario are
  exactly section 3.4's five, each with a stated reason, and each a name the running git knows.
* **T3** — every author entry is a name in `git --list-cmds=main`.
* **T4 (a missing recorder says so, derived)** — every name in `git --list-cmds=list-history` is
  classified, in the author set or in the measured non-author table.
* **T5 (a missing recorder says so, measured)** — every non-author entry authors nothing in a
  SUCCESSFUL invocation, so a command that starts authoring turns red.
* **T6 (the exemption's both ends)** — `test_the_produce_first_option_is_exempted_exactly_where_it
  _works` drives each exempt verb's `--no-commit` form and asserts `(not authored) == (verb in
  HONOURS_THE_SUPPRESSOR)`, so the suppressor authors nothing for `merge`/`revert`/`cherry-pick`
  and records for `rebase`/`am`/`pull`.
* **T7 (F2, every rebase spelling)** — `test_no_spelling_of_a_rebase_pull_survives_the_suppressor`
  drives `pull --no-commit` with `--rebase`, `-r`, `--rebase=true` and `-c pull.rebase=true`
  against a diverged shared-base remote; each must author, and `pull` must stay OUT of
  `HONOURS_THE_SUPPRESSOR`. The old pull scenario hard-wired `--no-rebase`, so it could not fail on
  this case — a test that cannot fail, replaced.
* **T8 (F1, the plumbing author)** — `hash-object` is in `RECORDS_HISTORY` and driven with a byte
  stdin; the tripwire measures it authors a commit object on the installed git, and two gate-level
  edges (`git hash-object -t commit -w --stdin` and the verifier's exact `update-ref $(printf … |
  git hash-object …)` chain) must be rc 2 with a verdict in the tree.

What T4 does not reach: a NEW git command that authors commits and stands outside
`--list-cmds=list-history`. Named as a residue.

## 8. Residues this build does not close (for the lead's wishlist pass)

1. **Author-elsewhere / imported object, then move a ref here.** This is the residue that carries
   the plumbing installers, and its chain is measured (`scratchpad/measure_plumbing.py`):

   | line | authors here? | installs a commit object into this store? |
   |---|---|---|
   | `git unpack-objects < pack` then `git update-ref refs/heads/main <sha>` | no (unpacks a donor pack) | **yes** — measured, ref moved |
   | `git index-pack --stdin < pack` | no | **yes** — object indexed into the store |
   | `git clone <donor> sub` | no (new subdir repo) | no (into a *different* store) |
   | `git bundle create b main` | no | no (writes a file) |

   These INSTALL a commit object rather than author one. Why the one-call *fabricate-and-install*
   route stays closed: the pack or bundle they read has to already contain the fabricated commit,
   and building it needs an authoring verb — `git pack-objects` can only pack objects that exist,
   and `git -C <anydir> commit` / `commit-tree` / `hash-object -t commit` are all refused by this
   gate whatever `-C` points at. So no NEW fabricated commit reaches the store through them in one
   tool call. What DOES reach it is a commit that already exists in some real repository — the
   `fetch` class AC-2 keeps open (`git fetch`, `git update-ref`, `branch -f`, `reset --hard`,
   `checkout -B`, all measured to author nothing). Folding `unpack-objects`/`index-pack` into the
   refusal set is available and fail-closed; it is left OUT here because it over-refuses legitimate
   pack receipt and does not close a one-call fabricate hole — the lead's call for the wishlist.
2. **Over-refusal, by subcommand rather than by flag**: `git merge --ff-only`, `git merge --abort`,
   `git rebase --abort`, `git cherry-pick --abort`, `git stash list|show|pop`, `git notes list`,
   **`git pull --no-commit --no-rebase`** (authors nothing in merge mode — §3.5 — but pull has no
   produce-first form, so it is refused), and **`git hash-object -w <blob>`** (writes a blob, not a
   commit — but the verb is the subject, not its `-t` type, because the type can be spelled where
   the gate cannot see it). All author nothing and all are refused. Reading a flag to ALLOW is the
   fail-open direction; the one exemption that exists is the produce-first shape, and it is
   measured. Ways through: `git fetch` + `git merge --no-commit` for the pull, `git hash-object`
   without `-w` (prints, writes nothing) or the shell outside Claude Code for the blob,
   `git merge --no-commit --ff-only …` for the fast-forward, `git reset --hard` for an abort.
3. **Over-refusal of the kits' reader over-trigger class**: `ls git*`, `echo git$VERSION`,
   `grep -rn "git$" .`, `cat git{a,b}.txt`, `echo "use git^ …"` all read as an invocation with an
   unresolved verb and are now refused UNCONDITIONALLY, where before they were refused only while
   no verdict covered the tree. Measured through the reader. The remedy is compliable (spell it
   differently), and the fail-open alternative is a measured hole: `git ${VERB} --no-ff other` was
   rc 0 before, with a valid verdict in the tree.
   The same class one step further: UNQUOTED prose that names an author is now a refusal too —
   `echo run git merge later` is rc 2 through the real gate, while `echo "run git merge later"` is
   rc 0 (one quoted word, no invocation). That is the kits' rule that a command is a command
   whatever stands in front of it (`sudo git push`), and before this round the same shape was
   already refused for `commit`.
4. **`git submodule foreach '<git command>'` and `git bisect run <script>`** hand a command to an
   interpreter this gate does not read — the H11 class, not new here.
5. **A commit made from a shell outside the provider** — unchanged, already in the gate's
   docstring.
